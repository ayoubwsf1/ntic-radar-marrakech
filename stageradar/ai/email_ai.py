# ==============================================================================
# Fichier : email_ai.py
# Rôle : Classification avancée des e-mails de recrutement en combinant deux approches :
#        1. Règles simples et rapides (mots-clés gratuits)
#        2. Intelligence Artificielle (LLM) en secours si les règles ne détectent rien
# ==============================================================================

# Permet d'utiliser les annotations de type modernes
from __future__ import annotations

# Module pour lire et écrire du JSON
import json
# Module pour les expressions régulières (Regex)
import re
# Type optionnel (valeur ou None)
from typing import Optional

# Importer le classificateur par mots-clés (gratuit et rapide)
from ..classification import classify
# Importer la liste officielle des statuts
from ..config import STATUTS
# Importer le client pour communiquer avec le modèle d'IA
from .llm import LLMClient, LLMError

# Instruction système envoyée à l'Intelligence Artificielle pour guider sa réponse
SYSTEM = (
    "Tu classes des e-mails reçus après une candidature de stage. Réponds UNIQUEMENT par un objet JSON "
    '{"statut": "Entretien" | "Accepté" | "Refusé" | "Aucun", "raison": "<10 mots max>"}. '
    "« Entretien » = invitation à un entretien, test ou rendez-vous ; « Accepté » = offre ou confirmation de stage ; "
    "« Refusé » = refus explicite ; « Aucun » = accusé de réception, newsletter ou message sans décision."
)


# ------------------------------------------------------------------------------
# Fonction : parse_reponse
# Rôle : Extraire le statut et la raison depuis la réponse JSON de l'IA.
#        L'IA peut parfois entourer son JSON avec du texte ou des backticks markdown.
# ------------------------------------------------------------------------------
def parse_reponse(texte: str) -> tuple[Optional[str], str]:
    # Chercher un objet JSON {...} dans le texte retourné par l'IA
    m = re.search(r"\{.*\}", texte or "", re.S)
    if not m:
        return None, ""
    try:
        # Décoder le JSON trouvé
        d = json.loads(m.group(0))
    except json.JSONDecodeError:
        # Si le JSON est mal formé, abandonner
        return None, ""
    # Récupérer le statut détecté
    statut = d.get("statut")
    # Vérifier que le statut est valide et différent de "Non encore postulé"
    if statut not in STATUTS or statut == "Non encore postulé":
        return None, str(d.get("raison", ""))[:80]
    # Retourner le statut et la raison (limitée à 80 caractères)
    return statut, str(d.get("raison", ""))[:80]


# ------------------------------------------------------------------------------
# Fonction : classifier_llm
# Rôle : Demander à l'Intelligence Artificielle de classifier l'e-mail.
# ------------------------------------------------------------------------------
def classifier_llm(sujet: str, corps: str, llm: LLMClient) -> tuple[Optional[str], str]:
    # Limiter le corps du message à 1500 caractères pour économiser les tokens et protéger la vie privée
    extrait = re.sub(r"\s+", " ", corps or "")[:1500]
    try:
        # Envoyer le sujet et le corps à l'IA avec l'instruction système
        rep = llm.complete(f"Objet : {sujet}\n\nMessage : {extrait}", SYSTEM, max_tokens=120, temperature=0)
    except LLMError:
        # Si l'API ne répond pas (problème réseau, quota épuisé...), abandonner
        return None, ""
    # Analyser la réponse JSON de l'IA
    statut, raison = parse_reponse(rep)
    # Retourner le statut et préfixer la raison avec "IA :" pour indiquer la source
    return statut, (f"IA : {raison}" if statut else "")


# ------------------------------------------------------------------------------
# Fonction principale : classifier_hybride
# Rôle : Stratégie intelligente en deux étapes pour maximiser l'efficacité :
#        1. Essayer d'abord les règles par mots-clés (rapide, gratuit, sans connexion)
#        2. Si les règles ne trouvent rien ET que l'IA est disponible, utiliser l'IA
# ------------------------------------------------------------------------------
def classifier_hybride(sujet: str, corps: str, llm: LLMClient | None = None) -> tuple[Optional[str], str]:
    # Étape 1 : Tenter la classification par règles simples (gratuit et instantané)
    statut, indice = classify(sujet, corps)
    # Si un statut a été trouvé OU que l'IA n'est pas disponible, s'arrêter ici
    if statut or not llm or not llm.available:
        return statut, indice
    # Étape 2 : Aucune règle n'a fonctionné, demander à l'IA en dernier recours
    return classifier_llm(sujet, corps, llm)
