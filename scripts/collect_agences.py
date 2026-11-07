from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path

import requests
from openpyxl import load_workbook

from stageradar.config import CITY_COORDS, TYPES, XLSX_PATH, get_secret
from stageradar.matching import domain_of

TAVILY_URL = "https://api.tavily.com/search"

ANNUAIRES: list[str] = []

DOMAINES_EXCLUS = {
    "facebook.com", "instagram.com", "linkedin.com", "twitter.com", "x.com",
    "youtube.com", "tiktok.com", "wikipedia.org", "clutch.co", "indeed.com",
    "glassdoor.com", "rekrute.com", "emploi.ma", "marocannonces.com", "avito.ma",
    "google.com", "googleapis.com", "gstatic.com", "goodfirms.co", "designrush.com",
    "trustpilot.com", "pagesjaunes.ma", "yelp.com", "wixsite.com", "blogspot.com",
    "medium.com", "pinterest.com", "doubleclick.net", "google-analytics.com",
    "googletagmanager.com", "cloudflare.com", "schema.org", "w3.org", "apple.com",
    "play.google.com", "whatsapp.com", "wa.me",
}

REQUETE_PAR_TYPE = {
    "Web & Développement": "agence développement web création site internet",
    "Marketing digital": "agence marketing digital SEO SEA réseaux sociaux",
    "Design & Créa": "agence design graphique branding création",
    "Publicité & Com": "agence publicité communication événementiel",
}

_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": "Mozilla/5.0 (compatible; NticRadarMaroc/1.0)"})

_HREF_RX = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)


def normaliser_nom(domaine: str) -> str:
    base = domaine.split(".")[0]
    base = re.sub(r"[-_]+", " ", base)
    return base.title()


def domaines_existants() -> set[str]:
    wb = load_workbook(XLSX_PATH, data_only=True)
    ws = wb["Agences"]
    headers = [c.value for c in ws[1]]
    i_site = headers.index("Site web")
    out = set()
    for row in ws.iter_rows(min_row=2, values_only=True):
        site = row[i_site]
        if site:
            d = domain_of(str(site))
            if d:
                out.add(d)
    return out


def rechercher(api_key: str, requete: str, annuaires: list[str], budget: list) -> list[dict]:
    if budget[0] <= 0:
        return []
    budget[0] -= 1
    payload = {
        "api_key": api_key,
        "query": requete,
        "search_depth": "basic",
        "max_results": 10,
    }
    if annuaires:
        payload["include_domains"] = annuaires
    try:
        r = requests.post(TAVILY_URL, json=payload, timeout=15)
        if r.status_code == 401:
            print("  ⚠️  Clé Tavily invalide (401). Arrêt.")
            budget[0] = 0
            return []
        if r.status_code == 429:
            print("  ⚠️  Quota Tavily épuisé pour ce mois (429). Arrêt.")
            budget[0] = 0
            return []
        r.raise_for_status()
        return r.json().get("results", [])
    except Exception as e:
        print(f"  ⚠️  Erreur sur « {requete} » : {e}")
        return []


def trouver_site_reel(url_fiche: str) -> str:
    domaine_annuaire = domain_of(url_fiche)
    try:
        r = _SESSION.get(url_fiche, timeout=12)
        r.raise_for_status()
    except Exception:
        return ""

    for lien in _HREF_RX.findall(r.text):
        if not lien.startswith("http"):
            continue
        d = domain_of(lien)
        if not d or d == domaine_annuaire or d in DOMAINES_EXCLUS:
            continue
        return f"https://{d}"
    return ""


