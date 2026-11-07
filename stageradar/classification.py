from __future__ import annotations

import re
from typing import Optional

from .text_utils import norm


def _rx(patterns: list[str]) -> re.Pattern:
    return re.compile("|".join(patterns))


RX_REFUS = _rx([
    r"malheureusement", r"nous regrettons", r"\bregret", r"nous ne pouvons (?:donc )?pas",
    r"ne pouvons (?:donner|pas donner|poursuivre|retenir)", r"pas de suite", r"sans suite",
    r"pas (?:ete )?retenue?", r"ne sera pas retenue?", r"ne retenons pas", r"ne correspond pas",
    r"autres? candidat", r"autre profil", r"poste (?:est )?pourvu", r"candidature (?:a ete )?(?:declinee|refusee|rejetee)",
    r"unfortunately", r"we regret", r"not (?:been )?selected", r"not (?:be )?moving forward",
    r"will not be (?:moving|proceeding)", r"other candidates", r"position (?:has been|is) filled",
    r"not successful", r"decided not to",
])

RX_ACCEPT = _rx([
    r"felicitations", r"congratulations", r"nous avons le plaisir de (?:vous )?(?:annoncer|informer|confirmer|proposer)",
    r"(?:candidature|profil|dossier) (?:a ete |est )?(?:retenu|accepte)", r"accept(?:e|ons|er) votre candidature",
    r"convention de stage", r"pleased to (?:offer|inform|invite you to join)", r"happy to (?:offer|welcome)",
    r"welcome (?:aboard|to the team)", r"bienvenue (?:dans l'equipe|chez|parmi)", r"confirm(?:e|ons) votre stage",
    r"debut de (?:votre )?stage", r"offer letter", r"offre de stage.{0,40}(?:acceptee|confirm)",
])

RX_ENTRETIEN = _rx([
    r"entretien", r"interview", r"convoqu", r"convocation", r"test technique", r"disponibilit",
    r"visio(?:conference)?", r"rendez-vous", r"rencontrer", r"appel telephonique", r"call with",
])


_ORDRE = (
    ("Refusé", RX_REFUS),
    ("Accepté", RX_ACCEPT),
    ("Entretien", RX_ENTRETIEN),
)


def classify(subject: str, body: str) -> tuple[Optional[str], str]:
    text = norm(f"{subject}\n{body[:4000]}")
    for status, rx in _ORDRE:
        m = rx.search(text)
        if m:
            return status, m.group(0)
    return None, ""
