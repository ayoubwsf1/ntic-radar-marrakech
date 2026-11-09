# ==============================================================================
# Fichier : cleaning.py
# Rôle : Pipeline complet de nettoyage des données d'agences avec Python et Pandas.
#        Chaque correction est enregistrée dans un rapport afin de prouver et
#        documenter la qualité du travail de nettoyage de données.
# ==============================================================================

# Permet d'utiliser les annotations de type modernes
from __future__ import annotations

# Module pour les expressions régulières (Regex)
import re
# Outils dataclass pour créer facilement des structures de données
from dataclasses import dataclass, field
# Outil pour analyser la structure des adresses web (URLs)
from urllib.parse import urlparse

# Bibliothèque Pandas pour manipuler les tableaux de données
import pandas as pd

# Importer les coordonnées des villes, les statuts et les types d'agences
from .config import CITY_COORDS, STATUTS, TYPES
# Importer la fonction de normalisation de texte (sans accents, minuscules)
from .text_utils import norm

# Liste officielle des colonnes attendues dans le fichier nettoyé
COLONNES = ["Nom", "Type", "Ville", "Taille", "Services", "Site web", "Source", "Latitude", "Longitude", "Statut", "Notes"]

# Dictionnaire de correspondance pour corriger les noms de colonnes mal écrits
_ALIAS_COLONNES = {
    "nom": "Nom", "type": "Type", "ville": "Ville", "taille": "Taille", "services": "Services",
    "site_web": "Site web", "site web": "Site web", "site": "Site web", "source": "Source",
    "latitude": "Latitude", "longitude": "Longitude", "statut": "Statut", "notes": "Notes",
}

# Dictionnaire de normalisation des noms de villes (ex: "marrakesh" devient "Marrakech")
_VILLES = {norm(v): v for v in CITY_COORDS}
_VILLES.update({
    "fes": "Fès", "kenitra": "Kénitra", "tanger": "Tanger", "tangier": "Tanger",
    "marrakesh": "Marrakech", "marrakech": "Marrakech", "sale": "Salé", "temara": "Témara",
    "laayoune": "Laâyoune", "beni mellal": "Béni Mellal", "tetouan": "Tétouan", "meknes": "Meknès"
})

# Dictionnaire de normalisation des types d'agences (ex: "dev" devient "Web & Développement")
_TYPES = {norm(t): t for t in TYPES}
_TYPES.update({
    "web": "Web & Développement", "developpement": "Web & Développement", "dev": "Web & Développement",
    "marketing": "Marketing digital", "design": "Design & Créa", "publicite": "Publicité & Com",
    "communication": "Publicité & Com", "com": "Publicité & Com"
})

# Dictionnaire de standardisation des sources de données (ex: "gmaps" devient "Google Maps")
_SOURCES = {
    "google maps": "Google Maps", "gmaps": "Google Maps", "maps": "Google Maps",
    "clutch": "Clutch.co (Maroc)", "clutch.co": "Clutch.co (Maroc)",
    "tavily": "Recherche web (Tavily)", "site officiel": "Site officiel"
}


# ------------------------------------------------------------------------------
# Classe : Rapport
# Rôle : Mémoriser le nombre de lignes au début, à la fin, et chaque correction effectuée.
# ------------------------------------------------------------------------------
@dataclass
class Rapport:
    lignes_entree: int = 0                  # Nombre de lignes au début
    lignes_sortie: int = 0                  # Nombre de lignes propres à la fin
    corrections: dict = field(default_factory=dict)  # Dictionnaire avec le détail des corrections

    # Ajouter une correction au compteur
    def add(self, cle: str, n: int) -> None:
        if n:
            self.corrections[cle] = self.corrections.get(cle, 0) + int(n)

    # Convertir le rapport en tableau Pandas pour l'enregistrer dans Excel
    def to_frame(self) -> pd.DataFrame:
        rows = [("Lignes en entrée", self.lignes_entree)] + sorted(self.corrections.items()) + [
            ("Lignes en sortie", self.lignes_sortie)
        ]
        return pd.DataFrame(rows, columns=["Opération", "Nombre"])


