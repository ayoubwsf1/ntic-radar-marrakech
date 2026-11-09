"""Panneau Gmail dans la barre latérale. Il permet de scanner les mails."""
import imaplib  # pour lire la boîte Gmail
from datetime import datetime  # pour la date du scan

import pandas as pd  # pour les listes de données
import streamlit as st  # pour afficher des boutons et messages

from ..ai.email_ai import classifier_hybride  # le classifieur qui utilise l'IA
from ..ai.llm import get_client  # pour avoir le client IA
from ..classification import classify  # pour classer les mails avec des règles simples
from ..events import apply_events  # pour mettre à jour les statuts
from ..gmail_scan import scan_mailbox  # pour scanner la boîte Gmail
from .helpers import wide  

_JOURS_ANALYSES = 90  # on analyse les mails des 90 derniers jours


def render_gmail_panel(df_all: pd.DataFrame) -> None:
    # Affiche le panneau Gmail avec le bouton pour scanner les mails
    st.markdown("### Gmail")  # le titre
    if st.session_state.get("demo") and "gmail_user" not in st.session_state:
        # En mode démo, on ne peut pas scanner les mails
        st.info("Mode démo : Gmail n'est pas connecté, le scan automatique est désactivé.")
        if st.button("Connecter Gmail", **wide()):
            st.session_state.pop("demo", None)  # on quitte le mode démo
            st.rerun()  # on recharge la page
        return  # on ne continue pas

    addr = st.session_state.get("gmail_user", "")  # l'adresse Gmail de l'utilisateur

    c1, c2 = st.columns([2.4, 1])  # deux colonnes à côté
    c1.success(f"Connecté : **{addr}**")  # on affiche que c'est connecté
    if c2.button("Déconnexion", **wide()):
        st.session_state.pop("gmail_user", None)  # on efface l'adresse
        st.session_state.pop("gmail_pwd", None)  # on efface le mot de passe
        st.rerun()  # on recharge la page

    llm = get_client()  # on prend le client IA
    if llm.available:  # seulement si l'IA est disponible
        st.toggle("Analyse IA des e-mails ambigus", key="ia_emails",
                  help="Si les règles ne détectent rien, un court extrait (1500 caractères) est envoyé à l'API du modèle. Désactivé par défaut.")
    scan_clicked = st.button("Vérifier mes mails", type="primary", **wide())  # bouton pour scanner
    scan_slot = st.empty()  # un espace vide pour les messages

    if scan_clicked:  # si l'utilisateur a cliqué sur le bouton
        _lancer_scan(addr, st.session_state.get("gmail_pwd", ""), _JOURS_ANALYSES, df_all, scan_slot)  # on lance le scan


def _lancer_scan(addr: str, pwd: str, days: int, df_all: pd.DataFrame, scan_slot) -> None:
    # Lance le scan des mails et met à jour les statuts
    if not addr.strip() or not pwd.strip():  # si l'adresse ou le mot de passe est vide
        scan_slot.error("Session Gmail expirée, reconnectez-vous.")  # message d'erreur
        return  # on arrête

    bar = scan_slot.progress(0.0, text="Connexion…")  # barre de progression au départ
    try:
        llm = get_client()  # on prend le client IA
        # on choisit le classifieur : règles simples ou IA si l'utilisateur l'a activé
        classifier = (lambda sujet, corps: classifier_hybride(sujet, corps, llm)) if st.session_state.get("ia_emails") else classify
        res = scan_mailbox(  # on scanne la boîte Gmail
            addr, pwd, df_all, days=days, classifier=classifier,
            progress=lambda f, t: bar.progress(min(max(f, 0.0), 1.0), text=t),  # on met à jour la barre
        )
        changes = apply_events(res.events)  # on applique les changements de statut
        st.session_state["last_scan"] = {  # on garde le résultat pour l'onglet scan
            "when": datetime.now().strftime("%d/%m/%Y %H:%M"), "scanned": res.scanned, "folder": res.folder,
            "events": res.events, "changes": len(changes), "days": days,
        }
        for k in [k for k in st.session_state if str(k).startswith("st_")]:  # on nettoie les clés temporaires
            del st.session_state[k]  # on supprime la clé
        bar.empty()  # on cache la barre de progression
        scan_slot.success(f"{res.scanned} mails analysés · {len(changes)} statut(s) mis à jour.")  # message de succès
    except imaplib.IMAP4.error as e:  # si Gmail refuse la connexion
        bar.empty()  # on cache la barre
        scan_slot.error(
            "Connexion refusée par Gmail. Vérifiez que le **mot de passe d'application** est "
            f"toujours valide et que IMAP est activé.\n\nDétail : {str(e)[:120]}"
        )
    except Exception as e:  # si un autre problème arrive
        bar.empty()  # on cache la barre
        scan_slot.error(f"Erreur pendant l'analyse : {str(e)[:160]}")  # message d'erreur
