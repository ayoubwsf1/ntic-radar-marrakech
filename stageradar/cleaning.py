"""Nettoyage des données d'agences (Python / pandas).

Chaque correction est comptabilisée dans un rapport afin de documenter
les problèmes détectés et les solutions apportées (livrable de la présentation).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

import pandas as pd

from .config import CITY_COORDS, STATUTS, TYPES
from .text_utils import norm

COLONNES = ["Nom", "Type", "Ville", "Taille", "Services", "Site web", "Source", "Latitude", "Longitude", "Statut", "Notes"]

_ALIAS_COLONNES = {
    "nom": "Nom", "type": "Type", "ville": "Ville", "taille": "Taille", "services": "Services",
    "site_web": "Site web", "site web": "Site web", "site": "Site web", "source": "Source",
    "latitude": "Latitude", "longitude": "Longitude", "statut": "Statut", "notes": "Notes",
}

_VILLES = {norm(v): v for v in CITY_COORDS}
_VILLES.update({"fes": "Fès", "kenitra": "Kénitra", "tanger": "Tanger", "tangier": "Tanger",
                "marrakesh": "Marrakech", "marrakech": "Marrakech", "sale": "Salé", "temara": "Témara",
                "laayoune": "Laâyoune", "beni mellal": "Béni Mellal", "tetouan": "Tétouan", "meknes": "Meknès"})

_TYPES = {norm(t): t for t in TYPES}
_TYPES.update({"web": "Web & Développement", "developpement": "Web & Développement", "dev": "Web & Développement",
               "marketing": "Marketing digital", "design": "Design & Créa", "publicite": "Publicité & Com",
               "communication": "Publicité & Com", "com": "Publicité & Com"})

_SOURCES = {"google maps": "Google Maps", "gmaps": "Google Maps", "maps": "Google Maps",
            "clutch": "Clutch.co (Maroc)", "clutch.co": "Clutch.co (Maroc)",
            "tavily": "Recherche web (Tavily)", "site officiel": "Site officiel"}


@dataclass
class Rapport:
    """Compteurs des corrections appliquées."""
    lignes_entree: int = 0
    lignes_sortie: int = 0
    corrections: dict = field(default_factory=dict)

    def add(self, cle: str, n: int) -> None:
        if n:
            self.corrections[cle] = self.corrections.get(cle, 0) + int(n)

    def to_frame(self) -> pd.DataFrame:
        rows = [("Lignes en entrée", self.lignes_entree)] + sorted(self.corrections.items()) + [
            ("Lignes en sortie", self.lignes_sortie)]
        return pd.DataFrame(rows, columns=["Opération", "Nombre"])


def normaliser_colonnes(df: pd.DataFrame, rap: Rapport | None = None) -> pd.DataFrame:
    rename, changed = {}, 0
    for c in df.columns:
        key = re.sub(r"\s+", " ", str(c).strip().lower())
        target = _ALIAS_COLONNES.get(key)
        if target and target != c:
            rename[c] = target
            changed += 1
    if rap:
        rap.add("En-têtes de colonnes normalisés", changed)
    return df.rename(columns=rename)


def normaliser_site(url) -> str:
    """Retourne https://domaine.tld (hôte en minuscules, sans chemin ni slash final)."""
    s = str(url or "").strip()
    if not s or s.lower() == "nan":
        return ""
    if "//" not in s:
        s = "https://" + s
    host = urlparse(s).netloc.lower().split(":")[0]
    host = re.sub(r"^www\.", "", host)
    return f"https://{host}" if "." in host else ""


def domaine(url: str) -> str:
    return normaliser_site(url).replace("https://", "")


def _map(series: pd.Series, table: dict, defaut: str = "") -> pd.Series:
    return series.map(lambda v: table.get(norm(str(v).strip()), defaut if str(v).strip() in ("", "nan") else str(v).strip()))


