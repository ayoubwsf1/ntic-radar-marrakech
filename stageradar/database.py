# ==============================================================================
# Fichier : database.py
# Rôle : Gestion de la base de données SQLite locale (stages.db).
#        Création des tables, synchronisation avec le fichier Excel,
#        mise à jour des statuts de candidature et sauvegarde du profil.
# ==============================================================================

# Permet d'utiliser les annotations de type modernes
from __future__ import annotations

# Module Python standard pour utiliser la base de données relationnelle SQLite
import sqlite3
# Outil pour fermer automatiquement la connexion à la base de données à la fin
from contextlib import closing
# Module pour récupérer la date et l'heure actuelles
from datetime import datetime
# Module pour manipuler les chemins de fichiers
from pathlib import Path
# Type optionnel (valeur ou None)
from typing import Optional

# Bibliothèque Pandas pour manipuler les tableaux de données
import pandas as pd

# Importer le chemin de la base de données, les statuts et le chemin du fichier Excel
from .config import DB_PATH, STATUTS, XLSX_PATH


# ------------------------------------------------------------------------------
# Fonction interne : _db
# Rôle : Ouvrir une connexion sécurisée à SQLite et permettre d'accéder
#        aux colonnes par leur nom (ex: row['nom']).
# ------------------------------------------------------------------------------
def _db():
    # Créer le dossier parent s'il n'existe pas
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Se connecter au fichier SQLite stages.db
    con = sqlite3.connect(DB_PATH)
    # Configurer l'accès aux résultats sous forme de dictionnaire (par nom de colonne)
    con.row_factory = sqlite3.Row
    # Retourner la connexion encapsulée pour fermeture automatique
    return closing(con)


# ------------------------------------------------------------------------------
# Fonction interne : _num
# Rôle : Convertir une valeur en nombre décimal (float) en toute sécurité,
#        ou renvoyer None si la conversion est impossible (valeur vide).
# ------------------------------------------------------------------------------
def _num(v) -> Optional[float]:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------------------
# Fonction : init_db
# Rôle : Initialiser la structure de la base de données (créer les tables si elles n'existent pas).
# ------------------------------------------------------------------------------
def init_db() -> None:
    with _db() as con:
        # 1. Créer la table 'agences' avec toutes ses colonnes
        con.execute(
            """CREATE TABLE IF NOT EXISTS agences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT UNIQUE NOT NULL,
                type TEXT DEFAULT '', ville TEXT DEFAULT '', taille TEXT DEFAULT '',
                services TEXT DEFAULT '', site TEXT DEFAULT '', source TEXT DEFAULT '',
                lat REAL, lng REAL,
                statut TEXT NOT NULL DEFAULT 'Non encore postulé',
                preuve TEXT DEFAULT '', maj TEXT DEFAULT '', notes TEXT DEFAULT ''
            )"""
        )
        # 2. Harmoniser les anciens statuts 'Postulé' vers 'Non encore postulé'
        con.execute("UPDATE agences SET statut='Non encore postulé' WHERE statut='Postulé'")
        # 3. Créer la table 'reglages' pour sauvegarder le profil candidat (clé / valeur)
        con.execute("CREATE TABLE IF NOT EXISTS reglages (cle TEXT PRIMARY KEY, valeur TEXT)")
        # Valider les changements dans la base
        con.commit()