# ------------------------------------------------------------------------------
# Fonction : normaliser_colonnes
# Rôle : Harmoniser le nom des colonnes (ex: 'nom ' ou 'NOM' devient 'Nom').
# ------------------------------------------------------------------------------
def normaliser_colonnes(df: pd.DataFrame, rap: Rapport | None = None) -> pd.DataFrame:
    rename, changed = {}, 0
    # Parcourir chaque colonne du tableau
    for c in df.columns:
        # Nettoyer le nom de la colonne (minuscules, sans espaces superflus)
        key = re.sub(r"\s+", " ", str(c).strip().lower())
        target = _ALIAS_COLONNES.get(key)
        # Si un nom officiel existe et qu'il est différent de l'actuel
        if target and target != c:
            rename[c] = target
            changed += 1
    # Enregistrer le nombre de colonnes renommées dans le rapport
    if rap:
        rap.add("En-têtes de colonnes normalisés", changed)
    # Renommer les colonnes dans le tableau Pandas
    return df.rename(columns=rename)


# ------------------------------------------------------------------------------
# Fonction : normaliser_site
# Rôle : Nettoyer une URL web au format standard : https://domaine.tld
#        (en minuscules, sans www., sans page interne ni slash final).
# ------------------------------------------------------------------------------
def normaliser_site(url) -> str:
    s = str(url or "").strip()
    # Si l'URL est vide ou nulle
    if not s or s.lower() == "nan":
        return ""
    # Ajouter https:// si le protocole manque
    if "//" not in s:
        s = "https://" + s
    # Extraire l'hôte en minuscules
    host = urlparse(s).netloc.lower().split(":")[0]
    # Retirer le préfixe www.
    host = re.sub(r"^www\.", "", host)
    # Retourner l'URL propre s'il y a au moins un point dans le domaine
    return f"https://{host}" if "." in host else ""


# ------------------------------------------------------------------------------
# Fonction : domaine
# Rôle : Extraire le domaine pur sans le 'https://'
# ------------------------------------------------------------------------------
def domaine(url: str) -> str:
    return normaliser_site(url).replace("https://", "")


# ------------------------------------------------------------------------------
# Fonction interne : _map
# Rôle : Remplacer les valeurs d'une colonne grâce à un dictionnaire de correspondance.
# ------------------------------------------------------------------------------
def _map(series: pd.Series, table: dict, defaut: str = "") -> pd.Series:
    return series.map(lambda v: table.get(norm(str(v).strip()), defaut if str(v).strip() in ("", "nan") else str(v).strip()))


