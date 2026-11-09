"""Page de connexion. L'utilisateur se connecte avec Gmail ou en mode démo."""
import imaplib  # pour tester la connexion à Gmail

import streamlit as st  # pour afficher les champs et les boutons

from ..gmail_scan import connect  # pour se connecter à Gmail
from .helpers import wide  # pour un bouton qui prend toute la largeur


def render_login_page() -> None:
    # Affiche le titre et le formulaire de connexion
    st.markdown(
        """
<div style="max-width:440px;margin:9vh auto 1.2rem auto;text-align:center;">
  <h1 style="margin:.3rem 0 .2rem 0;font-size:1.8rem;">Ntic Radar <span style="opacity:.6;">Marrakech</span></h1>
  <p style="opacity:.65;font-size:.95rem;">Plateforme de recherche, d'analyse et de suivi des stages à Marrakech. Connectez Gmail pour le suivi automatique, ou continuez en mode démo.</p>
</div>
""",
        unsafe_allow_html=True,
    )

    _, mid, _ = st.columns([1, 1.3, 1])  # trois colonnes, on utilise celle du milieu
    with mid:  # le bloc du milieu
        with st.container(border=True):  # une boîte avec une bordure
            addr = st.text_input("Adresse Gmail", key="login_addr", placeholder="prenom.nom@gmail.com")  # champ pour l'adresse
            pwd = st.text_input(  # champ pour le mot de passe
                "Mot de passe d'application", type="password", key="login_pwd", placeholder="xxxx xxxx xxxx xxxx"
            )
            err_slot = st.empty()  # un espace vide pour afficher les erreurs
            clicked = st.button("Se connecter", type="primary", **wide())  # bouton pour se connecter
            if st.button("Continuer sans Gmail (mode démo)", **wide()):  # bouton pour le mode démo
                st.session_state["demo"] = True  # on active le mode démo
                st.rerun()  # on recharge la page

            with st.expander("Obtenir un mot de passe d'application"):  # un bloc d'aide fermé
                st.markdown(  # le texte d'aide
                    """
Gmail refuse le mot de passe normal avec IMAP. Il faut :
1. Activer la **validation en 2 étapes** sur votre compte Google.
2. Aller sur `myaccount.google.com/apppasswords`, créer un mot de passe « Ntic Radar ».
3. Copier les 16 caractères ici.
4. Vérifier que **IMAP est activé** : Gmail → Paramètres → Transfert et POP/IMAP.

Le mot de passe reste en mémoire le temps de la session. Il n'est **jamais écrit sur le disque**.
"""
                )

            if clicked:  # si l'utilisateur a cliqué sur se connecter
                _tenter_connexion(addr, pwd, err_slot)  # on essaie la connexion


def _tenter_connexion(addr: str, pwd: str, err_slot) -> None:
    # Essaie de se connecter à Gmail avec l'adresse et le mot de passe
    if not addr.strip() or not pwd.strip():  # si un champ est vide
        err_slot.error("Saisissez l'adresse Gmail et le mot de passe d'application.")  # message d'erreur
        return  # on arrête

    with st.spinner("Connexion à Gmail…"):  # petit signe de chargement
        try:
            M = connect(addr.strip(), pwd)  # on essaie la connexion
            M.logout()  # on se déconnecte tout de suite, c'était juste un test
        except imaplib.IMAP4.error as e:  # si Gmail dit non
            err_slot.error(
                "Connexion refusée par Gmail. Vérifiez l'adresse, le **mot de passe d'application** "
                f"(pas le mot de passe normal) et que IMAP est activé.\n\nDétail : {str(e)[:120]}"
            )
            return  # on arrête
        except Exception as e:  # si un autre problème arrive
            err_slot.error(f"Erreur de connexion : {str(e)[:160]}")  # message d'erreur
            return  # on arrête

    st.session_state["gmail_user"] = addr.strip()  # on garde l'adresse pour la session
    st.session_state["gmail_pwd"] = pwd  # on garde le mot de passe pour la session
    st.rerun()  # on recharge la page, l'utilisateur est connecté
