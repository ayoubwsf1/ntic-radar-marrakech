# Base de Connaissances : NTic Radar Marrakech 🧭

## Résumé

Projet de suivi d'opportunités de stage à Marrakech, combinant collecte de données, tableaux de bord interactifs, filtrage, suivi de candidature et CV généré par IA. Développée avec Python · Streamlit · SQLite · IA (OpenRouter).

## Structure du Projet

### Architecture Général
```
app.py                  Point d'entrée Streamlit
stageradar/
  config.py             Configuration centrale
  database.py           Base de données SQLite
  cleaning.py           Nettoyage des données
  analytics.py          Analyses et statistiques
  filters.py            Filtres sidebar
  cv_render.py          Export PDF du CV
  gmail_scan.py         Connexion IMAP Gmail
  classification.py     Classification des e-mails
  ai/
    llm.py              Client OpenRouter / Anthropic
    cv.py               Bureau d'études CV (analyse → rédaction → export)
    profile.py          Profil candidat
    email_ai.py         Classification IA des e-mails
  ui/
    tab_dashboard.py    Tableau de bord
    tab_agences.py      Liste des agences
    tab_carte.py        Carte interactive
    tab_suivi.py        Suivi des candidatures
    tab_cv.py           Onglet CV
    tab_scan.py         Scan Gmail
data/
  agences_maroc.xlsx    Source des données
  stages.db           SQLite (cache) pour les agences
scripts/
  collect_agences.py    Collecte via Tavily
  clean_data.py         Nettoyage
  explore.py            Génération des figures
```

### Fichiers Principaux

#### App.py (Point d'Entrée Principal)
- **Rôle** : Point d'entrée Streamlit principal (fichier lancé avec `streamlit run app.py`)
- **Fonctions** :
  - `_boot()` : Initialise la base de données SQLite, synchronise les agences depuis Excel (mise en cache)
  - `main()` : Coordonne l'application entière : connexion, chargement données, affichage onglets, gestion état session

#### Système de Base de Données (stageradar/database.py)
- **Stockage principal** : SQLite pour les données d'agences et agences
- **Fonctions** :
  - `init_db()` : Crée toutes les tables nécessaires au démarrage
  - `sync_from_excel()` : Synchronise depuis Excel vers SQLite (une fois, via mise en cache)
  - `load_agences()` : Charge toutes les agences depuis SQLite pour l'application
- **Schéma** : Utilise `agences_maroc.xlsx` dans `data/` comme source initiale

