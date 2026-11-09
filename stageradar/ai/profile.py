# ==============================================================================
# Fichier : profile.py
# Rôle : Définir la structure du profil candidat et gérer son stockage dans SQLite.
#        Le profil contient toutes les informations personnelles et professionnelles
#        utilisées pour générer le CV automatiquement avec l'IA.
# ==============================================================================

# Permet d'utiliser les annotations de type modernes
from __future__ import annotations

# Module pour convertir les données en JSON (texte structuré)
import json
# Outils pour créer des classes de données et les convertir en dictionnaire
from dataclasses import asdict, dataclass, field

# Importer le module de gestion de la base de données
from .. import database


# ------------------------------------------------------------------------------
# Classe : Profil
# Rôle : Contenir toutes les informations du candidat pour la génération du CV.
# ------------------------------------------------------------------------------
@dataclass
class Profil:
    nom: str = ""                             # Nom complet du candidat (ex: "Ayoub Aamire")
    email: str = ""                           # Adresse e-mail professionnelle
    telephone: str = ""                       # Numéro de téléphone
    liens: str = ""                           # Liens sociaux/professionnels séparés par virgules (LinkedIn, GitHub, portfolio)
    formation: str = ""                       # Parcours académique (un diplôme par ligne)
    competences: list = field(default_factory=list)  # Liste des compétences techniques (Python, React, SEO...)
    experiences: str = ""                     # Expériences professionnelles formatées en blocs texte
    projets: str = ""                         # Projets réalisés (format : titre + description ligne par ligne)
    interets: str = ""                        # Centres d'intérêt personnels
    type_stage: str = "Stage"                 # Type de contrat recherché (Stage, Alternance, Emploi, Freelance)
    duree: str = ""                           # Durée souhaitée (ex: "3 mois", "6 mois")
    langues: str = "Arabe, Français, Anglais" # Langues parlées (par défaut Arabe, Français, Anglais)
    ville: str = "Marrakech"                  # Ville de résidence ou ville cible

    # Propriété calculée : vérifier si le profil est encore vide (non rempli)
    @property
    def vide(self) -> bool:
        return not (self.nom.strip() or self.competences or self.formation.strip() or self.experiences.strip())


# ------------------------------------------------------------------------------
# Fonction : charger
# Rôle : Lire le profil enregistré dans la base de données SQLite et le convertir
#        en objet Python Profil.
# ------------------------------------------------------------------------------
def charger() -> Profil:
    try:
        # Lire le JSON stocké dans la table 'reglages' sous la clé 'profil'
        d = json.loads(database.get_reglage("profil", "{}") or "{}")
    except json.JSONDecodeError:
        # Si le JSON est corrompu ou vide, utiliser un dictionnaire vide
        d = {}
    # Créer et retourner un objet Profil en ne gardant que les champs valides
    return Profil(**{k: v for k, v in d.items() if k in Profil.__dataclass_fields__})


# ------------------------------------------------------------------------------
# Fonction : sauver
# Rôle : Enregistrer le profil dans la base de données SQLite au format JSON.
# ------------------------------------------------------------------------------
def sauver(p: Profil) -> None:
    # Convertir l'objet Profil en dictionnaire, puis en texte JSON
    # ensure_ascii=False permet de garder les caractères accentués intacts
    database.set_reglage("profil", json.dumps(asdict(p), ensure_ascii=False))


# ------------------------------------------------------------------------------
# Fonction utilitaire : parse_competences
# Rôle : Découper un texte brut de compétences (séparées par virgules, points-virgules
#        ou retours à la ligne) en une liste propre.
# ------------------------------------------------------------------------------
def parse_competences(texte: str) -> list[str]:
    # Remplacer les points-virgules et les sauts de ligne par des virgules
    # Puis découper et nettoyer chaque compétence (enlever espaces inutiles)
    return [c.strip() for c in texte.replace(";", ",").replace("\n", ",").split(",") if c.strip()]
