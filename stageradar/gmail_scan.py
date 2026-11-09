# ==============================================================================
# Fichier : gmail_scan.py
# Rôle : Connexion sécurisée au compte Gmail via le protocole IMAP (SSL port 993)
#        en lecture seule (BODY.PEEK) pour chercher automatiquement les réponses de stage.
# ==============================================================================

# Permet d'utiliser les annotations de type modernes
from __future__ import annotations

# Module standard Python pour interagir avec un serveur de messagerie IMAP
import imaplib
# Module pour les expressions régulières (Regex)
import re
# Outils dataclass pour structurer les données
from dataclasses import dataclass, field
# Outils pour manipuler les dates et calculer des écarts de jours (timedelta)
from datetime import datetime, timedelta
# Outils de typage (fonction de rappel pour la barre de progression)
from typing import Callable, Optional

# Bibliothèque Pandas pour manipuler le tableau des agences
import pandas as pd

# Importer le classificateur de texte par mots-clés
from .classification import classify
# Importer la fonction d'analyse d'un message
from .events import analyse_message
# Importer le parseur d'e-mails bruts
from .mail_parser import parse_message
# Importer la fonction qui construit l'index des agences
from .matching import build_index

# Noms abrégés des mois pour le protocole standard IMAP
_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


# ------------------------------------------------------------------------------
# Classe : ScanResult
# Rôle : Contenir le bilan complet du scan (liste des événements trouvés, nombre d'e-mails lus).
# ------------------------------------------------------------------------------
@dataclass
class ScanResult:
    events: list = field(default_factory=list)  # Liste des réponses détectées (objets Event)
    scanned: int = 0                            # Nombre total de messages analysés
    folder: str = ""                            # Noms des dossiers explorés (ex: "[Gmail]/Tous les messages")
    gmail_search: bool = False                  # Vrai si la recherche avancée Gmail a été utilisée


# ------------------------------------------------------------------------------
# Fonction : connect
# Rôle : Se connecter à la boîte Gmail de façon sécurisée avec un mot de passe d'application.
# ------------------------------------------------------------------------------
def connect(user: str, app_password: str, host: str = "imap.gmail.com") -> imaplib.IMAP4_SSL:
    # Connexion sécurisée chiffrée SSL sur le port 993
    M = imaplib.IMAP4_SSL(host, 993)
    # Connexion avec l'adresse e-mail et le mot de passe d'application (sans espaces)
    M.login(user, app_password.replace(" ", ""))
    return M


# ------------------------------------------------------------------------------
# Fonction interne : _imap_date
# Rôle : Formater une date au format requis par IMAP (ex: "01-Jan-2026").
# ------------------------------------------------------------------------------
def _imap_date(d: datetime) -> str:
    return f"{d.day:02d}-{_MONTHS[d.month - 1]}-{d.year}"


# ------------------------------------------------------------------------------
# Fonction : find_folders
# Rôle : Détecter automatiquement le nom des dossiers spéciaux Gmail (Tous les messages, Spam, etc.).
# ------------------------------------------------------------------------------
def find_folders(M) -> dict:
    out = {}
    typ, data = M.list()
    if typ != "OK":
        return out
    for raw in data or []:
        line = raw.decode("utf-8", "ignore") if isinstance(raw, bytes) else str(raw)
        m = re.match(r'\((?P<flags>[^)]*)\)\s+"?(?P<delim>[^"\s]+)"?\s+(?P<n>.+)$', line)
        if not m:
            continue
        name = m.group("n").strip().strip('"')
        for flag in ("\\All", "\\Sent", "\\Junk"):
            if flag.lower() in m.group("flags").lower():
                out[flag] = name
    return out


# ------------------------------------------------------------------------------
# Fonction interne : _search_uids
# Rôle : Trouver les identifiants uniques (UIDs) des e-mails pertinents récents.
# ------------------------------------------------------------------------------
def _search_uids(M, days: int, domains: list[str], gmail: bool) -> list[bytes]:
    # Date limite de recherche (ex: les 90 derniers jours)
    since = datetime.now() - timedelta(days=days)
    found: list[bytes] = []
    seen = set()

    # Fonction locale pour ajouter un UID sans doublon
    def add(data):
        for u in (data[0] or b"").split():
            if u not in seen:
                seen.add(u)
                found.append(u)

    # Si le serveur supporte le moteur de recherche rapide de Gmail (X-GM-RAW)
    if gmail:
        after = since.strftime("%Y/%m/%d")
        queries = []
        # Chercher par paquets de 10 noms de domaines d'agences
        for i in range(0, len(domains), 10):
            terms = " OR ".join(f"from:{d} OR to:{d}" for d in domains[i:i + 10])
            queries.append(f"after:{after} ({terms})")
        # Chercher aussi les mots-clés liés au recrutement et aux stages
        queries.append(f"after:{after} (candidature OR stage OR stagiaire OR internship OR application)")
        for q in queries:
            typ, data = M.uid("SEARCH", "X-GM-RAW", f'"{q}"')
            if typ == "OK":
                add(data)
    else:
        # Recherche IMAP classique par date
        typ, data = M.uid("SEARCH", "SINCE", _imap_date(since))
        if typ == "OK":
            add(data)
    return found


