"""Agent CV : transforme le profil du candidat en CV structuré, vérifié puis prêt à être exporté.

Étapes de l'agent (chacune est visible dans l'interface) :
  1. Analyse    — lecture du profil et, si choisie, de l'agence visée (type, services).
  2. Rédaction  — le LLM reformule et structure le CV en JSON ; sans clé API, un constructeur local
                  met en forme le profil tel quel.
  3. Vérification — garde-fou anti-invention : toute compétence, langue ou expérience absente du
                  profil est retirée du CV avant l'export.
  4. Export     — PDF et DOCX (voir `stageradar/cv_render.py`).
"""
from __future__ import annotations

import json
import re
from typing import Callable, Optional

from ..text_utils import norm
from .llm import LLMClient, LLMError
from .profile import Profil

SYSTEM = (
    "Tu es un expert en rédaction de CV pour le marché marocain. Tu structures et reformules le profil fourni "
    "en un CV clair, sobre et orienté résultats. Règle absolue : tu n'inventes AUCUNE expérience, formation, "
    "compétence, langue, date, chiffre ni employeur ; tu n'utilises que les éléments du profil. "
    "Tu peux reformuler, ordonner et mettre en valeur ce qui est pertinent pour la cible. "
    "Réponds UNIQUEMENT par un objet JSON valide, sans commentaire ni balises."
)

_SCHEMA = (
    '{"titre": "intitulé du poste visé", "resume": "2 à 3 phrases", '
    '"formation": [{"intitule": "", "details": ""}], '
    '"experiences": [{"poste": "", "organisation": "", "periode": "", "points": [""]}], '
    '"projets": [{"nom": "", "points": [""]}], '
    '"competences": [""], "langues": [""], "interets": ""}'
)

_LANGUES = {"Français": "français", "English": "anglais"}

Etape = Callable[[str], None]


# --------------------------------------------------------------------------- utilitaires

def _lignes(texte: str) -> list[str]:
    return [l.strip(" -•\t") for l in (texte or "").splitlines() if l.strip(" -•\t")]


def _blocs(texte: str) -> list[list[str]]:
    """Découpe un texte en blocs séparés par une ligne vide ; chaque bloc = liste de lignes nettoyées."""
    blocs = [_lignes(b) for b in re.split(r"\n\s*\n", (texte or "").strip())]
    return [b for b in blocs if b]


def _separer_poste(entete: str) -> tuple[str, str, str]:
    """« Stagiaire web — Acme (juin 2025) » -> (poste, organisation, période)."""
    periode = ""
    m = re.search(r"\(([^)]*)\)\s*$", entete)
    if m:
        periode, entete = m.group(1).strip(), entete[:m.start()].strip()
    parts = re.split(r"\s+[—–-]\s+|\s*\|\s*|\s+chez\s+|\s+at\s+", entete, maxsplit=1)
    return parts[0].strip(), (parts[1].strip() if len(parts) > 1 else ""), periode


def _liste(texte: str) -> list[str]:
    return [x.strip() for x in re.split(r"[,;\n]", texte or "") if x.strip()]


def profil_en_texte(p: Profil) -> str:
    return (
        f"Nom : {p.nom}\nVille : {p.ville}\nType de candidature : {p.type_stage}"
        f"{(' · durée : ' + p.duree) if p.duree else ''}\n"
        f"Formation :\n{p.formation}\nCompétences : {', '.join(p.competences)}\n"
        f"Expériences :\n{p.experiences or '(aucune)'}\nProjets :\n{p.projets or '(aucun)'}\n"
        f"Langues : {p.langues}\nCentres d'intérêt : {p.interets}"
    )


# --------------------------------------------------------------------------- CV local (sans LLM)

def cv_local(p: Profil, cible: dict | None = None) -> dict:
    """Met en forme le profil tel quel, sans reformulation."""
    experiences = []
    for bloc in _blocs(p.experiences):
        poste, orga, periode = _separer_poste(bloc[0])
        experiences.append({"poste": poste, "organisation": orga, "periode": periode, "points": bloc[1:]})
    projets = [{"nom": b[0], "points": b[1:]} for b in _blocs(p.projets)]
    domaine = f" — {cible['type']}" if cible and cible.get("type") else ""
    return {
        "titre": f"{p.type_stage}{domaine}".strip(),
        "resume": "",
        "formation": [{"intitule": l, "details": ""} for l in _lignes(p.formation)],
        "experiences": experiences,
        "projets": projets,
        "competences": list(p.competences),
        "langues": _liste(p.langues),
        "interets": p.interets,
    }


# --------------------------------------------------------------------------- LLM

