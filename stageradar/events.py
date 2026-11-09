# ==============================================================================
# Fichier : events.py
# Rôle : Modéliser un événement détecté dans les e-mails (ex: un e-mail reçu
#        qui propose un entretien) et appliquer les mises à jour de statut dans la base.
# ==============================================================================

# Permet d'utiliser les annotations de type modernes
from __future__ import annotations

# Outil pour créer facilement des classes de données
from dataclasses import dataclass
# Module pour manipuler les dates
from datetime import datetime
# Type optionnel (valeur ou None)
from typing import Optional

# Importer la fonction de classification par mots-clés
from .classification import classify
# Importer les niveaux d'avancement des statuts (RANK)
from .config import RANK
# Importer les fonctions d'accès à la base de données
from .database import load_agences, set_statut
# Importer la structure d'un e-mail analysé
from .mail_parser import Parsed
# Importer la fonction qui associe l'e-mail à une agence
from .matching import match_agence


# ------------------------------------------------------------------------------
# Classe : Event
# Rôle : Représenter un événement lié à un e-mail trouvé.
# ------------------------------------------------------------------------------
@dataclass
class Event:
    agence_id: int            # Identifiant de l'agence concernée
    agence: str               # Nom de l'agence
    statut: str               # Nouveau statut détecté (Entretien, Accepté, Refusé)
    date: datetime            # Date et heure de l'e-mail
    sujet: str                # Objet de l'e-mail
    correspondant: str        # Adresse e-mail de l'expéditeur
    direction: str            # "reçu" ou "envoyé"
    indice: str               # La phrase ou le mot-clé qui a permis de décider

    # Propriété calculée : texte résumé utilisé comme preuve dans la base de données
    @property
    def preuve(self) -> str:
        arrow = "envoyé" if self.direction == "envoyé" else "reçu"
        return f"Mail {arrow} le {self.date.strftime('%d/%m/%Y')} — « {self.sujet[:70]} »"


# ------------------------------------------------------------------------------
# Fonction : analyse_message
# Rôle : Examiner un e-mail reçu pour voir s'il correspond à une agence
#        et s'il contient une réponse de recrutement.
# ------------------------------------------------------------------------------
def analyse_message(index: list[dict], p: Parsed, my_addr: str, classifier=classify) -> Optional[Event]:
    # 1. Ignorer l'e-mail s'il provient de notre propre adresse (expéditeur = nous-mêmes)
    if my_addr in p.from_addrs:
        return None

    # 2. Chercher à quelle agence appartient cet e-mail
    ag = match_agence(index, p, sent=False)
    if not ag:
        return None

    # 3. Classer le contenu du message pour trouver le statut
    status, hint = classifier(p.subject, p.body)
    if not status:
        return None

    # 4. Créer et retourner l'objet Event complet
    return Event(ag["id"], ag["nom"], status, p.date, p.subject, ", ".join(p.from_addrs)[:80], "reçu", hint)


# ------------------------------------------------------------------------------
# Fonction : apply_events
# Rôle : Appliquer les nouveaux statuts dans SQLite en respectant la règle d'or :
#        UN STATUT NE DOIT JAMAIS RÉTROGRADER (ex: 'Entretien' ne revient pas à 'Non postulé').
# ------------------------------------------------------------------------------
def apply_events(events: list[Event]) -> list[Event]:
    # Charger les agences actuelles
    df = load_agences()
    # Créer un dictionnaire : id_agence -> statut_actuel
    current = {int(r["id"]): r["statut"] for _, r in df.iterrows()}
    changes: list[Event] = []

    # Parcourir les événements triés par ordre chronologique (du plus ancien au plus récent)
    for ev in sorted(events, key=lambda e: e.date):
        cur = current.get(ev.agence_id, "Non encore postulé")
        # Vérifier que le nouveau statut a un rang supérieur ou égal au statut actuel
        if RANK[ev.statut] >= RANK[cur]:
            if ev.statut != cur:
                changes.append(ev)
            # Mettre à jour en mémoire et dans la base SQLite
            current[ev.agence_id] = ev.statut
            set_statut(ev.agence_id, ev.statut, ev.preuve)

    # Retourner la liste des changements réels appliqués
    return changes
