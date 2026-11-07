import html
import re

import streamlit as st

from ..config import STATUT_COLORS

esc = html.escape

_V = tuple(int(x) for x in re.findall(r"\d+", st.__version__)[:2])


def wide() -> dict:
    return {"width": "stretch"} if _V >= (1, 50) else {"use_container_width": True}


def pill(statut: str) -> str:
    return f'<span class="pill" style="background:{STATUT_COLORS[statut]}">{esc(statut)}</span>'
