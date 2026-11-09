"""Petites fonctions utiles pour l'interface."""
import html  # pour protéger le texte avant de l'afficher en HTML
import re  # pour chercher des nombres dans un texte

import streamlit as st  # pour la version de Streamlit

from ..config import STATUT_COLORS  # pour les couleurs des statuts

esc = html.escape  # on donne un nom court à la fonction qui protège le texte

_V = tuple(int(x) for x in re.findall(r"\d+", st.__version__)[:2])  # la version de Streamlit, par exemple (1, 50)


def wide() -> dict:
    # Donne la largeur pour un bouton, selon la version de Streamlit
    return {"width": "stretch"} if _V >= (1, 50) else {"use_container_width": True}


def pill(statut: str) -> str:
    # Crée une petite étiquette colorée avec le statut
    return f'<span class="pill" style="background:{STATUT_COLORS[statut]}">{esc(statut)}</span>'  # le texte HTML de l'étiquette
