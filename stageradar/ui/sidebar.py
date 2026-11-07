import pandas as pd
import streamlit as st

from .. import database
from ..config import CITY_COORDS, TYPES, VILLE_CIBLE
from ..filters import Filtres
from .gmail_panel import render_gmail_panel
from .helpers import wide


def render_sidebar(df_all: pd.DataFrame, statuts_possibles: list) -> Filtres:
    with st.sidebar:
        render_gmail_panel(df_all)
        st.divider()

        st.markdown("### Filtres")
        q = st.text_input("Recherche", placeholder="nom, ville, service…")
        villes = sorted(df_all["ville"].dropna().unique()) if not df_all.empty else []
        f_ville = st.multiselect("Ville", villes, default=[VILLE_CIBLE] if VILLE_CIBLE in villes else [],
                                 help=f"Par défaut : {VILLE_CIBLE}. Videz la sélection pour voir toutes les villes.")
        f_type = st.multiselect("Type d'agence", TYPES)
        f_statut = st.multiselect("Statut", statuts_possibles)

        st.divider()
        _render_ajout_agence()
        _render_reimport()

    return Filtres(q=q, ville=f_ville, type_=f_type, statut=f_statut)


def _render_ajout_agence() -> None:
    with st.expander("Ajouter une agence"):
        n_nom = st.text_input("Nom", key="n_nom")
        n_type = st.selectbox("Type", TYPES, key="n_type")
        n_ville = st.selectbox("Ville", list(CITY_COORDS), key="n_ville")
        n_site = st.text_input("Site web", key="n_site", placeholder="https://…")
        n_serv = st.text_input("Services", key="n_serv")
        if st.button("Ajouter", key="n_add", **wide()):
            if not n_nom.strip() or not n_site.strip():
                st.warning("Nom et site web obligatoires.")
            elif database.add_agence(n_nom, n_type, n_ville, n_site, n_serv):
                st.success("Agence ajoutée")
            else:
                st.info("Cette agence existe déjà.")


def _render_reimport() -> None:
    with st.expander("Réimporter l'Excel"):
        st.caption("Ajoute les nouvelles lignes de agences_maroc.xlsx (les statuts existants ne sont pas modifiés).")
        if st.button("Réimporter", key="reimport", **wide()):
            st.success(f"{database.sync_from_excel()} nouvelle(s) agence(s).")
