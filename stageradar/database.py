from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from .config import DB_PATH, STATUTS, XLSX_PATH


def _db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return closing(con)


def _num(v) -> Optional[float]:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def init_db() -> None:
    with _db() as con:
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
        con.execute("UPDATE agences SET statut='Non encore postulé' WHERE statut='Postulé'")
        con.execute("CREATE TABLE IF NOT EXISTS reglages (cle TEXT PRIMARY KEY, valeur TEXT)")
        con.commit()


def sync_from_excel(path: Path = XLSX_PATH) -> int:
    if not Path(path).exists():
        return 0
    df = pd.read_excel(path, sheet_name="Agences").fillna("")
    added = 0
    with _db() as con:
        for _, r in df.iterrows():
            nom = str(r.get("Nom", "")).strip()
            if not nom:
                continue
            statut = str(r.get("Statut", "")).strip()
            statut = statut if statut in STATUTS else "Non encore postulé"
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
            added += cur.rowcount
        con.commit()
    return added


def load_agences() -> pd.DataFrame:
    with _db() as con:
        rows = con.execute("SELECT * FROM agences ORDER BY nom COLLATE NOCASE").fetchall()
    return pd.DataFrame([dict(r) for r in rows])


def set_statut(agence_id: int, statut: str, preuve: str = "") -> None:
    if statut not in STATUTS:
        raise ValueError(f"Statut inconnu : {statut}")
    with _db() as con:
        con.execute(
            "UPDATE agences SET statut=?, preuve=?, maj=? WHERE id=?",
            (statut, preuve, datetime.now().strftime("%Y-%m-%d %H:%M"), agence_id),
        )
        con.commit()


def set_notes(agence_id: int, notes: str) -> None:
    with _db() as con:
        con.execute("UPDATE agences SET notes=? WHERE id=?", (notes, agence_id))
        con.commit()


def add_agence(nom, typ, ville, site, services="", taille="", lat=None, lng=None) -> bool:
    from .config import CITY_COORDS

    if lat is None or lng is None:
        lat, lng = CITY_COORDS.get(ville, (31.79, -7.09))
    with _db() as con:
        cur = con.execute(
            """INSERT OR IGNORE INTO agences (nom,type,ville,taille,services,site,source,lat,lng)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (nom.strip(), typ, ville, taille, services, site.strip(), "Ajout manuel", lat, lng),
        )
        con.commit()
        return cur.rowcount > 0


# --------------------------------------------------------------------------- réglages (profil, etc.)

def get_reglage(cle: str, defaut: str = "") -> str:
    with _db() as con:
        row = con.execute("SELECT valeur FROM reglages WHERE cle=?", (cle,)).fetchone()
    return row["valeur"] if row else defaut


def set_reglage(cle: str, valeur: str) -> None:
    with _db() as con:
        con.execute("INSERT INTO reglages(cle,valeur) VALUES(?,?) ON CONFLICT(cle) DO UPDATE SET valeur=excluded.valeur",
                    (cle, valeur))
        con.commit()