# ------------------------------------------------------------------------------
# Fonction principale : nettoyer
# Rôle : Exécuter la chaîne complète de nettoyage sur le tableau de données brut.
# Retourne : (DataFrame propre, Rapport des corrections)
# ------------------------------------------------------------------------------
def nettoyer(df: pd.DataFrame) -> tuple[pd.DataFrame, Rapport]:
    # Initialiser le rapport avec le nombre de lignes au départ
    rap = Rapport(lignes_entree=len(df))

    # Étape 0 : Normaliser le nom des colonnes
    df = normaliser_colonnes(df.copy(), rap)
    for c in COLONNES:
        if c not in df.columns:
            df[c] = ""
    df = df[COLONNES].copy()

    # Étape 1 : Nettoyer les valeurs manquantes (NaN) et espaces parasites
    before = df.isna().sum().sum()
    for c in ["Nom", "Type", "Ville", "Taille", "Services", "Site web", "Source", "Statut", "Notes"]:
        df[c] = df[c].fillna("").astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
    rap.add("Valeurs manquantes remplacées par une chaîne vide", before)

    # Étape 1b : Nettoyer les noms issus de titres web (retirer les prix, crochets et points de suspension)
    n0_ = df["Nom"].copy()
    df["Nom"] = (df["Nom"].str.replace(r"【[^】]*】|\[[^\]]*\]", "", regex=True)
                 .str.replace(r"\bà\s*\d+\s*(?:dh|mad)\b", "", regex=True, flags=re.I)
                 .str.replace(r"\s*(?:\.{3}|…)\s*$", "", regex=True)
                 .str.replace(r"\s+", " ", regex=True).str.strip(" -–—|:"))
    rap.add("Noms nettoyés (prix, crochets, points de suspension)", (n0_ != df["Nom"]).sum())

    # Étape 2 : Supprimer les lignes vides ou lignes de test (ex: 'test', 'exemple')
    vide = (df["Nom"] == "") | df["Nom"].map(norm).isin({"test", "exemple", "nan"})
    rap.add("Lignes invalides supprimées (sans nom / test)", vide.sum())
    df = df[~vide]

    # Étape 3 : Harmoniser l'écriture des villes (casse, accents)
    v0 = df["Ville"].copy()
    df["Ville"] = _map(df["Ville"], _VILLES).map(lambda v: v if v in CITY_COORDS else (v.title() if v else v))
    rap.add("Villes harmonisées (casse / accents)", (v0 != df["Ville"]).sum())

    # Étape 4 : Harmoniser les catégories d'agences
    t0 = df["Type"].copy()
    df["Type"] = _map(df["Type"], _TYPES)
    rap.add("Types d'agence harmonisés", (t0 != df["Type"]).sum())

    # Étape 5 : Harmoniser les noms des sources de collecte
    s0 = df["Source"].copy()
    df["Source"] = df["Source"].map(lambda v: _SOURCES.get(norm(v), v) if v else "Non renseignée")
    rap.add("Sources harmonisées", (s0 != df["Source"]).sum())

    # Étape 6 : Normaliser les adresses de sites web
    w0 = df["Site web"].copy()
    df["Site web"] = df["Site web"].map(normaliser_site)
    rap.add("URL normalisées (https, minuscules, sans slash final)", (w0 != df["Site web"]).sum())
    sans_site = df["Site web"] == ""
    rap.add("Lignes sans site web valide (conservées, signalées dans Notes)", sans_site.sum())
    df.loc[sans_site & (df["Notes"] == ""), "Notes"] = "Site web manquant — à compléter"

    # Étape 7 : Vérifier et réinitialiser les statuts invalides
    st0 = df["Statut"].copy()
    df["Statut"] = df["Statut"].map(lambda v: v if v in STATUTS else "Non encore postulé")
    rap.add("Statuts invalides ramenés à « Non encore postulé »", (st0 != df["Statut"]).sum())

    # Étape 8 : Supprimer les doublons (d'abord par même site web, puis par même nom)
    n0 = len(df)
    df["_dom"] = df["Site web"].map(domaine)
    df = pd.concat([df[df["_dom"] == ""], df[df["_dom"] != ""].drop_duplicates("_dom")])
    df["_nom"] = df["Nom"].map(norm)
    df = df.drop_duplicates("_nom")
    rap.add("Doublons supprimés (même site ou même nom)", n0 - len(df))

    # Étape 9 : Coordonnées GPS (assigner le centre de la ville si les coordonnées manquent)
    for c in ("Latitude", "Longitude"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    manque = df["Latitude"].isna() | df["Longitude"].isna()
    for i in df.index[manque]:
        lat, lng = CITY_COORDS.get(df.at[i, "Ville"], (31.79, -7.09))
        df.at[i, "Latitude"], df.at[i, "Longitude"] = lat, lng
    rap.add("Coordonnées GPS complétées depuis la ville", manque.sum())

    # Nettoyage final : supprimer les colonnes temporaires et trier par Ville et Nom
    df = df.drop(columns=["_dom", "_nom"]).sort_values(["Ville", "Nom"]).reset_index(drop=True)
    # Ajouter un numéro séquentiel N° en première colonne
    df.insert(0, "N°", range(1, len(df) + 1))
    rap.lignes_sortie = len(df)

    # Retourner le tableau propre et le rapport
    return df, rap
