# ==============================================================================
# Fichier : config.py
# Rôle : Configuration centrale du projet : définit les chemins des fichiers,
#        les constantes (villes, couleurs, statuts) et la lecture des clés secrètes.
# ==============================================================================

# Permet d'utiliser les annotations de type modernes
from __future__ import annotations

# Module pour accéder aux variables d'environnement du système
import os
# Module pour manipuler les chemins de fichiers de façon portable (Windows/Linux/Mac)
from pathlib import Path

# Chemin absolu de la racine du projet (le dossier principal claude 2)
BASE_DIR = Path(__file__).resolve().parent.parent


# ------------------------------------------------------------------------------
# Fonction : _charger_env
# Rôle : Lire le fichier .env (qui contient les clés secrètes CLE=VALEUR)
#        et les enregistrer dans l'environnement Python sans dépendre d'une bibliothèque externe.
# ------------------------------------------------------------------------------
def _charger_env(chemin: Path) -> None:
    # Si le fichier .env n'existe pas, on ne fait rien
    if not chemin.exists():
        return
    # Lire chaque ligne du fichier .env
    for ligne in chemin.read_text(encoding="utf-8").splitlines():
        # Enlever les espaces au début et à la fin de la ligne
        ligne = ligne.strip()
        # Si la ligne n'est pas vide, n'est pas un commentaire (#), et contient le signe '='
        if ligne and not ligne.startswith("#") and "=" in ligne:
            # Séparer la clé et sa valeur au premier '='
            cle, _, val = ligne.partition("=")
            # Enregistrer dans os.environ si la clé n'existe pas encore
            os.environ.setdefault(cle.strip(), val.strip().strip('"').strip("'"))


# Charger automatiquement le fichier .env qui se trouve à la racine
_charger_env(BASE_DIR / ".env")

# Chemin du dossier contenant les données (data/)
DATA_DIR = BASE_DIR / "data"

# Chemin vers la base de données SQLite (par défaut stages.db à la racine)
DB_PATH = Path(os.environ.get("RADAR_DB", BASE_DIR / "stages.db"))
# Chemin vers le fichier Excel principal des 229 agences
XLSX_PATH = Path(os.environ.get("RADAR_XLSX", DATA_DIR / "agences_maroc.xlsx"))
# Chemin vers le fichier Excel brut (avant le nettoyage)
RAW_XLSX_PATH = DATA_DIR / "raw" / "agences_maroc_avant_nettoyage.xlsx"
# Chemin vers le fichier Excel après le nettoyage automatique
CLEAN_XLSX_PATH = DATA_DIR / "cleaned" / "agences_apres_nettoyage.xlsx"
# Dossier où sont enregistrées les images des graphiques
FIGURES_DIR = BASE_DIR / "docs" / "figures"

# Ville principale ciblée par l'application
VILLE_CIBLE = "Marrakech"

# Liste officielle des 4 statuts possibles pour le suivi d'une candidature
STATUTS = ["Non encore postulé", "Entretien", "Accepté", "Refusé"]

# Niveau d'avancement (rang) de chaque statut pour empêcher de rétrograder
# Ex : si le statut est 'Entretien' (rang 2), on ne peut pas revenir à 'Non postulé' (rang 0)
RANK = {"Non encore postulé": 0, "Entretien": 2, "Accepté": 3, "Refusé": 3}

# Code couleur hexadécimal associé à chaque statut pour l'affichage visuel
STATUT_COLORS = {
    "Non encore postulé": "#64748b",  # Gris
    "Entretien": "#d97706",           # Orange
    "Accepté": "#16a34a",             # Vert
    "Refusé": "#dc2626",              # Rouge
}

# Coordonnées géographiques GPS (Latitude, Longitude) des 20 villes marocaines
CITY_COORDS = {
    "Casablanca": (33.5731, -7.5898), "Rabat": (34.0209, -6.8416),
    "Marrakech": (31.6295, -7.9811), "Tanger": (35.7595, -5.8340),
    "Fès": (34.0331, -5.0003), "Agadir": (30.4278, -9.5981),
    "El Jadida": (33.2316, -8.5007), "Kénitra": (34.2610, -6.5802),
    "Témara": (33.9287, -6.9067), "Martil": (35.6167, -5.2750),
    "Tiznit": (29.6974, -9.7316), "Errachidia": (31.9314, -4.4244),
    "Larache": (35.1932, -6.1557), "Meknès": (33.8935, -5.5473),
    "Oujda": (34.6814, -1.9086), "Tétouan": (35.5785, -5.3684),
    "Salé": (34.0531, -6.7985), "Mohammedia": (33.6861, -7.3829),
    "Laâyoune": (27.1253, -13.1625), "Béni Mellal": (32.3373, -6.3498),
}

# Les 4 grands secteurs d'activité des agences
TYPES = ["Web & Développement", "Marketing digital", "Design & Créa", "Publicité & Com"]

# Les types de contrats recherchés par le candidat (pour le profil et le CV)
CONTRATS = ["Stage", "Alternance", "Emploi", "Freelance"]

# Modèle d'Intelligence Artificielle utilisé (Mistral 7B gratuit via OpenRouter)
LLM_MODEL = os.environ.get("RADAR_LLM_MODEL", "mistralai/mistral-7b-instruct:free")
# Point de terminaison (URL) de l'API OpenRouter
LLM_URL   = "https://openrouter.ai/api/v1/chat/completions"


# ------------------------------------------------------------------------------
# Fonction : get_secret
# Rôle : Récupérer une clé secrète de manière sécurisée :
#        1. D'abord dans les variables d'environnement du système (.env)
#        2. Sinon dans Streamlit Secrets (pour le déploiement sur Streamlit Cloud)
#        3. Sinon renvoyer la valeur par défaut
# ------------------------------------------------------------------------------
def get_secret(name: str, default: str = "") -> str:
    # 1. Vérifier si la variable existe dans l'environnement du système
    val = os.environ.get(name)
    if val:
        return val
    # 2. Vérifier si Streamlit secrets est disponible (sur le Cloud)
    try:
        import streamlit as st

        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass
    # 3. Retourner la valeur par défaut si rien n'a été trouvé
    return default
