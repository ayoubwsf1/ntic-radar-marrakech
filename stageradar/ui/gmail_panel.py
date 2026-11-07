import imaplib
from datetime import datetime

import pandas as pd
import streamlit as st

from ..ai.email_ai import classifier_hybride
from ..ai.llm import get_client
from ..classification import classify
from ..events import apply_events
from ..gmail_scan import scan_mailbox
from .helpers import wide

_JOURS_ANALYSES = 90


def render_gmail_panel(df_all: pd.DataFrame) -> None:
    st.markdown("### Gmail")
    if st.session_state.get("demo") and "gmail_user" not in st.session_state:
        st.info("Mode démo : Gmail n'est pas connecté, le scan automatique est désactivé.")
        if st.button("Connecter Gmail", **wide()):
            st.session_state.pop("demo", None)
            st.rerun()
        return

    addr = st.session_state.get("gmail_user", "")

    c1, c2 = st.columns([2.4, 1])
    c1.success(f"Connecté : **{addr}**")
    if c2.button("Déconnexion", **wide()):
        st.session_state.pop("gmail_user", None)
        st.session_state.pop("gmail_pwd", None)
        st.rerun()

    llm = get_client()
    if llm.available:
        st.toggle("Analyse IA des e-mails ambigus", key="ia_emails",
                  help="Si les règles ne détectent rien, un court extrait (1500 caractères) est envoyé à l'API du modèle. Désactivé par défaut.")
    scan_clicked = st.button("Vérifier mes mails", type="primary", **wide())
    scan_slot = st.empty()

    if scan_clicked:
        _lancer_scan(addr, st.session_state.get("gmail_pwd", ""), _JOURS_ANALYSES, df_all, scan_slot)


def _lancer_scan(addr: str, pwd: str, days: int, df_all: pd.DataFrame, scan_slot) -> None:
    if not addr.strip() or not pwd.strip():
        scan_slot.error("Session Gmail expirée, reconnectez-vous.")
        return

    bar = scan_slot.progress(0.0, text="Connexion…")
    try:
        llm = get_client()
        classifier = (lambda sujet, corps: classifier_hybride(sujet, corps, llm)) if st.session_state.get("ia_emails") else classify
        res = scan_mailbox(
            addr, pwd, df_all, days=days, classifier=classifier,
            progress=lambda f, t: bar.progress(min(max(f, 0.0), 1.0), text=t),
        )
        changes = apply_events(res.events)
        st.session_state["last_scan"] = {
            "when": datetime.now().strftime("%d/%m/%Y %H:%M"), "scanned": res.scanned, "folder": res.folder,
            "events": res.events, "changes": len(changes), "days": days,
        }
        for k in [k for k in st.session_state if str(k).startswith("st_")]:
            del st.session_state[k]
        bar.empty()
        scan_slot.success(f"{res.scanned} mails analysés · {len(changes)} statut(s) mis à jour.")
    except imaplib.IMAP4.error as e:
        bar.empty()
        scan_slot.error(
            "Connexion refusée par Gmail. Vérifiez que le **mot de passe d'application** est "
            f"toujours valide et que IMAP est activé.\n\nDétail : {str(e)[:120]}"
        )
    except Exception as e:
        bar.empty()
        scan_slot.error(f"Erreur pendant l'analyse : {str(e)[:160]}")
