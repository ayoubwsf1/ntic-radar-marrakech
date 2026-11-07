"""Analyses descriptives des données (utilisées par le tableau de bord et les scripts)."""
from __future__ import annotations

import re
from collections import Counter

import pandas as pd

from .config import VILLE_CIBLE
from .text_utils import norm

_STOP_SERV = set("""et de des du la le les en pour au aux un une the and of with web site sites agence agences digital
services service solutions marketing creation conception développement developpement
maroc nous est votre vous notre nos vos dans sur par plus avec qui que sont tout toutes tous votre vos ainsi
agency your our you are for from les ses leur cette ces pas sans entre vers chez aussi comme mais ont été""".split())


def compter(df: pd.DataFrame, col: str, top: int | None = None) -> pd.Series:
    if df.empty or col not in df:
        return pd.Series(dtype=int)
    s = df[col].replace("", pd.NA).dropna().value_counts()
    return s.head(top) if top else s


def croiser_ville_type(df: pd.DataFrame, villes: int = 8) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    top = compter(df, "ville", villes).index
    return pd.crosstab(df[df["ville"].isin(top)]["ville"], df["type"])


def mots_services(df: pd.DataFrame, top: int = 12) -> pd.Series:
    """Termes les plus fréquents dans la colonne `services` (hors mots vides)."""
    if df.empty or "services" not in df:
        return pd.Series(dtype=int)
    c: Counter = Counter()
    for t in df["services"].fillna("").astype(str):
        c.update(w for w in re.findall(r"[a-zà-ÿ+#]{3,}", t.lower()) if norm(w) not in _STOP_SERV)
    return pd.Series(dict(c.most_common(top)), dtype=int)


def qualite(df: pd.DataFrame) -> pd.DataFrame:
    """Taux de complétude par colonne (en %)."""
    if df.empty:
        return pd.DataFrame(columns=["colonne", "renseigné (%)"])
    rows = []
    for c in ["nom", "type", "ville", "taille", "services", "site", "source"]:
        if c in df:
            ok = (df[c].fillna("").astype(str).str.strip().replace("n.c.", "") != "").mean() * 100
            rows.append((c, round(ok, 1)))
    return pd.DataFrame(rows, columns=["colonne", "renseigné (%)"])


def focus_ville(df: pd.DataFrame, ville: str = VILLE_CIBLE) -> dict:
    d = df[df["ville"] == ville] if not df.empty else df
    total = len(df)
    return {
        "ville": ville, "n": len(d), "part": round(len(d) / total * 100, 1) if total else 0.0,
        "rang": int(compter(df, "ville").rank(ascending=False, method="min").get(ville, 0)) if total else 0,
        "par_type": compter(d, "type"), "par_source": compter(d, "source"),
    }