def extraire_candidat(item: dict, ville: str, type_: str, annuaires: list[str]) -> dict | None:
    lien = item.get("url", "")
    if not lien:
        return None

    if annuaires:
        site = trouver_site_reel(lien)
        source = f"Annuaire ({domain_of(lien)})"
    else:
        d = domain_of(lien)
        if not d or d in DOMAINES_EXCLUS:
            return None
        site = lien
        source = "Recherche web (Tavily)"

    if not site:
        return None
    domaine = domain_of(site)
    if not domaine or domaine in DOMAINES_EXCLUS:
        return None

    titre = (item.get("title") or "").strip()
    nom = re.split(r"[|\-–—:]", titre)[0].strip()[:80] if titre else ""
    nom = nom or normaliser_nom(domaine)
    contenu = re.sub(r"\s+", " ", item.get("content", "")).strip()
    return {
        "nom": nom, "type": type_, "ville": ville, "taille": "",
        "services": contenu[:200], "site": site,
        "source": source, "domaine": domaine,
    }


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Recherche de nouvelles agences via Tavily (recherche web, quota gratuit mensuel)."
    )
    ap.add_argument("--villes", nargs="*", default=["Marrakech"], help="Villes ciblées (défaut : Marrakech).")
    ap.add_argument("--types", nargs="*", default=TYPES, help="Types d'agences ciblés (défaut : tous).")
    ap.add_argument(
        "--annuaires", nargs="*", default=ANNUAIRES,
        help="Restreindre la recherche à ces sites (défaut : aucun = tout le web).",
    )
    ap.add_argument("--max-requetes", type=int, default=90, help="Plafond de requêtes Tavily (1 requête = 1 crédit).")
    ap.add_argument("--api-key", default=get_secret("TAVILY_API_KEY"), help="Ou variable d'env TAVILY_API_KEY.")
    args = ap.parse_args()

    if not args.api_key:
        sys.exit(
            "❌ Clé API Tavily manquante.\n"
            "   export TAVILY_API_KEY=\"tvly-...\"\n"
            "   (récupérable gratuitement sur https://app.tavily.com/)"
        )
    if not Path(XLSX_PATH).exists():
        sys.exit(f"❌ Fichier introuvable : {XLSX_PATH}")

    existants = domaines_existants()
    print(f"📚 {len(existants)} agence(s) déjà dans le fichier.")
    if args.annuaires:
        print(f"🗂️  Recherche restreinte aux annuaires : {', '.join(args.annuaires)}\n")
    else:
        print("🌐 Recherche libre sur tout le web (via Tavily)\n")

    budget = [args.max_requetes]
    trouvees: dict[str, dict] = {}

    for ville in args.villes:
        for type_ in args.types:
            if budget[0] <= 0:
                break
            requete = f"{REQUETE_PAR_TYPE.get(type_, 'agence')} {ville} Maroc"
            print(f"🔎 [{budget[0]} requêtes restantes] {ville} — {type_}")
            for item in rechercher(args.api_key, requete, args.annuaires, budget):
                cand = extraire_candidat(item, ville, type_, args.annuaires)
                if not cand or cand["domaine"] in existants or cand["domaine"] in trouvees:
                    continue
                trouvees[cand["domaine"]] = cand
                if args.annuaires:
                    time.sleep(0.3)
            time.sleep(0.2)
        if budget[0] <= 0:
            print("⏹️  Plafond de requêtes atteint, arrêt.")
            break

    if not trouvees:
        print("\nAucune nouvelle agence trouvée cette fois-ci.")
        return

    print(f"\n✅ {len(trouvees)} nouvelle(s) agence(s) trouvée(s). Ajout dans {XLSX_PATH.name}…")
    wb = load_workbook(XLSX_PATH)
    ws = wb["Agences"]
    n = ws.max_row - 1
    for cand in trouvees.values():
        n += 1
        lat, lng = CITY_COORDS.get(cand["ville"], (31.79, -7.09))
        ws.append([
            n, cand["nom"], cand["type"], cand["ville"], cand["taille"],
            cand["services"], cand["site"], cand["source"], lat, lng,
            "Non encore postulé", "Trouvée automatiquement — à vérifier",
        ])
        print(f"   + {cand['nom']} ({cand['ville']}, {cand['type']}) — {cand['site']}")

    wb.save(XLSX_PATH)
    print(f"\n💾 Fichier mis à jour : {XLSX_PATH}")
    print("👉 Relance l'application (streamlit run app.py) pour importer ces agences dans la base.")


if __name__ == "__main__":
    main()
