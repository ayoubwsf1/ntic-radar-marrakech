"""Configuration centrale : chemins, constantes métier et lecture des secrets."""
from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _charger_env(chemin: Path) -> None:
    """Charge un fichier .env (CLE=valeur) sans dépendance externe ; l'environnement réel a priorité."""
    if not chemin.exists():
        return
    for ligne in chemin.read_text(encoding="utf-8").splitlines():
        ligne = ligne.strip()
        if ligne and not ligne.startswith("#") and "=" in ligne:
            cle, _, val = ligne.partition("=")
            os.environ.setdefault(cle.strip(), val.strip().strip('"').strip("'"))


_charger_env(BASE_DIR / ".env")
DATA_DIR = BASE_DIR / "data"

# La base SQLite peut être déplacée via la variable d'environnement RADAR_DB
DB_PATH = Path(os.environ.get("RADAR_DB", BASE_DIR / "stages.db"))
XLSX_PATH = Path(os.environ.get("RADAR_XLSX", DATA_DIR / "agences_maroc.xlsx"))
RAW_XLSX_PATH = DATA_DIR / "raw" / "agences_maroc_avant_nettoyage.xlsx"
CLEAN_XLSX_PATH = DATA_DIR / "cleaned" / "agences_apres_nettoyage.xlsx"
FIGURES_DIR = BASE_DIR / "docs" / "figures"

VILLE_CIBLE = "Marrakech"

STATUTS = ["Non encore postulé", "Entretien", "Accepté", "Refusé"]

RANK = {"Non encore postulé": 0, "Entretien": 2, "Accepté": 3, "Refusé": 3}

STATUT_COLORS = {
    "Non encore postulé": "#64748b",
    "Entretien": "#d97706",
    "Accepté": "#16a34a",
    "Refusé": "#dc2626",
}

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

TYPES = ["Web & Développement", "Marketing digital", "Design & Créa", "Publicité & Com"]

# Type de candidature visé (profil et CV)
CONTRATS = ["Stage", "Alternance", "Emploi", "Freelance"]

# Modèle de langage — OpenRouter (free) ou Anthropic
LLM_MODEL = os.environ.get("RADAR_LLM_MODEL", "mistralai/mistral-7b-instruct:free")
LLM_URL   = "https://openrouter.ai/api/v1/chat/completions"


def get_secret(name: str, default: str = "") -> str:
    """Lit un secret : variable d'environnement d'abord, puis st.secrets si disponible."""
    val = os.environ.get(name)
    if val:
        return val
    try:  # Streamlit Community Cloud : .streamlit/secrets.toml ou onglet « Secrets »
        import streamlit as st

        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass
    return default
