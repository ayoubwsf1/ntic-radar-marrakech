"""Tableau de bord : analyse exploratoire des agences collectées."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from .. import analytics
from ..config import VILLE_CIBLE


def _bar(serie: pd.Series, titre: str, horizontal: bool = True) -> None:
    st.markdown(f"**{titre}**")
    if serie.empty:
        st.caption("Pas de données.")
        return
    st.bar_chart(serie, horizontal=horizontal, height=280)


def _pie_part(n_ville: int, total: int, ville: str) -> None:
    """Pie chart : part de la ville cible vs reste du Maroc."""
    st.markdown(f"**Part du total — {ville}**")
    reste = total - n_ville
    fig = go.Figure(go.Pie(
        labels=[ville, "Autres villes"],
        values=[n_ville, reste],
        hole=0.45,
        marker=dict(colors=["#3b82f6", "#e2e8f0"]),
        textinfo="percent+label",
        textfont=dict(size=13),
        hovertemplate="%{label} : %{value} agences (%{percent})<extra></extra>",
    ))
    fig.update_layout(
        margin=dict(t=10, b=10, l=10, r=10),
        height=280,
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)


def render_tab_dashboard(df_all: pd.DataFrame) -> None:
    if df_all.empty:
        st.info("Aucune donnée : lancez la collecte ou importez un fichier Excel.")
        return

    f = analytics.focus_ville(df_all, VILLE_CIBLE)
    st.markdown(f"#### Focus {VILLE_CIBLE}")
    c1, c2, c3 = st.columns(3)
    c1.metric(f"Agences à {VILLE_CIBLE}", f["n"])
    c2.metric("Part du total", f"{f['part']} %")
    c3.metric("Rang parmi les villes", f"n°{f['rang']}" if f["rang"] else "—")

    a, b, c = st.columns(3)
    with a:
        _bar(f["par_type"], f"Agences de {VILLE_CIBLE} par type")
    with b:
        _bar(f["par_source"], f"Agences de {VILLE_CIBLE} par source de collecte")
    with c:
        _pie_part(f["n"], len(df_all), VILLE_CIBLE)

    st.divider()
    st.markdown("#### Vue d'ensemble du dataset")
    a, b = st.columns(2)
    with a:
        _bar(analytics.compter(df_all, "ville", 10), "Top 10 des villes")
    with b:
        _bar(analytics.compter(df_all, "type"), "Répartition par type d'agence")

    a, b = st.columns(2)
    with a:
        croise = analytics.croiser_ville_type(df_all)
        st.markdown("**Villes × types d'agence**")
        if croise.empty:
            st.caption("Pas de données.")
        else:
            st.bar_chart(croise, height=300)
    with b:
        _bar(analytics.mots_services(df_all, 12), "Termes les plus fréquents dans les services")

    _bar(analytics.compter(df_all, "source"), "Sources de données")