def nettoyer(df: pd.DataFrame) -> tuple[pd.DataFrame, Rapport]:
    """Applique toute la chaîne de nettoyage. Retourne (DataFrame propre, rapport)."""
    rap = Rapport(lignes_entree=len(df))
    df = normaliser_colonnes(df.copy(), rap)
    for c in COLONNES:
        if c not in df.columns:
            df[c] = ""
    df = df[COLONNES].copy()

    # 1. Espaces parasites et valeurs manquantes
    before = df.isna().sum().sum()
    for c in ["Nom", "Type", "Ville", "Taille", "Services", "Site web", "Source", "Statut", "Notes"]:
        df[c] = df[c].fillna("").astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
    rap.add("Valeurs manquantes remplacées par une chaîne vide", before)

    # 1b. Noms issus de titres de pages : retrait des prix, crochets et points de suspension
    n0_ = df["Nom"].copy()
    df["Nom"] = (df["Nom"].str.replace(r"【[^】]*】|\[[^\]]*\]", "", regex=True)
                 .str.replace(r"\bà\s*\d+\s*(?:dh|mad)\b", "", regex=True, flags=re.I)
                 .str.replace(r"\s*(?:\.{3}|…)\s*$", "", regex=True)
                 .str.replace(r"\s+", " ", regex=True).str.strip(" -–—|:"))
    rap.add("Noms nettoyés (prix, crochets, points de suspension)", (n0_ != df["Nom"]).sum())

    # 2. Lignes sans nom ou lignes de test
    vide = (df["Nom"] == "") | df["Nom"].map(norm).isin({"test", "exemple", "nan"})
    rap.add("Lignes invalides supprimées (sans nom / test)", vide.sum())
    df = df[~vide]

    # 3. Villes
    v0 = df["Ville"].copy()
    df["Ville"] = _map(df["Ville"], _VILLES).map(lambda v: v if v in CITY_COORDS else (v.title() if v else v))
    rap.add("Villes harmonisées (casse / accents)", (v0 != df["Ville"]).sum())

    # 4. Types
    t0 = df["Type"].copy()
    df["Type"] = _map(df["Type"], _TYPES)
    rap.add("Types d'agence harmonisés", (t0 != df["Type"]).sum())

    # 5. Sources
    s0 = df["Source"].copy()
    df["Source"] = df["Source"].map(lambda v: _SOURCES.get(norm(v), v) if v else "Non renseignée")
    rap.add("Sources harmonisées", (s0 != df["Source"]).sum())

    # 6. Sites web
    w0 = df["Site web"].copy()
    df["Site web"] = df["Site web"].map(normaliser_site)
    rap.add("URL normalisées (https, minuscules, sans slash final)", (w0 != df["Site web"]).sum())
    sans_site = df["Site web"] == ""
    rap.add("Lignes sans site web valide (conservées, signalées dans Notes)", sans_site.sum())
    df.loc[sans_site & (df["Notes"] == ""), "Notes"] = "Site web manquant — à compléter"

    # 7. Statuts
    st0 = df["Statut"].copy()
    df["Statut"] = df["Statut"].map(lambda v: v if v in STATUTS else "Non encore postulé")
    rap.add("Statuts invalides ramenés à « Non encore postulé »", (st0 != df["Statut"]).sum())

    # 8. Doublons (même domaine, puis même nom)
    n0 = len(df)
    df["_dom"] = df["Site web"].map(domaine)
    df = pd.concat([df[df["_dom"] == ""], df[df["_dom"] != ""].drop_duplicates("_dom")])
    df["_nom"] = df["Nom"].map(norm)
    df = df.drop_duplicates("_nom")
    rap.add("Doublons supprimés (même site ou même nom)", n0 - len(df))

    # 9. Coordonnées GPS (centre de la ville si manquantes)
    for c in ("Latitude", "Longitude"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    manque = df["Latitude"].isna() | df["Longitude"].isna()
    for i in df.index[manque]:
        lat, lng = CITY_COORDS.get(df.at[i, "Ville"], (31.79, -7.09))
        df.at[i, "Latitude"], df.at[i, "Longitude"] = lat, lng
    rap.add("Coordonnées GPS complétées depuis la ville", manque.sum())

    df = df.drop(columns=["_dom", "_nom"]).sort_values(["Ville", "Nom"]).reset_index(drop=True)
    df.insert(0, "N°", range(1, len(df) + 1))
    rap.lignes_sortie = len(df)
    return df, rap
