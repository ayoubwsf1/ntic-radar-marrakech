import io

import pandas as pd
import streamlit as st

from ..config import STATUT_COLORS, STATUTS
from .helpers import esc, wide


def _barres(series: pd.Series, color_map: dict | None = None, top: int | None = None, default: str = "#6366f1") -> str:
    s = series if series.dtype.kind in "iu" else series.value_counts()
    if top:
        s = s.head(top)
    mx = max(s.max(), 1) if len(s) else 1
    out = ""
    for label, n in s.items():
        c = (color_map or {}).get(label, default)
        out += (f'<div class="bar-row"><div class="bar-label">{esc(str(label))}</div><div class="bar-track">'
                f'<div class="bar-fill" style="width:{n / mx * 100:.0f}%;background:{c}"></div></div><div class="bar-n">{n}</div></div>')
    return out


def _bouton_export(df_all: pd.DataFrame) -> None:
    export = df_all[["nom", "type", "ville", "site", "statut", "preuve", "maj"]].rename(
        columns={"nom": "Nom", "type": "Type", "ville": "Ville", "site": "Site web", "statut": "Statut",
                 "preuve": "Dernière preuve (mail)", "maj": "Mis à jour"})
    buf = io.BytesIO()
    export.to_excel(buf, index=False, sheet_name="Suivi")
    st.download_button("Exporter le suivi (Excel)", buf.getvalue(), "suivi_candidatures.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", **wide())


def render_tab_suivi(df_all: pd.DataFrame) -> None:
    if df_all.empty:
        st.info("Aucune donnée.")
        return

    total = len(df_all)
    applied = int((df_all["statut"] != "Non encore postulé").sum())
    st.markdown(f"#### Progression : **{applied}/{total}** candidatures ({applied / total * 100:.0f} %)")
    st.progress(applied / total)

    a, b = st.columns(2)
    with a:
        st.markdown("**Par statut**")
        st.markdown(_barres(df_all["statut"].value_counts().reindex(STATUTS, fill_value=0), STATUT_COLORS), unsafe_allow_html=True)
        st.markdown("**Par type d'agence**")
        st.markdown(_barres(df_all["type"]), unsafe_allow_html=True)
    with b:
        st.markdown("**Par ville (top 10)**")
        st.markdown(_barres(df_all["ville"], top=10, default="#0ea5e9"), unsafe_allow_html=True)

    _bouton_export(df_all)
