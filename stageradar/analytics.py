# ==============================================================================
# Fichier : analytics.py
# Rôle : Fonctions d'analyse statistique et descriptive des données d'agences.
#        Utilisé par le tableau de bord Streamlit (dashboard) et le script explore.py.
# ==============================================================================

# Permet d'utiliser les annotations de type modernes
from __future__ import annotations

# Module pour utiliser les expressions régulières (Regex)
import re
# Compteur automatique d'éléments (Counter)
from collections import Counter

# Bibliothèque Pandas pour le traitement de données
import pandas as pd

# Importer la ville cible (Marrakech)
from .config import VILLE_CIBLE
# Importer la fonction de normalisation de texte
from .text_utils import norm

# Liste des mots vides (stop words) en français et anglais à ignorer lors de l'analyse des textes
# (ex: "le", "la", "et", "de", "web", "agence" car ils ne donnent pas d'information spécifique)
_STOP_SERV = set("""et de des du la le les en pour au aux un une the and of with web site sites agence agences digital
services service solutions marketing creation conception développement developpement
maroc nous est votre vous notre nos vos dans sur par plus avec qui que sont tout toutes tous votre vos ainsi
agency your our you are for from les ses leur cette ces pas sans entre vers chez aussi comme mais ont été""".split())


# ------------------------------------------------------------------------------
# Fonction : compter
# Rôle : Compter le nombre d'occurrences d'une colonne (ex: nombre d'agences par ville)
#        et renvoyer les plus fréquentes (top N).
# ------------------------------------------------------------------------------
def compter(df: pd.DataFrame, col: str, top: int | None = None) -> pd.Series:
    # Si le tableau est vide ou que la colonne n'existe pas
    if df.empty or col not in df:
        return pd.Series(dtype=int)
    # Compter les valeurs non vides en ordre décroissant
    s = df[col].replace("", pd.NA).dropna().value_counts()
    # Retourner les 'top' premiers si demandé, sinon toute la série
    return s.head(top) if top else s


# ------------------------------------------------------------------------------
# Fonction : croiser_ville_type
# Rôle : Créer un tableau croisé dynamique (crosstab) entre les villes et les types d'agences.
# ------------------------------------------------------------------------------
def croiser_ville_type(df: pd.DataFrame, villes: int = 8) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    # Sélectionner les N premières villes ayant le plus d'agences
    top = compter(df, "ville", villes).index
    # Construire la table de contingence (Ville en lignes, Type d'agence en colonnes)
    return pd.crosstab(df[df["ville"].isin(top)]["ville"], df["type"])


# ------------------------------------------------------------------------------
# Fonction : mots_services
# Rôle : Extraire et compter les mots-clés de compétences les plus fréquents
#        dans la colonne 'services' (ex: 'seo', 'react', 'design', 'ecommerce').
# ------------------------------------------------------------------------------
def mots_services(df: pd.DataFrame, top: int = 12) -> pd.Series:
    if df.empty or "services" not in df:
        return pd.Series(dtype=int)
    # Initialiser le compteur de mots
    c: Counter = Counter()
    # Parcourir chaque texte de description de service
    for t in df["services"].fillna("").astype(str):
        # Trouver tous les mots d'au moins 3 lettres et exclure les mots vides
        c.update(w for w in re.findall(r"[a-zà-ÿ+#]{3,}", t.lower()) if norm(w) not in _STOP_SERV)
    # Renvoyer les mots les plus fréquents sous forme de Série Pandas
    return pd.Series(dict(c.most_common(top)), dtype=int)


# ------------------------------------------------------------------------------
# Fonction : qualite
# Rôle : Calculer le pourcentage de données renseignées pour chaque colonne
#        (indicateur de la complétude et de la qualité des données).
# ------------------------------------------------------------------------------
def qualite(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["colonne", "renseigné (%)"])
    rows = []
    # Vérifier les colonnes principales une par une
    for c in ["nom", "type", "ville", "taille", "services", "site", "source"]:
        if c in df:
            # Calculer le taux de valeurs non vides (exclure 'n.c.')
            ok = (df[c].fillna("").astype(str).str.strip().replace("n.c.", "") != "").mean() * 100
            rows.append((c, round(ok, 1)))
    # Retourner le tableau récapitulatif de qualité
    return pd.DataFrame(rows, columns=["colonne", "renseigné (%)"])


# ------------------------------------------------------------------------------
# Fonction : focus_ville
# Rôle : Calculer les statistiques ciblées pour une ville précise (par défaut Marrakech) :
#        - Nombre d'agences
#        - Part en pourcentage par rapport au Maroc
#        - Classement national (rang)
#        - Répartition par type et par source
# ------------------------------------------------------------------------------
def focus_ville(df: pd.DataFrame, ville: str = VILLE_CIBLE) -> dict:
    # Filtrer les agences de la ville demandée
    d = df[df["ville"] == ville] if not df.empty else df
    total = len(df)
    return {
        "ville": ville,                                                   # Nom de la ville
        "n": len(d),                                                      # Nombre d'agences dans cette ville
        "part": round(len(d) / total * 100, 1) if total else 0.0,         # Part en % du total national
        # Position de la ville dans le classement des villes marocaines
        "rang": int(compter(df, "ville").rank(ascending=False, method="min").get(ville, 0)) if total else 0,
        "par_type": compter(d, "type"),                                  # Nombre d'agences par spécialité
        "par_source": compter(d, "source"),                              # Nombre d'agences par source
    }
