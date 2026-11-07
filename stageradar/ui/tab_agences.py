import pandas as pd
import streamlit as st

from ..config import STATUTS
from .helpers import esc, pill, wide

_ORDRES = {"Nom (A→Z)": "nom", "Ville": "ville", "Statut": "statut", "Type": "type"}


def _trier(df: pd.DataFrame, order: str) -> pd.DataFrame:
    key_sort = _ORDRES[order]
    if key_sort == "statut":
        return df.assign(_r=df["statut"].map(STATUTS.index)).sort_values(["_r", "nom"]).drop(columns="_r")
    return df.sort_values([key_sort, "nom"])


def _carte_agence(r: pd.Series) -> None:
    with st.container(border=True):
        proof = f'<div class="proof">{esc(r["preuve"])}</div>' if r["preuve"] else ""
        source = f'<span class="chip chip-source">📍 {esc(r["source"])}</span>' if r.get("source") else ""
        st.markdown(
            f"""<div class="ag-head"><div><div class="ag-name">{esc(r['nom'])}</div>
<div class="ag-meta">{esc(r['ville'])} &nbsp;·&nbsp; {esc(str(r['taille']) or 'n.c.')}</div></div>{pill(r['statut'])}</div>
<span class="chip">{esc(r['type'])}</span>{source}
<div class="ag-serv">{esc(r['services'])}</div>{proof}""",
            unsafe_allow_html=True,
        )
        if r["site"]:
            st.link_button("Site web", r["site"], **wide())


def render_tab_agences(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("Aucune agence ne correspond aux filtres.")
        return

    c1, c2, c3 = st.columns([2, 1, 1])
    c1.markdown(f"**{len(df)}** agence(s) affichée(s)")
    order = c2.selectbox("Trier par", list(_ORDRES), label_visibility="collapsed")
    per_page = c3.selectbox("Par page", [12, 24, 48], label_visibility="collapsed", format_func=lambda n: f"{n} par page")

    df = _trier(df, order)
    pages = max(1, -(-len(df) // per_page))
    page = st.number_input("Page", 1, pages, 1, key="page") if pages > 1 else 1
    chunk = df.iloc[(page - 1) * per_page: page * per_page]

    grid = st.columns(2)
    for i, (_, r) in enumerate(chunk.iterrows()):
        with grid[i % 2]:
            _carte_agence(r)
