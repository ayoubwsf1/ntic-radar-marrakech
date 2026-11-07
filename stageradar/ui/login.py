import imaplib

import streamlit as st

from ..gmail_scan import connect
from .helpers import wide


def render_login_page() -> None:
    st.markdown(
        """
<div style="max-width:440px;margin:9vh auto 1.2rem auto;text-align:center;">
  <h1 style="margin:.3rem 0 .2rem 0;font-size:1.8rem;">Ntic Radar <span style="opacity:.6;">Marrakech</span></h1>
  <p style="opacity:.65;font-size:.95rem;">Plateforme de recherche, d'analyse et de suivi des stages à Marrakech. Connectez Gmail pour le suivi automatique, ou continuez en mode démo.</p>
</div>
""",
        unsafe_allow_html=True,
    )

    _, mid, _ = st.columns([1, 1.3, 1])
    with mid:
        with st.container(border=True):
            addr = st.text_input("Adresse Gmail", key="login_addr", placeholder="prenom.nom@gmail.com")
            pwd = st.text_input(
                "Mot de passe d'application", type="password", key="login_pwd", placeholder="xxxx xxxx xxxx xxxx"
            )
            err_slot = st.empty()
            clicked = st.button("Se connecter", type="primary", **wide())
            if st.button("Continuer sans Gmail (mode démo)", **wide()):
                st.session_state["demo"] = True
                st.rerun()

            with st.expander("Obtenir un mot de passe d'application"):
                st.markdown(
                    """
Gmail refuse le mot de passe normal avec IMAP. Il faut :
1. Activer la **validation en 2 étapes** sur votre compte Google.
2. Aller sur `myaccount.google.com/apppasswords`, créer un mot de passe « Ntic Radar ».
3. Copier les 16 caractères ici.
4. Vérifier que **IMAP est activé** : Gmail → Paramètres → Transfert et POP/IMAP.

Le mot de passe reste en mémoire le temps de la session. Il n'est **jamais écrit sur le disque**.
"""
                )

            if clicked:
                _tenter_connexion(addr, pwd, err_slot)


def _tenter_connexion(addr: str, pwd: str, err_slot) -> None:
    if not addr.strip() or not pwd.strip():
        err_slot.error("Saisissez l'adresse Gmail et le mot de passe d'application.")
        return

    with st.spinner("Connexion à Gmail…"):
        try:
            M = connect(addr.strip(), pwd)
            M.logout()
        except imaplib.IMAP4.error as e:
            err_slot.error(
                "Connexion refusée par Gmail. Vérifiez l'adresse, le **mot de passe d'application** "
                f"(pas le mot de passe normal) et que IMAP est activé.\n\nDétail : {str(e)[:120]}"
            )
            return
        except Exception as e:
            err_slot.error(f"Erreur de connexion : {str(e)[:160]}")
            return

    st.session_state["gmail_user"] = addr.strip()
    st.session_state["gmail_pwd"] = pwd
    st.rerun()
