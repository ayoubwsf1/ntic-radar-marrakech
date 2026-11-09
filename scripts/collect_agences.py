# ==============================================================================
# Script : collect_agences.py
# Rôle : Chercher automatiquement des agences sur Internet avec l'API Tavily.
# ==============================================================================

# Permet d'utiliser les types modernes de Python (annotations de type)
from __future__ import annotations

# Module pour lire les options passées dans le terminal (arguments)
import argparse
# Module pour interagir avec le système d'exploitation
import os
# Module pour chercher des textes avec des expressions régulières (Regex)
import re
# Module pour quitter le programme ou gérer le système
import sys
# Module pour faire des pauses dans le temps (attendre quelques secondes)
import time
# Module pour manipuler les chemins de fichiers facilement
from pathlib import Path

# Bibliothèque pour envoyer des requêtes HTTP (accéder à des sites web et APIs)
import requests
# Bibliothèque pour ouvrir et modifier des fichiers Excel (.xlsx)
from openpyxl import load_workbook

# Importer les coordonnées des villes, les catégories, le chemin Excel et la fonction pour lire les clés secrètes
from stageradar.config import CITY_COORDS, TYPES, XLSX_PATH, get_secret
# Importer la fonction qui extrait le nom de domaine d'une URL (ex: 'google.com' depuis 'https://www.google.com')
from stageradar.matching import domain_of

# Adresse web de l'API Tavily pour faire la recherche
TAVILY_URL = "https://api.tavily.com/search"

# Liste des annuaires web (vide par défaut, on cherche sur tout le web)
ANNUAIRES: list[str] = []

# Liste des sites internet interdits qu'on ne veut pas enregistrer (réseaux sociaux, annonces, etc.)
DOMAINES_EXCLUS = {
    # Réseaux sociaux populaires
    "facebook.com", "instagram.com", "linkedin.com", "twitter.com", "x.com",
    "youtube.com", "tiktok.com", "wikipedia.org", "clutch.co", "indeed.com",
    # Sites d'emploi et petites annonces au Maroc
    "glassdoor.com", "rekrute.com", "emploi.ma", "marocannonces.com", "avito.ma",
    # Moteurs de recherche et plateformes techniques
    "google.com", "googleapis.com", "gstatic.com", "goodfirms.co", "designrush.com",
    "trustpilot.com", "pagesjaunes.ma", "yelp.com", "wixsite.com", "blogspot.com",
    "medium.com", "pinterest.com", "doubleclick.net", "google-analytics.com",
    "googletagmanager.com", "cloudflare.com", "schema.org", "w3.org", "apple.com",
    # Applications de messagerie
    "play.google.com", "whatsapp.com", "wa.me",
}

# Dictionnaire : pour chaque type d'agence, on prépare les mots-clés de recherche
REQUETE_PAR_TYPE = {
    # Mots-clés pour chercher des agences web
    "Web & Développement": "agence développement web création site internet",
    # Mots-clés pour chercher des agences de marketing
    "Marketing digital": "agence marketing digital SEO SEA réseaux sociaux",
    # Mots-clés pour chercher des agences de design
    "Design & Créa": "agence design graphique branding création",
    # Mots-clés pour chercher des agences de publicité
    "Publicité & Com": "agence publicité communication événementiel",
}

# Création d'une session HTTP pour faire les requêtes plus vite
_SESSION = requests.Session()
# On indique le nom de notre application pour se présenter aux sites web (User-Agent)
_SESSION.headers.update({"User-Agent": "Mozilla/5.0 (compatible; NticRadarMaroc/1.0)"})

# Expression régulière pour trouver les liens HTML du type href="https://..."
_HREF_RX = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)


# ------------------------------------------------------------------------------
# Fonction : normaliser_nom
# Rôle : Créer un nom propre à partir d'un nom de domaine internet.
# Exemple : "mon-agence.ma" devient "Mon Agence"
# ------------------------------------------------------------------------------
def normaliser_nom(domaine: str) -> str:
    # On prend la partie avant le point (ex: "mon-agence" dans "mon-agence.ma")
    base = domaine.split(".")[0]
    # On remplace les tirets et les underscores par un espace
    base = re.sub(r"[-_]+", " ", base)
    # On met la première lettre de chaque mot en majuscule
    return base.title()


