# ==============================================================================
# Fichier : filters.py
# Rôle : Filtrer le tableau des agences selon les critères choisis par l'utilisateur
#        dans la barre latérale (sidebar) : recherche texte, ville, type et statut.
# ==============================================================================

# Permet d'utiliser les annotations de type modernes
from __future__ import annotations

# Module pour les expressions régulières (Regex)
import re
# Outil pour créer des classes de données
from dataclasses import dataclass

# Bibliothèque Pandas pour manipuler les données
import pandas as pd

# Importer la fonction de normalisation de texte
from .text_utils import norm


# ------------------------------------------------------------------------------
# Classe : Filtres
# Rôle : Regrouper les options de filtrage sélectionnées dans l'interface.
# ------------------------------------------------------------------------------
@dataclass
class Filtres:
    q: str            # Texte libre tapé dans la barre de recherche (ex: "python")
    ville: list       # Liste des villes sélectionnées (ex: ["Marrakech"])
    type_: list       # Liste des types d'agences sélectionnés (ex: ["Web & Développement"])
    statut: list      # Liste des statuts sélectionnés (ex: ["Accepté", "Entretien"])


# ------------------------------------------------------------------------------
# Fonction principale : appliquer_filtres
# Rôle : Prendre le tableau complet de toutes les agences et renvoyer
#        uniquement les lignes qui correspondent aux filtres choisis.
# ------------------------------------------------------------------------------
def appliquer_filtres(df_all: pd.DataFrame, f: Filtres) -> pd.DataFrame:
    # Faire une copie du tableau original pour ne pas le modifier directement
    df = df_all.copy()

    # 1. Filtre par recherche textuelle (recherche dans nom, ville, services et type)
    if f.q.strip():
        # Normaliser le texte recherché (minuscules, sans accents)
        needle = norm(f.q)
        # Combiner toutes les colonnes textuelles en une seule grande chaîne normalisée
        hay = (df["nom"] + " " + df["ville"] + " " + df["services"] + " " + df["type"]).map(norm)
        # Ne garder que les lignes qui contiennent le mot recherché
        df = df[hay.str.contains(re.escape(needle), regex=True)]

    # 2. Filtre par Ville (si au moins une ville est cochée)
    if f.ville:
        df = df[df["ville"].isin(f.ville)]

    # 3. Filtre par Type d'agence (si au moins un type est coché)
    if f.type_:
        df = df[df["type"].isin(f.type_)]

    # 4. Filtre par Statut de candidature (si au moins un statut est coché)
    if f.statut:
        df = df[df["statut"].isin(f.statut)]

    # Retourner le tableau filtré
    return df
