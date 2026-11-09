"""Onglet Agences : la liste des agences sous forme de cartes, avec tri et pagination."""
import pandas as pd  # pour les listes de données
import streamlit as st  # pour afficher les cartes

from ..config import STATUTS  # pour l'ordre des statuts
from .helpers import esc, pill, wide  # pour protéger le texte, l'étiquette de statut, et la largeur

_ORDRES = {"Nom (A→Z)": "nom", "Ville": "ville", "Statut": "statut", "Type": "type"}  # les choix de tri


def _trier(df: pd.DataFrame, order: str) -> pd.DataFrame:
    # Trie la liste des agences selon le choix de l'utilisateur
    key_sort = _ORDRES[order]  # la colonne sur laquelle on trie
    if key_sort == "statut":  # si on trie par statut, on utilise l'ordre des statuts
        return df.assign(_r=df["statut"].map(STATUTS.index)).sort_values(["_r", "nom"]).drop(columns="_r")
    return df.sort_values([key_sort, "nom"])  # sinon on trie par la colonne puis par le nom


def _carte_agence(r: pd.Series) -> None:
    # Affiche une carte pour une agence
    with st.container(border=True):  # une boîte avec une bordure
        proof = f'<div class="proof">{esc(r["preuve"])}</div>' if r["preuve"] else ""  # la preuve, si elle existe
        source = f'<span class="chip chip-source">📍 {esc(r["source"])}</span>' if r.get("source") else ""  # la source, si elle existe
        st.markdown(  # on affiche la carte en HTML
            f"""<div class="ag-head"><div><div class="ag-name">{esc(r['nom'])}</div>
<div class="ag-meta">{esc(r['ville'])} &nbsp;·&nbsp; {esc(str(r['taille']) or 'n.c.')}</div></div>{pill(r['statut'])}</div>
<span class="chip">{esc(r['type'])}</span>{source}
<div class="ag-serv">{esc(r['services'])}</div>{proof}""",
            unsafe_allow_html=True,
        )
        if r["site"]:  # si l'agence a un site web
            st.link_button("Site web", r["site"], **wide())  # bouton pour ouvrir le site


def render_tab_agences(df: pd.DataFrame) -> None:
    # Affiche la liste des agences avec le tri et la pagination
    if df.empty:  # si la liste est vide
        st.info("Aucune agence ne correspond aux filtres.")  # message d'information
        return  # on arrête

    c1, c2, c3 = st.columns([2, 1, 1])  # trois colonnes en haut
    c1.markdown(f"**{len(df)}** agence(s) affichée(s)")  # on affiche le nombre d'agences
    order = c2.selectbox("Trier par", list(_ORDRES), label_visibility="collapsed")  # liste pour choisir le tri
    per_page = c3.selectbox("Par page", [12, 24, 48], label_visibility="collapsed", format_func=lambda n: f"{n} par page")  # nombre par page

    df = _trier(df, order)  # on trie la liste
    pages = max(1, -(-len(df) // per_page))  # on compte le nombre de pages
    page = st.number_input("Page", 1, pages, 1, key="page") if pages > 1 else 1  # champ pour choisir la page
    chunk = df.iloc[(page - 1) * per_page: page * per_page]  # les agences de cette page seulement

    grid = st.columns(2)  # deux colonnes pour les cartes
    for i, (_, r) in enumerate(chunk.iterrows()):  # pour chaque agence de la page
        with grid[i % 2]:  # on alterne entre la colonne 1 et la colonne 2
            _carte_agence(r)  # on affiche la carte de l'agence
