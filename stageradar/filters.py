from __future__ import annotations

import re
from dataclasses import dataclass

import pandas as pd

from .text_utils import norm


@dataclass
class Filtres:
    q: str
    ville: list
    type_: list
    statut: list


def appliquer_filtres(df_all: pd.DataFrame, f: Filtres) -> pd.DataFrame:
    df = df_all.copy()

    if f.q.strip():
        needle = norm(f.q)
        hay = (df["nom"] + " " + df["ville"] + " " + df["services"] + " " + df["type"]).map(norm)
        df = df[hay.str.contains(re.escape(needle), regex=True)]

    if f.ville:
        df = df[df["ville"].isin(f.ville)]
    if f.type_:
        df = df[df["type"].isin(f.type_)]
    if f.statut:
        df = df[df["statut"].isin(f.statut)]

    return df