# ------------------------------------------------------------------------------
# Fonction : domaines_existants
# Rôle : Lire le fichier Excel actuel et lister tous les sites déjà enregistrés
#        pour ne pas ajouter deux fois la même agence (éviter les doublons).
# ------------------------------------------------------------------------------
def domaines_existants() -> set[str]:
    # Charger le classeur Excel
    wb = load_workbook(XLSX_PATH, data_only=True)
    # Sélectionner la feuille nommée "Agences"
    ws = wb["Agences"]
    # Lire la première ligne (les titres des colonnes)
    headers = [c.value for c in ws[1]]
    # Trouver le numéro de la colonne "Site web"
    i_site = headers.index("Site web")
    # Créer un ensemble (set) vide pour stocker les domaines
    out = set()
    # Parcourir toutes les lignes à partir de la ligne 2
    for row in ws.iter_rows(min_row=2, values_only=True):
        # Récupérer la valeur de la colonne "Site web"
        site = row[i_site]
        # Si le site existe
        if site:
            # Extraire le domaine (ex: "agence.com")
            d = domain_of(str(site))
            # Si le domaine est valide, l'ajouter à notre ensemble
            if d:
                out.add(d)
    # Retourner l'ensemble des domaines déjà connus
    return out


# ------------------------------------------------------------------------------
# Fonction : rechercher
# Rôle : Envoyer une question à l'API Tavily et recevoir la liste des résultats.
# ------------------------------------------------------------------------------
def rechercher(api_key: str, requete: str, annuaires: list[str], budget: list) -> list[dict]:
    # Si le nombre maximum de requêtes autorisées est atteint (budget = 0)
    if budget[0] <= 0:
        # On arrête et on renvoie une liste vide
        return []
    # On diminue le budget d'une unité (1 requête utilisée)
    budget[0] -= 1
    # Préparer les données à envoyer à Tavily en format JSON
    payload = {
        "api_key": api_key,          # Clé secrète d'accès à l'API
        "query": requete,            # Texte de la recherche (ex: "agence web Marrakech")
        "search_depth": "basic",     # Mode de recherche rapide
        "max_results": 10,           # Nombre maximum de résultats demandés (10 par page)
    }
    # Si on a précisé des annuaires spécifiques
    if annuaires:
        payload["include_domains"] = annuaires
    try:
        # Envoyer la requête POST à Tavily avec une limite de 15 secondes d'attente
        r = requests.post(TAVILY_URL, json=payload, timeout=15)
        # Si la clé API n'est pas bonne (erreur 401 Non autorisé)
        if r.status_code == 401:
            print("  ⚠️  Clé Tavily invalide (401). Arrêt.")
            budget[0] = 0  # On met le budget à 0 pour tout arrêter
            return []
        # Si le quota mensuel gratuit est terminé (erreur 429 Trop de requêtes)
        if r.status_code == 429:
            print("  ⚠️  Quota Tavily épuisé pour ce mois (429). Arrêt.")
            budget[0] = 0  # On arrête le programme
            return []
        # Vérifier qu'il n'y a pas d'autre erreur HTTP
        r.raise_for_status()
        # Récupérer la liste des résultats trouvés dans la réponse JSON
        return r.json().get("results", [])
    except Exception as e:
        # En cas de problème de connexion ou autre erreur, afficher le message
        print(f"  ⚠️  Erreur sur « {requete} » : {e}")
        return []


# ------------------------------------------------------------------------------
# Fonction : trouver_site_reel
# Rôle : Si le lien trouvé est une page d'annuaire, ouvrir cette page pour
#        chercher le vrai site officiel de l'agence.
# ------------------------------------------------------------------------------
def trouver_site_reel(url_fiche: str) -> str:
    # Récupérer le domaine de l'annuaire (ex: pagesjaunes.ma)
    domaine_annuaire = domain_of(url_fiche)
    try:
        # Ouvrir la page de l'annuaire avec une limite de 12 secondes
        r = _SESSION.get(url_fiche, timeout=12)
        r.raise_for_status()
    except Exception:
        # Si la page ne s'ouvre pas, renvoyer une chaîne vide
        return ""

    # Chercher tous les liens HTML présents dans la page
    for lien in _HREF_RX.findall(r.text):
        # On ne garde que les liens complets qui commencent par "http"
        if not lien.startswith("http"):
            continue
        # Récupérer le domaine du lien
        d = domain_of(lien)
        # Si le lien est vide, ou s'il pointe vers l'annuaire lui-même, ou vers un site exclu (ex: Facebook)
        if not d or d == domaine_annuaire or d in DOMAINES_EXCLUS:
            continue
        # C'est le vrai site de l'agence : on le renvoie en format https
        return f"https://{d}"
    # Si aucun site officiel n'est trouvé dans la page
    return ""


