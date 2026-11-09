"""Onglet Carte : une carte du Maroc avec un point pour chaque agence."""
import pandas as pd  # pour les listes de données
import pydeck as pdk  # pour la carte interactive
import streamlit as st  # pour afficher la carte

from ..config import CITY_COORDS, STATUT_COLORS  # pour les coordonnées des villes et les couleurs des statuts
from .helpers import esc, wide  # pour protéger le texte et la largeur

_STYLES = {"Clair": "light", "Sombre": "dark", "Routes": "road"}  # les styles de fond de carte


def _hex_to_rgba(color_hex: str) -> list:
    # Convertit une couleur comme "#ff0000" en liste [rouge, vert, bleu, opacité]
    return [int(color_hex[i:i + 2], 16) for i in (1, 3, 5)] + [230]


def _vue(focus: str) -> pdk.ViewState:
    # Donne la vue de la carte selon la ville choisie
    if focus == "Tout le Maroc":  # si on veut voir tout le pays
        return pdk.ViewState(latitude=31.8, longitude=-7.1, zoom=4.7)  # vue large
    la, ln = CITY_COORDS.get(focus, (31.8, -7.1))  # les coordonnées de la ville
    return pdk.ViewState(latitude=la, longitude=ln, zoom=10.5)  # vue zoomée sur la ville


def render_tab_carte(df: pd.DataFrame) -> None:
    # Affiche la carte avec les agences
    mdf = df.dropna(subset=["lat", "lng"]).copy()  # on garde seulement les agences avec une position
    if mdf.empty:  # si aucune agence n'a de position
        st.info("Aucune agence à afficher sur la carte.")  # message d'information
        return  # on arrête

    m1, m2, _ = st.columns([1, 1.4, 1])  # deux colonnes pour les choix
    focus = m1.selectbox("Zoom sur", ["Tout le Maroc"] + sorted(mdf["ville"].unique()))  # liste pour choisir la ville
    style = m2.radio("Fond de carte", list(_STYLES), horizontal=True)  # choix du style de la carte

    mdf["color"] = mdf["statut"].map(lambda s: _hex_to_rgba(STATUT_COLORS[s]))  # la couleur de chaque point selon le statut
    layer = pdk.Layer(  # la couche de points sur la carte
        "ScatterplotLayer", data=mdf[["nom", "ville", "statut", "type", "lat", "lng", "color"]],
        get_position="[lng, lat]", get_fill_color="color", get_line_color=[255, 255, 255, 255],
        stroked=True, line_width_min_pixels=2, get_radius=1, radius_min_pixels=8, radius_max_pixels=18, pickable=True,
    )
    deck = pdk.Deck(  # la carte complète
        layers=[layer], initial_view_state=_vue(focus), map_style=_STYLES[style],
        tooltip={
            "html": "<b>{nom}</b><br/>{ville}<br/>{type}<br/><i>{statut}</i>",
            "style": {"backgroundColor": "#0f172a", "color": "white", "borderRadius": "10px", "padding": "8px 12px", "fontFamily": "Inter, sans-serif"},
        },
    )
    st.pydeck_chart(deck, height=560, **wide())  # on affiche la carte

    st.markdown(
        '<div class="legend">' + "".join(f'<span><i style="background:{c}"></i>{esc(s)}</span>' for s, c in STATUT_COLORS.items()) + "</div>",
        unsafe_allow_html=True,
    )
    st.caption("Les points sont placés au centre de chaque ville (léger décalage pour éviter la superposition) : ce ne sont pas des adresses exactes.")