# ------------------------------------------------------------------------------
# Fonction : sync_from_excel
# Rôle : Importer les agences depuis le fichier Excel vers la base de données SQLite.
#        N'ajoute que les nouvelles agences grâce à 'INSERT OR IGNORE'.
# ------------------------------------------------------------------------------
def sync_from_excel(path: Path = XLSX_PATH) -> int:
    # Si le fichier Excel n'existe pas, renvoyer 0
    if not Path(path).exists():
        return 0
    # Lire le fichier Excel avec Pandas
    df = pd.read_excel(path, sheet_name="Agences").fillna("")
    added = 0
    with _db() as con:
        # Parcourir chaque agence du tableau Excel
        for _, r in df.iterrows():
            nom = str(r.get("Nom", "")).strip()
            # Ignorer les lignes sans nom
            if not nom:
                continue
            # Vérifier que le statut est valide
            statut = str(r.get("Statut", "")).strip()
            statut = statut if statut in STATUTS else "Non encore postulé"
            # Insérer l'agence dans SQLite (ignorée si le nom existe déjà)
            cur = con.execute(
                """INSERT OR IGNORE INTO agences
                   (nom,type,ville,taille,services,site,source,lat,lng,statut,notes)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    nom, str(r.get("Type", "")), str(r.get("Ville", "")), str(r.get("Taille", "")),
                    str(r.get("Services", "")), str(r.get("Site web", "")), str(r.get("Source", "")),
                    _num(r.get("Latitude")), _num(r.get("Longitude")), statut, str(r.get("Notes", "")),
                ),
            )
            # Compter si une nouvelle ligne a été ajoutée
            added += cur.rowcount
        # Valider l'enregistrement dans la base
        con.commit()
    return added


# ------------------------------------------------------------------------------
# Fonction : load_agences
# Rôle : Charger toutes les agences de la base SQLite sous forme de DataFrame Pandas.
# ------------------------------------------------------------------------------
def load_agences() -> pd.DataFrame:
    with _db() as con:
        # Sélectionner toutes les lignes triées par ordre alphabétique
        rows = con.execute("SELECT * FROM agences ORDER BY nom COLLATE NOCASE").fetchall()
    # Convertir en tableau Pandas
    return pd.DataFrame([dict(r) for r in rows])


# ------------------------------------------------------------------------------
# Fonction : set_statut
# Rôle : Mettre à jour le statut d'une agence (ex: 'Entretien', 'Accepté', 'Refusé')
#        avec la preuve de l'e-mail et la date de mise à jour.
# ------------------------------------------------------------------------------
def set_statut(agence_id: int, statut: str, preuve: str = "") -> None:
    # Vérifier que le statut fait partie de la liste autorisée
    if statut not in STATUTS:
        raise ValueError(f"Statut inconnu : {statut}")
    with _db() as con:
        # Exécuter la mise à jour SQL
        con.execute(
            "UPDATE agences SET statut=?, preuve=?, maj=? WHERE id=?",
            (statut, preuve, datetime.now().strftime("%Y-%m-%d %H:%M"), agence_id),
        )
        con.commit()


# ------------------------------------------------------------------------------
# Fonction : set_notes
# Rôle : Mettre à jour les notes personnelles saisies pour une agence.
# ------------------------------------------------------------------------------
def set_notes(agence_id: int, notes: str) -> None:
    with _db() as con:
        con.execute("UPDATE agences SET notes=? WHERE id=?", (notes, agence_id))
        con.commit()


# ------------------------------------------------------------------------------
# Fonction : add_agence
# Rôle : Ajouter manuellement une nouvelle agence depuis l'interface Streamlit.
# ------------------------------------------------------------------------------
def add_agence(nom, typ, ville, site, services="", taille="", lat=None, lng=None) -> bool:
    from .config import CITY_COORDS

    # Si les coordonnées GPS ne sont pas renseignées, utiliser le centre de la ville
    if lat is None or lng is None:
        lat, lng = CITY_COORDS.get(ville, (31.79, -7.09))
    with _db() as con:
        # Insérer la nouvelle agence dans SQLite
        cur = con.execute(
            """INSERT OR IGNORE INTO agences (nom,type,ville,taille,services,site,source,lat,lng)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (nom.strip(), typ, ville, taille, services, site.strip(), "Ajout manuel", lat, lng),
        )
        con.commit()
        # Retourner True si l'agence a été ajoutée, False si elle existait déjà
        return cur.rowcount > 0


# ==============================================================================
# Gestion des réglages (profil candidat, préférences)
# ==============================================================================

# ------------------------------------------------------------------------------
# Fonction : get_reglage
# Rôle : Lire la valeur d'un réglage à partir de sa clé (ex: 'profil_json').
# ------------------------------------------------------------------------------
def get_reglage(cle: str, defaut: str = "") -> str:
    with _db() as con:
        row = con.execute("SELECT valeur FROM reglages WHERE cle=?", (cle,)).fetchone()
    # Retourner la valeur trouvée ou la valeur par défaut
    return row["valeur"] if row else defaut


# ------------------------------------------------------------------------------
# Fonction : set_reglage
# Rôle : Sauvegarder ou mettre à jour un réglage dans la table 'reglages'.
# ------------------------------------------------------------------------------
def set_reglage(cle: str, valeur: str) -> None:
    with _db() as con:
        # Insérer ou remplacer si la clé existe déjà (UPSERT)
        con.execute(
            "INSERT INTO reglages(cle,valeur) VALUES(?,?) ON CONFLICT(cle) DO UPDATE SET valeur=excluded.valeur",
            (cle, valeur)
        )
        con.commit()