def _prompt(p: Profil, cible: dict | None, langue: str) -> str:
    cible_txt = ""
    if cible:
        cible_txt = (f"\nCible : agence « {cible.get('nom', '')} » ({cible.get('type', '')}, {cible.get('ville', '')}). "
                     f"Services : {str(cible.get('services', ''))[:250]}. Mets en avant les éléments du profil les plus pertinents pour elle.")
    return (
        f"Rédige le CV en {_LANGUES.get(langue, 'français')} au format JSON suivant :\n{_SCHEMA}\n\n"
        f"Consignes : résumé de 2 à 3 phrases ; 2 à 4 points courts par expérience ou projet, verbes d'action, "
        f"sans chiffre inventé ; ne garde que des compétences, langues et expériences présentes dans le profil, en recopiant les noms des compétences exactement comme dans le profil ; "
        f"si une section n'a pas de matière, renvoie une liste vide.{cible_txt}\n\nPROFIL :\n{profil_en_texte(p)}"
    )


def parse_cv_json(texte: str) -> Optional[dict]:
    """Extrait l'objet JSON même s'il est entouré de texte ou de ```json."""
    m = re.search(r"\{.*\}", texte or "", re.S)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    return d if isinstance(d, dict) else None


# --------------------------------------------------------------------------- vérification anti-invention

def verifier(cv: dict, p: Profil) -> tuple[dict, list[str]]:
    """Retire du CV ce qui n'est pas dans le profil. Retourne (cv corrigé, avertissements)."""
    alertes: list[str] = []
    out = {k: cv.get(k) for k in ("titre", "resume", "formation", "experiences", "projets", "competences", "langues", "interets")}

    autorises = {norm(c) for c in p.competences}
    gardees = [c for c in (out["competences"] or []) if norm(str(c)) in autorises]
    retirees = [c for c in (out["competences"] or []) if norm(str(c)) not in autorises]
    if retirees:
        alertes.append(f"Compétences non présentes dans le profil, retirées : {', '.join(map(str, retirees))}")
    out["competences"] = gardees or list(p.competences)

    langues_profil = _liste(p.langues)
    if len(out["langues"] or []) > len(langues_profil):
        alertes.append("Langues en trop retirées.")
        out["langues"] = out["langues"][:len(langues_profil)]
    out["langues"] = out["langues"] or langues_profil

    n_exp, n_proj = len(_blocs(p.experiences)), len(_blocs(p.projets))
    if len(out["experiences"] or []) > n_exp:
        alertes.append(f"{len(out['experiences']) - n_exp} expérience(s) inventée(s) retirée(s).")
        out["experiences"] = out["experiences"][:n_exp]
    if len(out["projets"] or []) > n_proj:
        alertes.append(f"{len(out['projets']) - n_proj} projet(s) inventé(s) retiré(s).")
        out["projets"] = out["projets"][:n_proj]
    n_form = len(_lignes(p.formation))
    if len(out["formation"] or []) > n_form:
        alertes.append("Formation(s) non présente(s) dans le profil retirée(s).")
        out["formation"] = out["formation"][:n_form]

    for k in ("formation", "experiences", "projets"):
        out[k] = [x for x in (out[k] or []) if isinstance(x, dict)]
    for k in ("titre", "resume", "interets"):
        out[k] = str(out[k] or "").strip()
    return out, alertes


# --------------------------------------------------------------------------- agent

def generer_cv(p: Profil, cible: dict | None = None, langue: str = "Français",
               llm: LLMClient | None = None, etape: Etape | None = None) -> dict:
    """Exécute l'agent. Retourne {cv, origine, alertes}. `etape(texte)` reçoit l'avancement."""
    say = etape or (lambda t: None)
    say("1/4 · Analyse du profil" + (f" et de l'agence « {cible.get('nom')} »" if cible else ""))

    cv, origine, alertes = None, "local", []
    if llm and llm.available:
        say("2/4 · Rédaction du CV par l'IA")
        try:
            cv = parse_cv_json(llm.complete(_prompt(p, cible, langue), SYSTEM, max_tokens=1800, temperature=0.3))
            if cv is None:
                alertes.append("Réponse de l'IA illisible : CV construit localement.")
            else:
                origine = "IA"
        except LLMError as e:
            alertes.append(f"IA indisponible ({str(e)[:80]}) : CV construit localement.")
    else:
        say("2/4 · Mise en forme locale (aucune clé API : pas de reformulation)")
    if cv is None:
        cv = cv_local(p, cible)

    say("3/4 · Vérification : aucun élément inventé")
    cv, a = verifier(cv, p)
    cv.update({"nom": p.nom, "email": p.email, "telephone": p.telephone, "ville": p.ville, "liens": _liste(p.liens), "langue": langue})
    say("4/4 · CV prêt à télécharger")
    return {"cv": cv, "origine": origine, "alertes": alertes + a}
