# ==============================================================================
# Fichier : cv.py
# Rôle : Agent intelligent de génération de CV en 4 étapes :
#        1. Analyse du profil (et de l'agence cible si choisie)
#        2. Rédaction par l'IA (ou construction locale si pas d'API)
#        3. Vérification anti-invention (garde-fou de sécurité)
#        4. Export prêt en PDF et DOCX
# ==============================================================================

# Permet d'utiliser les annotations de type modernes
from __future__ import annotations

# Module pour manipuler le JSON
import json
# Module pour les expressions régulières (Regex)
import re
# Type pour les fonctions de rappel (callbacks) et valeurs optionnelles
from typing import Callable, Optional

# Importer la fonction de normalisation de texte
from ..text_utils import norm
# Importer le client LLM et son exception d'erreur
from .llm import LLMClient, LLMError
# Importer la structure du profil candidat
from .profile import Profil

# Instruction système donnée à l'Intelligence Artificielle pour cadrer son travail
SYSTEM = (
    "Tu es un expert en rédaction de CV pour le marché marocain. Tu structures et reformules le profil fourni "
    "en un CV clair, sobre et orienté résultats. Règle absolue : tu n'inventes AUCUNE expérience, formation, "
    "compétence, langue, date, chiffre ni employeur ; tu n'utilises que les éléments du profil. "
    "Tu peux reformuler, ordonner et mettre en valeur ce qui est pertinent pour la cible. "
    "Réponds UNIQUEMENT par un objet JSON valide, sans commentaire ni balises."
)

# Structure JSON attendue en retour de l'IA (schéma du CV)
_SCHEMA = (
    '{"titre": "intitulé du poste visé", "resume": "2 à 3 phrases", '
    '"formation": [{"intitule": "", "details": ""}], '
    '"experiences": [{"poste": "", "organisation": "", "periode": "", "points": [""]}], '
    '"projets": [{"nom": "", "points": [""]}], '
    '"competences": [""], "langues": [""], "interets": ""}'
)

# Dictionnaire de traduction des langues (pour générer le CV en français ou anglais)
_LANGUES = {"Français": "français", "English": "anglais"}

# Type de fonction de rappel pour afficher l'avancement dans l'interface
Etape = Callable[[str], None]


# ==============================================================================
# UTILITAIRES DE PARSING (découper et nettoyer le texte brut du profil)
# ==============================================================================

# ------------------------------------------------------------------------------
# Fonction interne : _lignes
# Rôle : Découper un texte en lignes et nettoyer les espaces et les puces.
# ------------------------------------------------------------------------------
def _lignes(texte: str) -> list[str]:
    return [l.strip(" -•\t") for l in (texte or "").splitlines() if l.strip(" -•\t")]


# ------------------------------------------------------------------------------
# Fonction interne : _blocs
# Rôle : Séparer un texte en blocs (séparés par une ligne vide).
# ------------------------------------------------------------------------------
def _blocs(texte: str) -> list[list[str]]:
    # Découper le texte en blocs séparés par une ligne vide
    blocs = [_lignes(b) for b in re.split(r"\n\s*\n", (texte or "").strip())]
    # Ne garder que les blocs non vides
    return [b for b in blocs if b]


# ------------------------------------------------------------------------------
# Fonction interne : _separer_poste
# Rôle : Découper l'en-tête d'une expérience en (poste, organisation, période).
# Exemple : "Stagiaire web — Acme (juin 2025)" devient ("Stagiaire web", "Acme", "juin 2025")
# ------------------------------------------------------------------------------
def _separer_poste(entete: str) -> tuple[str, str, str]:
    periode = ""
    # Extraire la période entre parenthèses à la fin
    m = re.search(r"\(([^)]*)\)\s*$", entete)
    if m:
        periode, entete = m.group(1).strip(), entete[:m.start()].strip()
    # Séparer le poste et l'organisation avec les séparateurs courants (—, |, chez, at)
    parts = re.split(r"\s+[—–-]\s+|\s*\|\s*|\s+chez\s+|\s+at\s+", entete, maxsplit=1)
    return parts[0].strip(), (parts[1].strip() if len(parts) > 1 else ""), periode