# ------------------------------------------------------------------------------
# Fonction : extraire_candidat
# Rôle : Transformer un résultat brut de Tavily en une fiche d'agence propre.
# ------------------------------------------------------------------------------
def extraire_candidat(item: dict, ville: str, type_: str, annuaires: list[str]) -> dict | None:
    # Récupérer le lien internet du résultat
    lien = item.get("url", "")
    # Si pas de lien, on ignore ce résultat
    if not lien:
        return None

    # Si on cherche dans des annuaires
    if annuaires:
        # Trouver le vrai site web dans la fiche
        site = trouver_site_reel(lien)
        source = f"Annuaire ({domain_of(lien)})"
    else:
        # Recherche directe sur le web
        d = domain_of(lien)
        # Si le domaine est vide ou dans la liste noire (exclus)
        if not d or d in DOMAINES_EXCLUS:
            return None
        site = lien
        source = "Recherche web (Tavily)"

    # Si aucun site valide n'est trouvé
    if not site:
        return None
    # Récupérer le nom de domaine
    domaine = domain_of(site)
    # Vérifier encore une fois que le domaine n'est pas interdit
    if not domaine or domaine in DOMAINES_EXCLUS:
        return None

    # Récupérer le titre de la page web
    titre = (item.get("title") or "").strip()
    # Couper le titre au premier séparateur (| ou -) pour garder seulement le nom de l'agence
    nom = re.split(r"[|\-–—:]", titre)[0].strip()[:80] if titre else ""
    # Si le nom est vide, on utilise le domaine nettoyé
    nom = nom or normaliser_nom(domaine)
    # Nettoyer les espaces dans la description (résumé des services)
    contenu = re.sub(r"\s+", " ", item.get("content", "")).strip()
    # Renvoyer le dictionnaire avec toutes les informations de l'agence
    return {
        "nom": nom, "type": type_, "ville": ville, "taille": "",
        "services": contenu[:200], "site": site,
        "source": source, "domaine": domaine,
    }


