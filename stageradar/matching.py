# ==============================================================================
# Fichier : matching.py
# Rôle : Associer un e-mail reçu à une agence de notre base de données.
#        L'association se fait soit par le nom de domaine de l'e-mail (ex: @web-marrakech.com),
#        soit par la recherche du nom de l'agence dans l'objet ou le texte de l'e-mail.
# ==============================================================================

# Permet d'utiliser les annotations de type modernes
from __future__ import annotations

# Module pour les expressions régulières (Regex)
import re
# Type optionnel (peut être un dictionnaire ou None si rien n'est trouvé)
from typing import Optional
# Outil pour découper et analyser les adresses web (URLs)
from urllib.parse import urlparse

# Bibliothèque Pandas pour manipuler les données
import pandas as pd

# Classe représentant un e-mail déjà analysé
from .mail_parser import Parsed
# Fonction de normalisation de texte (minuscules, sans accents)
from .text_utils import norm

# Liste des noms d'agences trop génériques ou courts pour éviter les faux positifs lors de la recherche dans le texte
GENERIC_NAMES = {"marketing agency", "la boite", "billboard", "omd", "spikal", "quick agency", "wellbek", "push"}


# ------------------------------------------------------------------------------
# Fonction : domain_of
# Rôle : Extraire le nom de domaine propre d'une URL.
# Exemple : "https://www.mon-agence.ma/contact" devient "mon-agence.ma"
# ------------------------------------------------------------------------------
def domain_of(site: str) -> str:
    # Récupérer l'hôte de l'adresse web (sans http:// ni slash)
    host = urlparse(site if "//" in site else f"//{site}").netloc.lower().split(":")[0]
    # Supprimer les préfixes courants comme www., fr., en., ar.
    return re.sub(r"^(www|en|fr|ar)\.", "", host)


# ------------------------------------------------------------------------------
# Fonction : build_index
# Rôle : Créer un index rapide en mémoire avec toutes les agences pour chercher vite.
# ------------------------------------------------------------------------------
def build_index(df: pd.DataFrame) -> list[dict]:
    idx = []
    # Parcourir chaque agence du tableau pandas
    for _, r in df.iterrows():
        # Nettoyer le nom de l'agence (minuscules, sans accents, sans mention superflue)
        name_n = norm(r["nom"]).replace(" - social media agency", "").strip()
        idx.append({
            "id": int(r["id"]),                          # Identifiant unique de l'agence
            "nom": r["nom"],                             # Nom original
            "domain": domain_of(r["site"] or ""),        # Nom de domaine du site web
            "name_n": name_n,                            # Nom normalisé
            # Vrai si le nom est trop court ou générique (risque de fausse alerte)
            "generic": name_n in GENERIC_NAMES or len(name_n) < 5,
            # Expression régulière pour chercher le nom exact comme mot entier
            "name_rx": re.compile(r"(?<![a-z0-9])" + re.escape(name_n) + r"(?![a-z0-9])"),
        })
    return idx


# ------------------------------------------------------------------------------
# Fonction interne : _addr_domain_match
# Rôle : Vérifier si une des adresses e-mail correspond au nom de domaine du site.
# Exemple : "contact@agence.com" correspond au domaine "agence.com"
# ------------------------------------------------------------------------------
def _addr_domain_match(addrs: list, domain: str) -> Optional[str]:
    # Si l'agence n'a pas de domaine web, la correspondance est impossible
    if not domain:
        return None
    # Vérifier chaque adresse e-mail de la liste
    for a in addrs:
        # Extraire la partie après le symbole '@'
        d = a.rsplit("@", 1)[-1]
        # Si le domaine de l'e-mail est identique ou un sous-domaine
        if d == domain or d.endswith("." + domain):
            return a
    return None


# ------------------------------------------------------------------------------
# Fonction : match_agence
# Rôle : Trouver l'agence correspondant à un e-mail donné :
#        1. D'abord en comparant le nom de domaine de l'expéditeur / destinataire
#        2. Si rien n'est trouvé, en cherchant le nom de l'agence dans l'objet et le texte
# ------------------------------------------------------------------------------
def match_agence(index: list[dict], p: Parsed, sent: bool) -> Optional[dict]:
    # Si c'est un e-mail envoyé, on regarde les destinataires ; si reçu, l'expéditeur
    addrs = p.to_addrs if sent else p.from_addrs

    # Étape 1 : Correspondance stricte par nom de domaine
    for ag in index:
        if _addr_domain_match(addrs, ag["domain"]):
            return ag

    # Pour les e-mails envoyés, on s'arrête ici (on ne devine pas par le texte)
    if sent:
        return None

    # Étape 2 : Chercher le nom de l'agence dans le texte (uniquement pour les e-mails reçus)
    hay_head = norm(f"{p.from_name} {p.subject}")
    # On limite la recherche aux 1500 premiers caractères du corps pour la rapidité
    hay_body = norm(p.body[:1500])

    for ag in index:
        # Ne pas chercher les noms génériques (ex: "marketing") pour éviter les erreurs
        if ag["generic"]:
            continue
        # Si le nom de l'agence apparaît dans le sujet ou le corps du message
        if ag["name_rx"].search(hay_head) or ag["name_rx"].search(hay_body):
            return ag

    # Aucune agence n'a été trouvée pour cet e-mail
    return None