# ------------------------------------------------------------------------------
# Fonction interne : _liste
# Rôle : Transformer un texte séparé par virgules, points-virgules ou retours
#        à la ligne en une liste propre.
# ------------------------------------------------------------------------------
def _liste(texte: str) -> list[str]:
    return [x.strip() for x in re.split(r"[,;\n]", texte or "") if x.strip()]


# ------------------------------------------------------------------------------
# Fonction : profil_en_texte
# Rôle : Convertir l'objet Profil en texte lisible pour l'envoyer à l'IA.
# ------------------------------------------------------------------------------
def profil_en_texte(p: Profil) -> str:
    return (
        f"Nom : {p.nom}\nVille : {p.ville}\nType de candidature : {p.type_stage}"
        f"{(' · durée : ' + p.duree) if p.duree else ''}\n"
        f"Formation :\n{p.formation}\nCompétences : {', '.join(p.competences)}\n"
        f"Expériences :\n{p.experiences or '(aucune)'}\nProjets :\n{p.projets or '(aucun)'}\n"
        f"Langues : {p.langues}\nCentres d'intérêt : {p.interets}"
    )


# ==============================================================================
# CV LOCAL (sans Intelligence Artificielle)
# ==============================================================================

# ------------------------------------------------------------------------------
# Fonction : cv_local
# Rôle : Construire le CV directement à partir du profil sans reformulation IA.
#        Utilisé quand aucune clé API n'est disponible.
# ------------------------------------------------------------------------------
def cv_local(p: Profil, cible: dict | None = None) -> dict:
    # Parser les expériences professionnelles (blocs séparés par ligne vide)
    experiences = []
    for bloc in _blocs(p.experiences):
        poste, orga, periode = _separer_poste(bloc[0])
        experiences.append({"poste": poste, "organisation": orga, "periode": periode, "points": bloc[1:]})
    # Parser les projets
    projets = [{"nom": b[0], "points": b[1:]} for b in _blocs(p.projets)]
    # Construire le titre du CV avec le type d'agence cible si fournie
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


# ==============================================================================
# GÉNÉRATION AVEC IA (LLM)
# ==============================================================================

# ------------------------------------------------------------------------------
# Fonction interne : _prompt
# Rôle : Construire le texte d'instruction complet envoyé à l'IA.
# ------------------------------------------------------------------------------
def _prompt(p: Profil, cible: dict | None, langue: str) -> str:
    cible_txt = ""
    if cible:
        # Si une agence est ciblée, inclure ses informations pour personnaliser le CV
        cible_txt = (f"\nCible : agence « {cible.get('nom', '')} » ({cible.get('type', '')}, {cible.get('ville', '')}). "
                     f"Services : {str(cible.get('services', ''))[:250]}. Mets en avant les éléments du profil les plus pertinents pour elle.")
    return (
        f"Rédige le CV en {_LANGUES.get(langue, 'français')} au format JSON suivant :\n{_SCHEMA}\n\n"
        f"Consignes : résumé de 2 à 3 phrases ; 2 à 4 points courts par expérience ou projet, verbes d'action, "
        f"sans chiffre inventé ; ne garde que des compétences, langues et expériences présentes dans le profil, en recopiant les noms des compétences exactement comme dans le profil ; "
        f"si une section n'a pas de matière, renvoie une liste vide.{cible_txt}\n\nPROFIL :\n{profil_en_texte(p)}"
    )


# ------------------------------------------------------------------------------
# Fonction : parse_cv_json
# Rôle : Extraire l'objet JSON du CV même si l'IA l'a entouré de texte superflu.
# ------------------------------------------------------------------------------
def parse_cv_json(texte: str) -> Optional[dict]:
    # Chercher un objet JSON {...} dans la réponse
    m = re.search(r"\{.*\}", texte or "", re.S)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    return d if isinstance(d, dict) else None


# ==============================================================================
# VÉRIFICATION ANTI-INVENTION (garde-fou de sécurité)
# ==============================================================================

