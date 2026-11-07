"""Ntic Radar Marrakech — plateforme de recherche, d'analyse et de suivi des stages.

Lancer :    
"""
import streamlit as st

from stageradar import database
from stageradar.config import STATUTS
from stageradar.filters import appliquer_filtres
from stageradar.ui.header import render_header, render_kpis
from stageradar.ui.login import render_login_page
from stageradar.ui.sidebar import render_sidebar
from stageradar.ui.styles import CSS
from stageradar.ui.tab_agences import render_tab_agences
from stageradar.ui.tab_carte import render_tab_carte
from stageradar.ui.tab_cv import render_tab_cv
from stageradar.ui.tab_dashboard import render_tab_dashboard
from stageradar.ui.tab_scan import render_tab_scan
from stageradar.ui.tab_suivi import render_tab_suivi

st.set_page_config(page_title="Ntic Radar Marrakech", page_icon="🧭", layout="wide", initial_sidebar_state="expanded")


@st.cache_resource
def _boot() -> bool:
    database.init_db()
    database.sync_from_excel()
    return True


def main() -> None:
    _boot()
    st.markdown(CSS, unsafe_allow_html=True)

    if "gmail_user" not in st.session_state and not st.session_state.get("demo"):
        render_login_page()
        return

    df_all = database.load_agences()
    filtres = render_sidebar(df_all, STATUTS)
    df_all = database.load_agences()
    df = appliquer_filtres(df_all, filtres)

    render_header(df_all)
    render_kpis(df_all)
    st.write("")

    tabs = st.tabs(["Tableau de bord", "Agences", "Carte", "Suivi", "Mon CV", "Dernier scan"])
    with tabs[0]:
        render_tab_dashboard(df_all)
    with tabs[1]:
        render_tab_agences(df)
    with tabs[2]:
        render_tab_carte(df)
    with tabs[3]:
        render_tab_suivi(df_all)
    with tabs[4]:
        render_tab_cv()
    with tabs[5]:
        render_tab_scan()


if __name__ == "__main__":
    main()
