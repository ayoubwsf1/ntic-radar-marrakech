# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commandes essentielles

```bash
# Lancer l'application
streamlit run app.py

# Tests unitaires
python -m unittest discover -s tests -t . -v

# Un seul test
python -m unittest tests.test_database -v

# Collecter de nouvelles agences
python -m scripts.collect_agences --villes Marrakech

# Nettoyer les données brutes
python -m scripts.clean_data

# Générer les figures (stats)
python -m scripts.explore

# Installer les dépendances
pip install -r requirements.txt
pip install -r requirements-dev.txt  # pour les figures matplotlib
```

## Configuration

Copier `.env.example` en `.env` à la racine. Variables clés :

| Variable | Rôle | Obligatoire |
|---|---|---|
| `TAVILY_API_KEY` | Collecte web des agences | Pour `collect_agences` |
| `ANTHROPIC_API_KEY` | Agent CV + classification e-mails | Non |
| `RADAR_LLM_MODEL` | Modèle LLM (défaut : `claude-sonnet-5-5`) | Non |
| `RADAR_DB` | Chemin SQLite (défaut : `stages.db`) | Non |

Les secrets peuvent aussi aller dans `.streamlit/secrets.toml` (voir `secrets.toml.example`). La fonction `get_secret()` dans `stageradar/config.py` lit d'abord `os.environ`, puis `st.secrets`.

## Architecture

```
app.py                  Point d'entrée Streamlit — boot, auth, onglets
stageradar/
  config.py             Chemins, constantes métier, get_secret()
  database.py           SQLite via sqlite3 : agences + réglages
  cleaning.py           Pipeline pandas : normalisation, dédoublonnage, rapport
  analytics.py          Comptages, croisements ville×type, termes fréquents
  filters.py            Filtrage du DataFrame selon les choix de la sidebar
  cv_render.py          Export PDF (reportlab) et DOCX (python-docx)
  gmail_scan.py         Connexion IMAP, lecture des réponses
  classification.py     Règles regex FR/EN pour classer les e-mails
  mail_parser.py        Parsing des messages bruts
  matching.py           Rapprochement e-mail ↔ agence
  events.py             Historique des actions
  text_utils.py         Utilitaires texte partagés
  ai/
    llm.py              Appel HTTP direct à l'API Anthropic (pas de SDK)
    cv.py               Agent CV : analyse → rédaction → vérification → export
    profile.py          Lecture / écriture du profil candidat (SQLite reglages)
    email_ai.py         Classification LLM des e-mails non reconnus par les règles
  ui/
    header.py           Bandeau titre + KPIs globaux
    sidebar.py          Filtres ville / type / statut
    styles.py           CSS injecté via st.markdown
    login.py            Page de connexion Gmail ou mode démo
    tab_agences.py      Onglet liste + ajout manuel
    tab_carte.py        Onglet carte pydeck
    tab_dashboard.py    Onglet tableau de bord
    tab_suivi.py        Onglet suivi des candidatures + export Excel
    tab_cv.py           Onglet Agent CV
    tab_scan.py         Onglet dernier scan Gmail
    gmail_panel.py      Composant réutilisable pour le scan
    helpers.py          Petits utilitaires UI
scripts/
  collect_agences.py    Collecte via API Tavily
  clean_data.py         Lance cleaning.py sur data/raw
  explore.py            Stats + figures dans docs/figures/
data/
  agences_maroc.xlsx    Source Excel (feuille « Agences »)
  raw/                  Données brutes avant nettoyage
  cleaned/              Données nettoyées + rapport
docs/
  ARCHITECTURE.md       Détails d'architecture
  DATA.md               Dictionnaire de données + journal de nettoyage
tests/
  test_database.py / test_cleaning.py / test_cv.py / test_classification.py
```

## Points importants

**Flux de données** : `data/agences_maroc.xlsx` → `database.sync_from_excel()` → `stages.db` (SQLite). Le boot se fait une seule fois via `@st.cache_resource`. La base est la source de vérité à l'exécution ; l'Excel reste la source de vérité pour le jeu de données initial.

**LLM** : `stageradar/ai/llm.py` fait un appel HTTP direct à `https://api.anthropic.com/v1/messages` sans SDK. Si `ANTHROPIC_API_KEY` est absente, l'agent CV met en forme le profil brut sans reformulation, et la classification e-mail tombe en mode règles seulement.

**Modèle par défaut** : `claude-sonnet-5-5` (défini dans `config.py`).

**Auth** : le mot de passe Gmail reste en `st.session_state` uniquement, jamais écrit sur disque. Le mode démo (`st.session_state["demo"] = True`) contourne la page de login.

**SQLite sur Streamlit Community Cloud** : le disque est éphémère, la base est recréée depuis l'Excel à chaque redémarrage. Pour persister les statuts, utiliser Docker avec un volume monté sur `/data`.
