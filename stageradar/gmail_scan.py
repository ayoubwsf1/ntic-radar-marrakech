from __future__ import annotations

import imaplib
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, Optional

import pandas as pd

from .classification import classify
from .events import analyse_message
from .mail_parser import parse_message
from .matching import build_index

_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


@dataclass
class ScanResult:
    events: list = field(default_factory=list)
    scanned: int = 0
    folder: str = ""
    gmail_search: bool = False


def connect(user: str, app_password: str, host: str = "imap.gmail.com") -> imaplib.IMAP4_SSL:
    M = imaplib.IMAP4_SSL(host, 993)
    M.login(user, app_password.replace(" ", ""))
    return M


def _imap_date(d: datetime) -> str:
    return f"{d.day:02d}-{_MONTHS[d.month - 1]}-{d.year}"


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


def _search_uids(M, days: int, domains: list[str], gmail: bool) -> list[bytes]:
    since = datetime.now() - timedelta(days=days)
    found: list[bytes] = []
    seen = set()

    def add(data):
        for u in (data[0] or b"").split():
            if u not in seen:
                seen.add(u)
                found.append(u)

    if gmail:
        after = since.strftime("%Y/%m/%d")
        queries = []
        for i in range(0, len(domains), 10):
            terms = " OR ".join(f"from:{d} OR to:{d}" for d in domains[i:i + 10])
            queries.append(f"after:{after} ({terms})")
        queries.append(f"after:{after} (candidature OR stage OR stagiaire OR internship OR application)")
        for q in queries:
            typ, data = M.uid("SEARCH", "X-GM-RAW", f'"{q}"')
            if typ == "OK":
                add(data)
    else:
        typ, data = M.uid("SEARCH", "SINCE", _imap_date(since))
        if typ == "OK":
            add(data)
    return found


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


def _folders_a_parcourir(folders: dict) -> list[str]:
    targets = [folders.get("\\All") or "INBOX"]
    if "\\Junk" in folders:
        targets.append(folders["\\Junk"])
    return targets


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
    say = progress or (lambda f, t: None)
    say(0.02, "Connexion à Gmail…")
    M = connection or connect(user, app_password)
    res = ScanResult()
    try:
        index = build_index(df)
        domains = sorted({a["domain"] for a in index if a["domain"]})
        folders = find_folders(M)
        gmail = "X-GM-EXT-1" in getattr(M, "capabilities", ())
        res.gmail_search = gmail

        targets = _folders_a_parcourir(folders)
        res.folder = " + ".join(targets)
        my_addr = user.lower().strip()

        for ti, folder in enumerate(targets):
            base, span = 0.08 + 0.87 * ti / len(targets), 0.87 / len(targets)
            say(base, f"Recherche dans « {folder} »…")
            typ, _ = M.select(f'"{folder}"', readonly=True)
            if typ != "OK":
                continue

            uids = _search_uids(M, days, domains, gmail)
            uids = uids[-max_msgs:] if len(uids) > max_msgs else uids
            total = len(uids)

            for i in range(0, total, 40):
                chunk = uids[i:i + 40]
                for header, text in _fetch_batch(M, chunk):
                    res.scanned += 1
                    try:
                        ev = analyse_message(index, parse_message(header, text), my_addr, classifier or classify)
                    except Exception:
                        ev = None
                    if ev:
                        res.events.append(ev)
                say(base + span * min(i + 40, total) / max(total, 1),
                    f"Analyse des messages… {min(i + 40, total)}/{total}")
    finally:
        try:
            M.logout()
        except Exception:
            pass
    say(1.0, "Terminé")
    return res
