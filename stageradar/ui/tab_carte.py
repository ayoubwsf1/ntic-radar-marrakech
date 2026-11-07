import pandas as pd
import pydeck as pdk
import streamlit as st

from ..config import CITY_COORDS, STATUT_COLORS
from .helpers import esc, wide

_STYLES = {"Clair": "light", "Sombre": "dark", "Routes": "road"}


def _hex_to_rgba(color_hex: str) -> list:
    return [int(color_hex[i:i + 2], 16) for i in (1, 3, 5)] + [230]


def _vue(focus: str) -> pdk.ViewState:
    if focus == "Tout le Maroc":
        return pdk.ViewState(latitude=31.8, longitude=-7.1, zoom=4.7)
    la, ln = CITY_COORDS.get(focus, (31.8, -7.1))
    return pdk.ViewState(latitude=la, longitude=ln, zoom=10.5)


def render_tab_carte(df: pd.DataFrame) -> None:
    mdf = df.dropna(subset=["lat", "lng"]).copy()
    if mdf.empty:
        st.info("Aucune agence à afficher sur la carte.")
        return

    m1, m2, _ = st.columns([1, 1.4, 1])
    focus = m1.selectbox("Zoom sur", ["Tout le Maroc"] + sorted(mdf["ville"].unique()))
    style = m2.radio("Fond de carte", list(_STYLES), horizontal=True)

    mdf["color"] = mdf["statut"].map(lambda s: _hex_to_rgba(STATUT_COLORS[s]))
    layer = pdk.Layer(
        "ScatterplotLayer", data=mdf[["nom", "ville", "statut", "type", "lat", "lng", "color"]],
        get_position="[lng, lat]", get_fill_color="color", get_line_color=[255, 255, 255, 255],
        stroked=True, line_width_min_pixels=2, get_radius=1, radius_min_pixels=8, radius_max_pixels=18, pickable=True,
    )
    deck = pdk.Deck(
        layers=[layer], initial_view_state=_vue(focus), map_style=_STYLES[style],
        tooltip={
            "html": "<b>{nom}</b><br/>{ville}<br/>{type}<br/><i>{statut}</i>",
            "style": {"backgroundColor": "#0f172a", "color": "white", "borderRadius": "10px", "padding": "8px 12px", "fontFamily": "Inter, sans-serif"},
        },
    )
    st.pydeck_chart(deck, height=560, **wide())

    st.markdown(
        '<div class="legend">' + "".join(f'<span><i style="background:{c}"></i>{esc(s)}</span>' for s, c in STATUT_COLORS.items()) + "</div>",
        unsafe_allow_html=True,
    )
    st.caption("Les points sont placés au centre de chaque ville (léger décalage pour éviter la superposition) : ce ne sont pas des adresses exactes.")