#### Modules UI (stageradar/ui/)
- **tab_dashboard.py** : Tableau de bord avec statistiques et graphiques
- **tab_agences.py** : Liste des agences sous forme de tableau détaillé avec recherche
- **tab_carte.py** : Carte interactive (pydeck) des agences sur Marrakech
- **tab_suivi.py** : Suivi des candidatures (progression par statut de candidature)
- **tab_cv.py** : Génération de CV avec l'IA (OpenRouter)
- **tab_scan.py** : Résultat du scan Gmail (e-mails détectés)
- **sidebar.py** : Filtres d'interface gauche : ville, type, statut, recherche texte
- **header.py** : Logo, titre, bouton de déconnexion + KPI (nombre d'agences, etc.)

#### Pipelines de Données (scripts/)
- **collect_agences.py** : Collecte les agences via l'API Tavily (web scraping)
- **clean_data.py** : Nettoyage et normalisation des données (pandas)
- **explore.py** : Explore les données et génère les figures

#### Intelligence Artificielle (stageradar/ai/)
- **llm.py** : Client OpenRouter / Anthropic (basé sur requests + token counting)
- **cv.py** : Bureau d'études CV — orchestration de l'analyse → rédaction → export (export PDF via reportlab)
- **email_ai.py** : Classification IA des e-mails via l'IA (détection réponses)

#### Configuration (stageradar/config.py)
- **STATUTS** : Constantes de statut de candidature pour le suivi des candidatures (ex: « En attente », « Acceptée », « Refusée »)
- **Variables d'environnement** : OPENROUTER_API_KEY, TAVILY_API_KEY (gérées via .env/.env.example)

## Fonctionnalités Clé

### Collecte et Traitements de Données
- **Collecte web** : Via l'API Tavily (recherche des agences de stage)
- **Nettoyage des données** : Normalisation des données, validation structure
- **Pipeline d'ingestion** : Excel SQLite à la base de données SQLite
- **Cache de données** : Mise en cache des données Excel via st.cache_resource (une fois par session)

### Tableau de Bord et Visualisations
- **KPI** : Nombre total d'agences, distribution par catégorie/type
- **Graphiques interactifs** : Graphique à barres, pie (Plotly)
- **Carte interactive** : Carte de Marrakech avec points d'agences (pydeck)
- **Tableau détaillé** : Recherche et tri des agences (aggrégats)

### Suivi des Candidatures
- **Suivi par statut** : Progression des candidatures (onglet Suivi)
- **Filtres évolutifs** : Ville, type d'agence, statut de candidature, recherche texte
- **Prise en charge de la session** : Connexion Gmail (OAuth2) ou mode démo

### Génération de CV et IA
- **Agent CV** : Bureau d'études IA — analyse du profil, rédaction → export PDF
- **Classification d'e-mails** : Scan IA des réponses e-mails Gmail (IMAP)
- **Modèle IA** : Utilise OpenRouter avec Mistral/Gemma/Autres

## Technologies et Stack Technique

### Technologies Principales
| Composant | Technologie |
|---|---|
| Interface | Streamlit |
| Base de données | SQLite (sqlite3) |
| Analyse des données | pandas |
| Visualisations | Plotly, pydeck |
| Agent IA | OpenRouter (Gemma, Nemotron) |
| Export CV | reportlab (PDF) |
| Collecte web | Tavily API |
| Scan e-mail | IMAP / Gmail OAuth2 |
| Backend IA | OpenRouter (gratuit, clé API) |

### Ports et URL
- **Local** : `http://localhost:8501` (Streamlit)
- **Production** : `https://ntic-radar-marrakech-production.up.railway.app`
- **GitHub** : https://github.com/ayoubwsf1/ntic-radar-marrakech.git

## Configuration et Déploiement

### Installation
```bash
pip install -r requirements.txt
streamlit run app.py
```

### Variables d'Environnement
Créez `.env` depuis `.env.example` :
```
OPENROUTER_API_KEY=sk-or-v1-...   # Agent CV
TAVILY_API_KEY=...                 # Collecte
```

### Déploiement
- **Docker** : Dockerfile existant (voir Dockerfile)
- **Platform** : Railway (Docker)
- **Procédure** : git push → CI déploiement

## Conseils de Maintenance et Développement

### Maintenance des Données
1. **Mises à jour agences** : Utiliser `scripts/collect_agences.py` pour collecter de nouvelles agences
2. **Nettoyage** : Utiliser `scripts/clean_data.py` pour la qualité des données
3. **Séquencement** : sync_excel → init_db → charge applicative

### Développement Avancé
- **Améliorations UI/UX** : Composants UI Streamlit (sidebar/header)
- **Intégrations IA** : Bureau d'études CV (agent IA), classification e-mails (IA)
- **Performance** : Mise en cache (@st.cache_resource) des opérations de base de données lourdes

### Bonnes Pratiques
- **Unité d'application** : `app.py` contient tout le workflow Streamlit
- **Séparation des préoccupations** : UI (ui/), Business (stageradar/), Scripts (scripts/)
- **Mises en cache** : Bases de données lourdes mises en cache pour de meilleures performances
- **Environnement** : .env pour secrets, .env.example comme modèle

## Demandes d'Ajout Typiques

### Nouvelles Sources de Données
- Ajouter une nouvelle source Excel à `data/`
- Mettre à jour `database.sync_from_excel()` pour inclure le schéma
- Ajouter la nouvelle colonne à `stageradar.config`

### Nouveaux Onglets
- Créer `stageradar/ui/tab_nouveau.py` (modèle `render_tab_*`)
- Ajouter l'onglet dans `app.py` `st.tabs(["...", "..."]`)
- Conserver la signature : `render_tab_*(df_all)` ou `render_tab_*()`

### Nouvelles Visualisations
- Utiliser Plotly/pydeck via `st.plotly_chart()`/`st.pydeck_chart()`
- Ajouter les calculs via `stageradar.analytics`
- Ajouter les KPI via `stageradar.ui.header`

## Étapes Prochaines (Futur)

### Court Terme (1-2 semaines)
- [ ] Optimisation performance (streaming de base de données lourdes)
- [ ] Migration interface utilisateur (sidebar/glassmorphism)
- [ ] IA améliorée (suivi d'entretien via CV)

### Moyen Terme (1-3 mois)
- [ ] MCP (Model Context Protocol) pour intégrations externes
- [ ] Enrichissement dashboard (KPI/Messages dynamiques)
- [ ] ETL w/ historique complet (ajout nouvelles agences)

### Long Terme (3-6 mois)
- [ ] Génération IA complète (description d'offre d'emploi → CV)
- [ ] Suivi d'entretien automatisé (e-mails Gmail)
- [ ] Analyse sentiment (évolution analyse e-mails)

## Ressources

### Documentation du Projet
- **LIRE** : `app.py` pour le flux principal
- **LIRE** : `stageradar/database.py` pour le schéma
- **LIRE** : `stageradar/ui/` pour les composants UI

### Appels Utiles
```bash
streamlit run app.py        # Lancer l'application
pip install -r requirements.txt # Installation dépendances
python scripts/collect_agences.py # Collecter agences
python scripts/clean_data.py # Nettoyer données
```

### Problèmes Connus
1. **Linting** : Utiliser flake8/pylint sur le code `stageradar/`
2. **Performance** : Mise en cache des charges de base de données SQLite
3. **IA** : Surcoût d'erreur clé OpenRouter (vérifier .env)
4. **Déploiement** : Processus CI Railway (vérifier Dockerfile)

---
*Mis à jour : 2026-11-08 | Maintenance : Ayoub Aamire (AI201)*
*Pour la dernière mise à jour des connaissances, utiliser : `git diff HEAD~1 KNOWLEDGE_BASE.md`*