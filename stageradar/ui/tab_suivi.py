"""Onglet Suivi : la progression des candidatures et le bouton pour exporter en Excel."""
import io  # pour écrire le fichier Excel en mémoire

import pandas as pd  # pour les listes de données
import streamlit as st  # pour afficher

from ..config import STATUT_COLORS, STATUTS  # pour les couleurs et l'ordre des statuts
from .helpers import esc, wide  # pour protéger le texte et la largeur


def _barres(series: pd.Series, color_map: dict | None = None, top: int | None = None, default: str = "#6366f1") -> str:
    # Crée des barres HTML pour afficher un compteur
    s = series if series.dtype.kind in "iu" else series.value_counts()  # si ce n'est pas un compteur, on le crée
    if top:  # si on veut seulement les premiers
        s = s.head(top)  # on garde les premiers éléments
    mx = max(s.max(), 1) if len(s) else 1  # le plus grand nombre, pour la taille des barres
    out = ""  # le texte HTML que l'on construit
    for label, n in s.items():  # pour chaque ligne
        c = (color_map or {}).get(label, default)  # la couleur de la ligne
        out += (f'<div class="bar-row"><div class="bar-label">{esc(str(label))}</div><div class="bar-track">'
                f'<div class="bar-fill" style="width:{n / mx * 100:.0f}%;background:{c}"></div></div><div class="bar-n">{n}</div></div>')
    return out  # on renvoie le HTML


def _bouton_export(df_all: pd.DataFrame) -> None:
    # Affiche le bouton pour télécharger le suivi en Excel
    export = df_all[["nom", "type", "ville", "site", "statut", "preuve", "maj"]].rename(  # on garde seulement les colonnes utiles
        columns={"nom": "Nom", "type": "Type", "ville": "Ville", "site": "Site web", "statut": "Statut",
                 "preuve": "Dernière preuve (mail)", "maj": "Mis à jour"})
    buf = io.BytesIO()  # un fichier en mémoire
    export.to_excel(buf, index=False, sheet_name="Suivi")  # on écrit les données en Excel
    st.download_button("Exporter le suivi (Excel)", buf.getvalue(), "suivi_candidatures.xlsx",  # bouton de téléchargement
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", **wide())


def render_tab_suivi(df_all: pd.DataFrame) -> None:
    # Affiche la progression des candidatures
    if df_all.empty:  # si il n'y a pas de données
        st.info("Aucune donnée.")  # message d'information
        return  # on arrête

    total = len(df_all)  # le nombre total d'agences
    applied = int((df_all["statut"] != "Non encore postulé").sum())  # le nombre d'agences où l'on a postulé
    st.markdown(f"#### Progression : **{applied}/{total}** candidatures ({applied / total * 100:.0f} %)")  # le titre avec le pourcentage
    st.progress(applied / total)  # la barre de progression

    a, b = st.columns(2)  # deux colonnes
    with a:  # colonne de gauche
        st.markdown("**Par statut**")  # titre
        st.markdown(_barres(df_all["statut"].value_counts().reindex(STATUTS, fill_value=0), STATUT_COLORS), unsafe_allow_html=True)  # barres par statut
        st.markdown("**Par type d'agence**")  # titre
        st.markdown(_barres(df_all["type"]), unsafe_allow_html=True)  # barres par type
    with b:  # colonne de droite
        st.markdown("**Par ville (top 10)**")  # titre
        st.markdown(_barres(df_all["ville"], top=10, default="#0ea5e9"), unsafe_allow_html=True)  # barres par ville

    _bouton_export(df_all)  # le bouton pour exporter en Excel
