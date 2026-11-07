"""Profil du candidat : stocké en base (table `reglages`) et utilisé par l'agent CV."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

from .. import database


@dataclass
class Profil:
    nom: str = ""
    email: str = ""
    telephone: str = ""
    liens: str = ""                       # LinkedIn, GitHub, portfolio… (séparés par des virgules)
    formation: str = ""                   # une formation par ligne
    competences: list = field(default_factory=list)
    experiences: str = ""                 # blocs séparés par une ligne vide : « Poste — Organisation (période) » puis une ligne par mission
    projets: str = ""                     # même principe : « Nom du projet » puis une ligne par réalisation
    interets: str = ""
    type_stage: str = "Stage"
    duree: str = ""
    langues: str = "Arabe, Français, Anglais"
    ville: str = "Marrakech"

    @property
    def vide(self) -> bool:
        return not (self.nom.strip() or self.competences or self.formation.strip() or self.experiences.strip())


def charger() -> Profil:
    try:
        d = json.loads(database.get_reglage("profil", "{}") or "{}")
    except json.JSONDecodeError:
        d = {}
    return Profil(**{k: v for k, v in d.items() if k in Profil.__dataclass_fields__})


def sauver(p: Profil) -> None:
    database.set_reglage("profil", json.dumps(asdict(p), ensure_ascii=False))


def parse_competences(texte: str) -> list[str]:
    return [c.strip() for c in texte.replace(";", ",").replace("\n", ",").split(",") if c.strip()]
