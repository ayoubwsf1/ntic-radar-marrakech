"""Classification des e-mails de recrutement : règles d'abord, LLM ensuite (optionnel)."""
from __future__ import annotations

import json
import re
from typing import Optional

from ..classification import classify
from ..config import STATUTS
from .llm import LLMClient, LLMError

SYSTEM = (
    "Tu classes des e-mails reçus après une candidature de stage. Réponds UNIQUEMENT par un objet JSON "
    '{"statut": "Entretien" | "Accepté" | "Refusé" | "Aucun", "raison": "<10 mots max>"}. '
    "« Entretien » = invitation à un entretien, test ou rendez-vous ; « Accepté » = offre ou confirmation de stage ; "
    "« Refusé » = refus explicite ; « Aucun » = accusé de réception, newsletter ou message sans décision."
)


def parse_reponse(texte: str) -> tuple[Optional[str], str]:
    """Extrait (statut, raison) d'une réponse JSON, même entourée de texte ou de ```json."""
    m = re.search(r"\{.*\}", texte or "", re.S)
    if not m:
        return None, ""
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None, ""
    statut = d.get("statut")
    if statut not in STATUTS or statut == "Non encore postulé":
        return None, str(d.get("raison", ""))[:80]
    return statut, str(d.get("raison", ""))[:80]


def classifier_llm(sujet: str, corps: str, llm: LLMClient) -> tuple[Optional[str], str]:
    extrait = re.sub(r"\s+", " ", corps or "")[:1500]  # on limite ce qui quitte la machine
    try:
        rep = llm.complete(f"Objet : {sujet}\n\nMessage : {extrait}", SYSTEM, max_tokens=120, temperature=0)
    except LLMError:
        return None, ""
    statut, raison = parse_reponse(rep)
    return statut, (f"IA : {raison}" if statut else "")


def classifier_hybride(sujet: str, corps: str, llm: LLMClient | None = None) -> tuple[Optional[str], str]:
    """Règles (rapides, gratuites) puis LLM seulement si les règles ne détectent rien."""
    statut, indice = classify(sujet, corps)
    if statut or not llm or not llm.available:
        return statut, indice
    return classifier_llm(sujet, corps, llm)
