import pandas as pd
import streamlit as st

from ..config import STATUT_COLORS, STATUTS, VILLE_CIBLE


def render_header(df_all: pd.DataFrame) -> None:
    total = len(df_all)
    nb_villes = df_all["ville"].nunique() if total else 0
    nb_cible = int((df_all["ville"] == VILLE_CIBLE).sum()) if total else 0
    st.markdown(
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
    total = len(df_all)
    counts = df_all["statut"].value_counts().to_dict() if total else {}
    tiles = [("Agences", total, "#6366f1")] + [(s, counts.get(s, 0), STATUT_COLORS[s]) for s in STATUTS]
    cols = st.columns(len(tiles))
    for col, (label, n, color) in zip(cols, tiles):
        col.markdown(
            f'<div class="kpi"><div class="kpi-n" style="color:{color}">{n}</div><div class="kpi-l">{label}</div></div>',
            unsafe_allow_html=True,
        )
