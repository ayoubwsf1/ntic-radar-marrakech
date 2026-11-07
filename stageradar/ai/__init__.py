"""Couche d'intelligence artificielle de Ntic Radar.

- cv.py        : agent CV (analyse -> rédaction LLM -> vérification anti-invention), repli local sans clé
- profile.py   : profil du candidat, stocké en base
- email_ai.py  : classification des e-mails (règles + LLM en option)
- llm.py       : client minimal de l'API Anthropic (clé facultative)

Principe : tout fonctionne sans clé API grâce à des méthodes locales ;
le LLM améliore la qualité quand ANTHROPIC_API_KEY est définie.
"""
