"""En-tête de la page : le grand titre et les petits chiffres clés."""
import pandas as pd  # pour les listes de données
import streamlit as st  # pour afficher

from ..config import STATUT_COLORS, STATUTS, VILLE_CIBLE  # pour les couleurs, les statuts et la ville cible


def render_header(df_all: pd.DataFrame) -> None:
    # Affiche le grand titre en haut de la page
    total = len(df_all)  # le nombre total d'agences
    nb_villes = df_all["ville"].nunique() if total else 0  # le nombre de villes différentes
    nb_cible = int((df_all["ville"] == VILLE_CIBLE).sum()) if total else 0  # le nombre d'agences à Marrakech
    st.markdown(  # on affiche le bloc HTML en haut
        f"""
<div class="hero">
  <div class="hero-title">Ntic Radar <span>Marrakech</span></div>
  <div class="hero-sub">Recherchez, analysez et suivez les agences qui recrutent à Marrakech,
  avec un agent IA qui crée votre CV.</div>
  <div class="hero-badges"><b>{nb_cible} agences à {VILLE_CIBLE}</b><b>{total} au total · {nb_villes} villes</b><b>Agent CV</b><b>Suivi Gmail</b></div>
</div>""",
        unsafe_allow_html=True,
    )


def render_kpis(df_all: pd.DataFrame) -> None:
    # Affiche les petits chiffres : total et nombre par statut
    total = len(df_all)  # le nombre total d'agences
    counts = df_all["statut"].value_counts().to_dict() if total else {}  # on compte les agences par statut
    tiles = [("Agences", total, "#6366f1")] + [(s, counts.get(s, 0), STATUT_COLORS[s]) for s in STATUTS]  # la liste des cartes à afficher
    cols = st.columns(len(tiles))  # on crée les colonnes
    for col, (label, n, color) in zip(cols, tiles):  # pour chaque carte
        col.markdown(  # on affiche la carte
            f'<div class="kpi"><div class="kpi-n" style="color:{color}">{n}</div><div class="kpi-l">{label}</div></div>',
            unsafe_allow_html=True,
        )