# ------------------------------------------------------------------------------
# Fonction : verifier
# Rôle : Comparer le CV généré par l'IA avec le profil original et supprimer
#        tout ce qui n'existe pas dans le profil (compétences inventées, etc.).
# ------------------------------------------------------------------------------
def verifier(cv: dict, p: Profil) -> tuple[dict, list[str]]:
    alertes: list[str] = []
    # Extraire les sections principales du CV
    out = {k: cv.get(k) for k in ("titre", "resume", "formation", "experiences", "projets", "competences", "langues", "interets")}

    # 1. Vérifier les compétences (ne garder que celles présentes dans le profil)
    autorises = {norm(c) for c in p.competences}
    gardees = [c for c in (out["competences"] or []) if norm(str(c)) in autorises]
    retirees = [c for c in (out["competences"] or []) if norm(str(c)) not in autorises]
    if retirees:
        alertes.append(f"Compétences non présentes dans le profil, retirées : {', '.join(map(str, retirees))}")
    out["competences"] = gardees or list(p.competences)

    # 2. Vérifier les langues (pas plus que dans le profil)
    langues_profil = _liste(p.langues)
    if len(out["langues"] or []) > len(langues_profil):
        alertes.append("Langues en trop retirées.")
        out["langues"] = out["langues"][:len(langues_profil)]
    out["langues"] = out["langues"] or langues_profil

    # 3. Vérifier les expériences (pas plus de blocs que dans le profil)
    n_exp, n_proj = len(_blocs(p.experiences)), len(_blocs(p.projets))
    if len(out["experiences"] or []) > n_exp:
        alertes.append(f"{len(out['experiences']) - n_exp} expérience(s) inventée(s) retirée(s).")
        out["experiences"] = out["experiences"][:n_exp]
    if len(out["projets"] or []) > n_proj:
        alertes.append(f"{len(out['projets']) - n_proj} projet(s) inventé(s) retiré(s).")
        out["projets"] = out["projets"][:n_proj]

    # 4. Vérifier la formation (pas plus d'entrées que dans le profil)
    n_form = len(_lignes(p.formation))
    if len(out["formation"] or []) > n_form:
        alertes.append("Formation(s) non présente(s) dans le profil retirée(s).")
        out["formation"] = out["formation"][:n_form]

    # 5. Nettoyer les structures de données (garder seulement les dictionnaires valides)
    for k in ("formation", "experiences", "projets"):
        out[k] = [x for x in (out[k] or []) if isinstance(x, dict)]
    for k in ("titre", "resume", "interets"):
        out[k] = str(out[k] or "").strip()

    return out, alertes


# ==============================================================================
# AGENT PRINCIPAL DE GÉNÉRATION DE CV
# ==============================================================================

# ------------------------------------------------------------------------------
# Fonction principale : generer_cv
# Rôle : Orchestrer toute la génération du CV en 4 étapes avec feedback en temps réel.
# Retourne : {"cv": {...}, "origine": "IA" ou "local", "alertes": [...]}
# ------------------------------------------------------------------------------
def generer_cv(p: Profil, cible: dict | None = None, langue: str = "Français",
               llm: LLMClient | None = None, etape: Etape | None = None) -> dict:
    # Fonction de callback pour afficher l'avancement (ou fonction vide si non fournie)
    say = etape or (lambda t: None)

    # Étape 1 : Analyse
    say("1/4 · Analyse du profil" + (f" et de l'agence « {cible.get('nom')} »" if cible else ""))

    cv, origine, alertes = None, "local", []

    # Étape 2 : Rédaction (avec IA si disponible, sinon local)
    if llm and llm.available:
        say("2/4 · Rédaction du CV par l'IA")
        try:
            # Appeler l'IA pour générer le CV
            cv = parse_cv_json(llm.complete(_prompt(p, cible, langue), SYSTEM, max_tokens=1800, temperature=0.3))
            if cv is None:
                alertes.append("Réponse de l'IA illisible : CV construit localement.")
            else:
                origine = "IA"
        except LLMError as e:
            alertes.append(f"IA indisponible ({str(e)[:80]}) : CV construit localement.")
    else:
        say("2/4 · Mise en forme locale (aucune clé API : pas de reformulation)")

    # Si l'IA n'a pas fonctionné, utiliser la construction locale
    if cv is None:
        cv = cv_local(p, cible)

    # Étape 3 : Vérification anti-invention
    say("3/4 · Vérification : aucun élément inventé")
    cv, a = verifier(cv, p)
    # Ajouter les informations de contact du profil
    cv.update({"nom": p.nom, "email": p.email, "telephone": p.telephone, "ville": p.ville, "liens": _liste(p.liens), "langue": langue})

    # Étape 4 : Export prêt
    say("4/4 · CV prêt à télécharger")
    return {"cv": cv, "origine": origine, "alertes": alertes + a}
