# ==============================================================================
# Fichier : classification.py
# Rôle : Analyser automatiquement les e-mails reçus pour déterminer le statut
#        de la candidature (Refusé, Accepté, Entretien) grâce à des mots-clés (Regex).
# ==============================================================================

# Permet d'utiliser les annotations de type modernes
from __future__ import annotations

# Module pour les expressions régulières (Regex)
import re
# Type optionnel (valeur ou None)
from typing import Optional

# Importer la fonction de normalisation de texte (sans accents, minuscules)
from .text_utils import norm


# ------------------------------------------------------------------------------
# Fonction interne : _rx
# Rôle : Combiner une liste de mots ou phrases en une seule expression régulière.
# ------------------------------------------------------------------------------
def _rx(patterns: list[str]) -> re.Pattern:
    return re.compile("|".join(patterns))


# Liste des expressions indiquant un REFUS (français et anglais)
RX_REFUS = _rx([
    # Français
    r"malheureusement", r"nous regrettons", r"\bregret", r"nous ne pouvons (?:donc )?pas",
    r"ne pouvons (?:donner|pas donner|poursuivre|retenir)", r"pas de suite", r"sans suite",
    r"pas (?:ete )?retenue?", r"ne sera pas retenue?", r"ne retenons pas", r"ne correspond pas",
    r"autres? candidat", r"autre profil", r"poste (?:est )?pourvu", r"candidature (?:a ete )?(?:declinee|refusee|rejetee)",
    # Anglais
    r"unfortunately", r"we regret", r"not (?:been )?selected", r"not (?:be )?moving forward",
    r"will not be (?:moving|proceeding)", r"other candidates", r"position (?:has been|is) filled",
    r"not successful", r"decided not to",
])

# Liste des expressions indiquant une ACCEPTATION ou offre de stage
RX_ACCEPT = _rx([
    # Français
    r"felicitations", r"congratulations", r"nous avons le plaisir de (?:vous )?(?:annoncer|informer|confirmer|proposer)",
    r"(?:candidature|profil|dossier) (?:a ete |est )?(?:retenu|accepte)", r"accept(?:e|ons|er) votre candidature",
    r"convention de stage", r"confirm(?:e|ons) votre stage", r"bienvenue (?:dans l'equipe|chez|parmi)",
    r"debut de (?:votre )?stage", r"offre de stage.{0,40}(?:acceptee|confirm)",
    # Anglais
    r"pleased to (?:offer|inform|invite you to join)", r"happy to (?:offer|welcome)",
    r"welcome (?:aboard|to the team)", r"offer letter",
])

# Liste des expressions indiquant une proposition d'ENTRETIEN ou test
RX_ENTRETIEN = _rx([
    r"entretien", r"interview", r"convoqu", r"convocation", r"test technique", r"disponibilit",
    r"visio(?:conference)?", r"rendez-vous", r"rencontrer", r"appel telephonique", r"call with",
])

# Ordre de vérification des statuts (on vérifie d'abord les refus, puis acceptation, puis entretien)
_ORDRE = (
    ("Refusé", RX_REFUS),
    ("Accepté", RX_ACCEPT),
    ("Entretien", RX_ENTRETIEN),
)


# ------------------------------------------------------------------------------
# Fonction : classify
# Rôle : Lire le sujet et le texte d'un e-mail pour deviner le statut.
# Retourne : (Statut détecté ou None, Extrait du texte qui a servi de preuve)
# ------------------------------------------------------------------------------
def classify(subject: str, body: str) -> tuple[Optional[str], str]:
    # 1. Normaliser l'objet et les 4000 premiers caractères du texte (minuscules, sans accents)
    text = norm(f"{subject}\n{body[:4000]}")

    # 2. Tester les expressions régulières dans l'ordre défini
    for status, rx in _ORDRE:
        m = rx.search(text)
        # Si une correspondance est trouvée, retourner le statut et la phrase correspondante
        if m:
            return status, m.group(0)

    # 3. Si aucun mot-clé n'a été détecté
    return None, ""