# ------------------------------------------------------------------------------
# Fonction principale : main
# Rôle : Coordonner toute la collecte : lire les options, faire les recherches,
#        filtrer les doublons et enregistrer les nouvelles agences dans Excel.
# ------------------------------------------------------------------------------
def main() -> None:
    # Créer le gestionnaire d'arguments de la ligne de commande
    ap = argparse.ArgumentParser(
        description="Recherche de nouvelles agences via Tavily (recherche web, quota gratuit mensuel)."
    )
    # Option pour choisir les villes (par défaut Marrakech)
    ap.add_argument("--villes", nargs="*", default=["Marrakech"], help="Villes ciblées (défaut : Marrakech).")
    # Option pour choisir les types d'agences (par défaut tous les types)
    ap.add_argument("--types", nargs="*", default=TYPES, help="Types d'agences ciblés (défaut : tous).")
    # Option pour limiter la recherche à certains annuaires
    ap.add_argument(
        "--annuaires", nargs="*", default=ANNUAIRES,
        help="Restreindre la recherche à ces sites (défaut : aucun = tout le web).",
    )
    # Option pour limiter le nombre de requêtes à consommer (par défaut 90)
    ap.add_argument("--max-requetes", type=int, default=90, help="Plafond de requêtes Tavily (1 requête = 1 crédit).")
    # Option pour fournir la clé API Tavily (ou prise automatiquement dans .env)
    ap.add_argument("--api-key", default=get_secret("TAVILY_API_KEY"), help="Ou variable d'env TAVILY_API_KEY.")
    # Lire les arguments entrés par l'utilisateur
    args = ap.parse_args()

    # Si la clé API est introuvable, afficher une erreur et quitter
    if not args.api_key:
        sys.exit(
            "❌ Clé API Tavily manquante.\n"
            "   export TAVILY_API_KEY=\"tvly-...\"\n"
            "   (récupérable gratuitement sur https://app.tavily.com/)"
        )
    # Si le fichier Excel n'existe pas, afficher une erreur et quitter
    if not Path(XLSX_PATH).exists():
        sys.exit(f"❌ Fichier introuvable : {XLSX_PATH}")

    # Récupérer la liste des agences déjà présentes dans Excel
    existants = domaines_existants()
    print(f"📚 {len(existants)} agence(s) déjà dans le fichier.")
    # Informer l'utilisateur du mode de recherche choisi
    if args.annuaires:
        print(f"🗂️  Recherche restreinte aux annuaires : {', '.join(args.annuaires)}\n")
    else:
        print("🌐 Recherche libre sur tout le web (via Tavily)\n")

    # Initialiser le budget de requêtes restantes sous forme de liste (pour pouvoir le modifier partout)
    budget = [args.max_requetes]
    # Dictionnaire pour stocker les nouvelles agences trouvées pendant cette session
    trouvees: dict[str, dict] = {}

    # Boucle 1 : pour chaque ville sélectionnée
    for ville in args.villes:
        # Boucle 2 : pour chaque type d'agence sélectionné
        for type_ in args.types:
            # Si le budget de requêtes est épuisé, arrêter
            if budget[0] <= 0:
                break
            # Construire la phrase de recherche (ex: "agence développement web Marrakech Maroc")
            requete = f"{REQUETE_PAR_TYPE.get(type_, 'agence')} {ville} Maroc"
            print(f"🔎 [{budget[0]} requêtes restantes] {ville} — {type_}")
            # Lancer la recherche avec l'API Tavily et parcourir les résultats
            for item in rechercher(args.api_key, requete, args.annuaires, budget):
                # Extraire les informations propres de l'agence
                cand = extraire_candidat(item, ville, type_, args.annuaires)
                # Si l'agence est invalide, ou déjà dans Excel, ou déjà trouvée à l'instant : on l'ignore
                if not cand or cand["domaine"] in existants or cand["domaine"] in trouvees:
                    continue
                # Enregistrer l'agence dans notre dictionnaire des découvertes
                trouvees[cand["domaine"]] = cand
                # Petite pause pour ne pas surcharger les serveurs
                if args.annuaires:
                    time.sleep(0.3)
            # Petite pause entre chaque recherche
            time.sleep(0.2)
        # Si budget épuisé, sortir de la boucle des villes
        if budget[0] <= 0:
            print("⏹️  Plafond de requêtes atteint, arrêt.")
            break

    # Si aucune nouvelle agence n'a été trouvée
    if not trouvees:
        print("\nAucune nouvelle agence trouvée cette fois-ci.")
        return

    # Si on a trouvé de nouvelles agences, les ajouter dans le fichier Excel
    print(f"\n✅ {len(trouvees)} nouvelle(s) agence(s) trouvée(s). Ajout dans {XLSX_PATH.name}…")
    # Ouvrir le fichier Excel existant
    wb = load_workbook(XLSX_PATH)
    # Sélectionner la feuille "Agences"
    ws = wb["Agences"]
    # Compter le nombre de lignes actuelles
    n = ws.max_row - 1
    # Parcourir chaque nouvelle agence trouvée
    for cand in trouvees.values():
        # Incrémenter le numéro identifiant
        n += 1
        # Récupérer les coordonnées GPS (latitude et longitude) de la ville
        lat, lng = CITY_COORDS.get(cand["ville"], (31.79, -7.09))
        # Ajouter une nouvelle ligne dans le tableau Excel avec toutes les colonnes
        ws.append([
            n, cand["nom"], cand["type"], cand["ville"], cand["taille"],
            cand["services"], cand["site"], cand["source"], lat, lng,
            "Non encore postulé", "Trouvée automatiquement — à vérifier",
        ])
        # Afficher le nom de l'agence ajoutée dans le terminal
        print(f"   + {cand['nom']} ({cand['ville']}, {cand['type']}) — {cand['site']}")

    # Sauvegarder les modifications dans le fichier Excel
    wb.save(XLSX_PATH)
    print(f"\n💾 Fichier mis à jour : {XLSX_PATH}")
    print("👉 Relance l'application (streamlit run app.py) pour importer ces agences dans la base.")


# Point d'entrée : si on lance ce fichier directement depuis le terminal, exécuter main()
if __name__ == "__main__":
    main()
