"""Barre latérale : le panneau Gmail, les filtres, et les boutons pour ajouter une agence."""
import pandas as pd  # pour les listes de données
import streamlit as st  # pour afficher la barre latérale

from .. import database  # pour lire et écrire la base de données
from ..config import CITY_COORDS, TYPES, VILLE_CIBLE  # pour les villes, les types et la ville cible
from ..filters import Filtres  # pour garder les valeurs des filtres
from .gmail_panel import render_gmail_panel  # pour afficher le panneau Gmail
from .helpers import wide  # pour un bouton qui prend toute la largeur


def render_sidebar(df_all: pd.DataFrame, statuts_possibles: list) -> Filtres:
    # Affiche la barre latérale et renvoie les filtres choisis
    with st.sidebar:  # tout ce qui est dans ce bloc est dans la barre latérale
        render_gmail_panel(df_all)  # le panneau Gmail en haut
        st.divider()  # une ligne de séparation

        st.markdown("### Filtres")  # le titre des filtres
        q = st.text_input("Recherche", placeholder="nom, ville, service…")  # champ pour rechercher par un mot
        villes = sorted(df_all["ville"].dropna().unique()) if not df_all.empty else []  # la liste des villes
        f_ville = st.multiselect("Ville", villes, default=[VILLE_CIBLE] if VILLE_CIBLE in villes else [],  # liste pour choisir les villes
                                 help=f"Par défaut : {VILLE_CIBLE}. Videz la sélection pour voir toutes les villes.")
        f_type = st.multiselect("Type d'agence", TYPES)  # liste pour choisir les types d'agence
        f_statut = st.multiselect("Statut", statuts_possibles)  # liste pour choisir les statuts

        st.divider()  # une ligne de séparation
        _render_ajout_agence()  # le bloc pour ajouter une agence
        _render_reimport()  # le bloc pour réimporter le fichier Excel

    return Filtres(q=q, ville=f_ville, type_=f_type, statut=f_statut)  # on renvoie les filtres choisis


def _render_ajout_agence() -> None:
    # Affiche le formulaire pour ajouter une nouvelle agence
    with st.expander("Ajouter une agence"):  # un bloc fermé que l'utilisateur peut ouvrir
        n_nom = st.text_input("Nom", key="n_nom")  # le nom de l'agence
        n_type = st.selectbox("Type", TYPES, key="n_type")  # le type, dans une liste
        n_ville = st.selectbox("Ville", list(CITY_COORDS), key="n_ville")  # la ville, dans une liste
        n_site = st.text_input("Site web", key="n_site", placeholder="https://…")  # l'adresse du site web
        n_serv = st.text_input("Services", key="n_serv")  # les services proposés
        if st.button("Ajouter", key="n_add", **wide()):  # bouton pour ajouter
            if not n_nom.strip() or not n_site.strip():  # si le nom ou le site est vide
                st.warning("Nom et site web obligatoires.")  # message d'avertissement
            elif database.add_agence(n_nom, n_type, n_ville, n_site, n_serv):  # on essaie d'ajouter dans la base
                st.success("Agence ajoutée")  # message de succès
            else:  # si l'agence existe déjà
                st.info("Cette agence existe déjà.")  # message d'information


def _render_reimport() -> None:
    # Affiche le bouton pour réimporter le fichier Excel
    with st.expander("Réimporter l'Excel"):  # un bloc fermé
        st.caption("Ajoute les nouvelles lignes de agences_maroc.xlsx (les statuts existants ne sont pas modifiés).")  # petit texte d'aide
        if st.button("Réimporter", key="reimport", **wide()):  # bouton pour réimporter
            st.success(f"{database.sync_from_excel()} nouvelle(s) agence(s).")  # on réimporte et on affiche le nombre
