# Ntic Radar Marrakech 🧭

Plateforme de recherche, d'analyse et de suivi des opportunités de stage à Marrakech.  
Développée avec Python · Streamlit · SQLite · IA (OpenRouter).

---

## Fonctionnalités

- **Collecte** des agences via l'API Tavily
- **Nettoyage** et normalisation des données (pandas)
- **Tableau de bord** avec visualisations interactives (charts, pie, carte)
- **Suivi** des candidatures par statut
- **Carte interactive** des agences (pydeck)
- **Agent CV** — génération PDF avec IA (OpenRouter / Mistral / Gemma)
- **Scan Gmail** — détection automatique des réponses

---

## Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/ayoubwsf1/ntic-radar-marrakech.git
cd ntic-radar-marrakech
```

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3. Configurer les variables d'environnement

Copier `.env.example` en `.env` :

```bash
cp .env.example .env
```

Renseigner les clés dans `.env` :

```
OPENROUTER_API_KEY=sk-or-v1-...   # pour l'agent CV (gratuit sur openrouter.ai)
TAVILY_API_KEY=...                 # pour la collecte (gratuit sur app.tavily.com)
```

### 4. Lancer l'application

```bash
streamlit run app.py
```

L'application s'ouvre sur `http://localhost:8501`

---

## Structure du projet

```
app.py                  Point d'entrée Streamlit
stageradar/
  config.py             Configuration centrale
  database.py           Base SQLite
  cleaning.py           Nettoyage des données
  analytics.py          Analyses et statistiques
  filters.py            Filtres sidebar
  cv_render.py          Export PDF du CV
  gmail_scan.py         Connexion IMAP Gmail
  classification.py     Classification des e-mails
  ai/
    llm.py              Client OpenRouter / Anthropic
    cv.py               Agent CV (analyse → rédaction → export)
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
scripts/
  collect_agences.py    Collecte via Tavily
  clean_data.py         Nettoyage
  explore.py            Génération des figures
```

---

## Stack technique

| Composant | Technologie |
|---|---|
| Interface | Streamlit |
| Base de données | SQLite (sqlite3) |
| Analyse des données | pandas |
| Visualisations | Plotly, pydeck |
| Agent IA | OpenRouter (Gemma, Nemotron) |
| Export CV | reportlab (PDF) |
| Collecte web | Tavily API |
| Scan e-mail | IMAP / Gmail |

---

## Déploiement

La plateforme est déployée sur **Railway (Docker)** :  
👉 [https://ntic-radar-marrakech-production.up.railway.app](https://ntic-radar-marrakech-production.up.railway.app)

---

## Auteur

**Ayoub Aamire** — AI201
