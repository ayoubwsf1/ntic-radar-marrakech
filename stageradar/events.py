from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .classification import classify
from .config import RANK
from .database import load_agences, set_statut
from .mail_parser import Parsed
from .matching import match_agence


@dataclass
class Event:
    agence_id: int
    agence: str
    statut: str
    date: datetime
    sujet: str
    correspondant: str
    direction: str
    indice: str

    @property
    def preuve(self) -> str:
        arrow = "envoyé" if self.direction == "envoyé" else "reçu"
        return f"Mail {arrow} le {self.date.strftime('%d/%m/%Y')} — « {self.sujet[:70]} »"


def analyse_message(index: list[dict], p: Parsed, my_addr: str, classifier=classify) -> Optional[Event]:
    if my_addr in p.from_addrs:
        return None

    ag = match_agence(index, p, sent=False)
    if not ag:
        return None

    status, hint = classifier(p.subject, p.body)
    if not status:
        return None
    return Event(ag["id"], ag["nom"], status, p.date, p.subject, ", ".join(p.from_addrs)[:80], "reçu", hint)


def apply_events(events: list[Event]) -> list[Event]:
    df = load_agences()
    current = {int(r["id"]): r["statut"] for _, r in df.iterrows()}
    changes: list[Event] = []

    for ev in sorted(events, key=lambda e: e.date):
        cur = current.get(ev.agence_id, "Non encore postulé")
        if RANK[ev.statut] >= RANK[cur]:
            if ev.statut != cur:
                changes.append(ev)
            current[ev.agence_id] = ev.statut
            set_statut(ev.agence_id, ev.statut, ev.preuve)

    return changes
