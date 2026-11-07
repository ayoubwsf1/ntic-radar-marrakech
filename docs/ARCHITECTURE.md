# Architecture

## Vue d'ensemble

| Couche | Fichiers | Rôle |
|---|---|---|
| Collecte | `scripts/collect_agences.py` | Recherche web (API Tavily), extraction, dédoublonnage |
| Préparation | `stageradar/cleaning.py`, `scripts/clean_data.py` | Nettoyage pandas + rapport des corrections |
| Données | `stageradar/database.py`, `data/` | Excel (source) et SQLite (`agences`, `reglages`) |
| Logique métier | `classification.py`, `events.py`, `matching.py`, `filters.py`, `gmail_scan.py` | Statuts de candidature, scan IMAP, filtres |
| Analyse | `stageradar/analytics.py`, `scripts/explore.py` | Statistiques descriptives et figures |
| Agent CV | `stageradar/ai/cv.py`, `stageradar/cv_render.py` | Rédaction, vérification anti-invention, export PDF / DOCX |
| IA e-mails | `stageradar/ai/email_ai.py` | Classification des réponses de recrutement |
| Frontend | `app.py`, `stageradar/ui/*` | Interface Streamlit en 6 onglets |

## Flux de données

1. `collect_*` interroge Tavily → résultats bruts (titre, URL, extrait).
2.  Les agences sont importées depuis Excel (`database.sync_from_excel`) ; `cleaning.nettoyer` prépare les fichiers bruts.
4. L'interface lit SQLite via `database.load_*`, calcule les analyses avec pandas et affiche tableau de bord, carte et fiches.
5. L'agent CV reçoit le profil (et éventuellement une agence), produit un CV structuré, le vérifie, puis `cv_render` l'exporte en PDF et DOCX.
6. Le scan Gmail lit les messages en lecture seule (`BODY.PEEK`), les rattache à une agence par domaine ou nom, les classe, puis met à jour le statut sans jamais le rétrograder.

## Choix techniques

- **Streamlit** : interface web 100 % Python, déploiement gratuit, adapté à un projet data.
- **SQLite** : zéro configuration ; suffisant pour un utilisateur ; remplaçable par PostgreSQL.
- **Tavily** : API de recherche web conçue pour les agents IA, quota gratuit mensuel.
- **IA hybride** : méthodes locales (mise en forme du profil, règles) pour le fonctionnement hors ligne et sans coût, LLM pour la qualité rédactionnelle. Le LLM est appelé avec `requests`, sans SDK, et toujours avec un repli local.
- **Secrets** : variables d'environnement, `.env` ou `st.secrets`, jamais commités.

## Sécurité et confidentialité

- Mot de passe d'application Gmail conservé en mémoire de session uniquement.
- Analyse IA des e-mails désactivée par défaut, extraits limités à 1500 caractères.
- Les prompts interdisent d'inventer des expériences ou diplômes, et le code retire de toute façon du CV ce qui n'est pas dans le profil.