# ------------------------------------------------------------------------------
# Fonction interne : _fetch_batch
# Rôle : Télécharger un paquet d'e-mails en lecture seule (BODY.PEEK)
#        afin de ne JAMAIS marquer les e-mails comme 'lus' dans la boîte Gmail.
# ------------------------------------------------------------------------------
def _fetch_batch(M, uids: list[bytes]) -> list[tuple[bytes, bytes]]:
    typ, data = M.uid(
        "FETCH", b",".join(uids).decode(),
        "(BODY.PEEK[HEADER.FIELDS (FROM TO CC SUBJECT DATE CONTENT-TYPE CONTENT-TRANSFER-ENCODING MIME-VERSION)] "
        "BODY.PEEK[TEXT]<0.6000>)",
    )
    if typ != "OK":
        return []
    msgs: list[dict] = []
    for item in data or []:
        if not isinstance(item, tuple):
            continue
        desc = item[0].decode("utf-8", "ignore").upper()
        if "BODY[TEXT" in desc:
            if msgs:
                msgs[-1]["text"] = item[1]
        elif "BODY[HEADER" in desc:
            msgs.append({"header": item[1], "text": b""})
    return [(m["header"], m["text"]) for m in msgs]


# ------------------------------------------------------------------------------
# Fonction interne : _folders_a_parcourir
# Rôle : Déterminer la liste des dossiers à scanner (Tous les messages + Spam/Junk).
# ------------------------------------------------------------------------------
def _folders_a_parcourir(folders: dict) -> list[str]:
    targets = [folders.get("\\All") or "INBOX"]
    if "\\Junk" in folders:
        targets.append(folders["\\Junk"])
    return targets


# ------------------------------------------------------------------------------
# Fonction principale : scan_mailbox
# Rôle : Orchestrer tout le scan : connexion, recherche des e-mails récents,
#        analyse du texte, association avec les agences et retour des résultats.
# ------------------------------------------------------------------------------
def scan_mailbox(
    user: str,
    app_password: str,
    df: pd.DataFrame,
    days: int = 90,
    max_msgs: int = 400,
    progress: Optional[Callable[[float, str], None]] = None,
    connection=None,
    classifier=None,
) -> ScanResult:
    # Gestionnaire de message de progression pour l'interface graphique Streamlit
    say = progress or (lambda f, t: None)
    say(0.02, "Connexion à Gmail…")

    # Établir la connexion sécurisée
    M = connection or connect(user, app_password)
    res = ScanResult()
    try:
        # 1. Préparer l'index des agences et leurs domaines web
        index = build_index(df)
        domains = sorted({a["domain"] for a in index if a["domain"]})
        folders = find_folders(M)
        gmail = "X-GM-EXT-1" in getattr(M, "capabilities", ())
        res.gmail_search = gmail

        # 2. Choisir les dossiers à scanner
        targets = _folders_a_parcourir(folders)
        res.folder = " + ".join(targets)
        my_addr = user.lower().strip()

        # 3. Scanner chaque dossier sélectionné
        for ti, folder in enumerate(targets):
            base, span = 0.08 + 0.87 * ti / len(targets), 0.87 / len(targets)
            say(base, f"Recherche dans « {folder} »…")
            # Ouvrir le dossier en lecture seule stricte
            typ, _ = M.select(f'"{folder}"', readonly=True)
            if typ != "OK":
                continue

            # Trouver les UIDs des e-mails
            uids = _search_uids(M, days, domains, gmail)
            uids = uids[-max_msgs:] if len(uids) > max_msgs else uids
            total = len(uids)

            # Traiter les e-mails par paquets de 40 pour la rapidité
            for i in range(0, total, 40):
                chunk = uids[i:i + 40]
                for header, text in _fetch_batch(M, chunk):
                    res.scanned += 1
                    try:
                        # Analyser le message et vérifier s'il s'agit d'une réponse de stage
                        ev = analyse_message(index, parse_message(header, text), my_addr, classifier or classify)
                    except Exception:
                        ev = None
                    if ev:
                        res.events.append(ev)
                # Mettre à jour la barre de progression
                say(base + span * min(i + 40, total) / max(total, 1),
                    f"Analyse des messages… {min(i + 40, total)}/{total}")
    finally:
        # Toujours se déconnecter proprement à la fin
        try:
            M.logout()
        except Exception:
            pass
    say(1.0, "Terminé")
    return res
