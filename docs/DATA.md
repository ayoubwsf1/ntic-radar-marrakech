# Données

## Jeux de données

| Fichier | Contenu |
|---|---|
| `data/raw/agences_maroc_avant_nettoyage.xlsx` | 74 lignes brutes (feuille « Brut »), 6 colonnes |
| `data/cleaned/agences_apres_nettoyage.xlsx` | Sortie de `python -m scripts.clean_data` (feuilles « Agences » et « Rapport ») |
| `data/cleaned/agences_apres_nettoyage_initial.xlsx` | Version obtenue lors du premier nettoyage manuel (65 lignes) |
| `data/agences_maroc.xlsx` | Jeu utilisé par l'application : 229 lignes, 20 villes |

## Dictionnaire (feuille « Agences »)

| Colonne | Description |
|---|---|
| N° | Identifiant de ligne |
| Nom | Nom de l'agence |
| Type | Web & Développement · Marketing digital · Design & Créa · Publicité & Com |
| Ville | Ville (liste de 20 villes avec coordonnées) |
| Taille | Tranche d'effectif (2-9, 10-49…) — renseignée à environ 27 % |
| Services | Description des services |
| Site web | URL normalisée `https://domaine` |
| Source | Recherche web (Tavily), Clutch.co (Maroc), Site officiel |
| Latitude / Longitude | Centre de la ville (pas l'adresse exacte) |
| Statut | Non encore postulé · Entretien · Accepté · Refusé |
| Notes | Commentaires libres |

## Problèmes détectés et solutions (fichier brut, 74 lignes)

| Problème | Solution Python | Occurrences |
|---|---|---|
| En-têtes avec espaces ou casse variable (`nom `, `TYPE`, `Statut `) | `normaliser_colonnes` | 5 |
| Villes en minuscules ou sans accent (`casablanca`, `fes`) | table de correspondance `_VILLES` | 11 |
| Types écrits de plusieurs façons | table `_TYPES` | 8 |
| Sources hétérogènes (`GMaps`, `google maps`) | table `_SOURCES` | 33 |
| URL en majuscules, avec `www`, chemin ou slash final | `normaliser_site` | 42 |
| Statuts invalides (`NON POSTULE`, `A postuler`, `test`, vides) | ramenés à « Non encore postulé » | 30 |
| Doublons (même domaine ou même nom) | `drop_duplicates` | 6 |
| Lignes de test | suppression | 1 |
| Sites manquants | conservés, signalés dans Notes | 4 |
| Coordonnées manquantes | centre de la ville | 67 |

Résultat : **74 → 67 lignes**. Le rapport complet est régénéré à chaque exécution du script.

## Exploration

`python -m scripts.explore` produit les statistiques et les figures de `docs/figures/` à partir de `data/agences_maroc.xlsx` :
229 lignes, 20 villes, 4 types ; Marrakech compte 26 agences (11,4 %), 2ᵉ ville après Casablanca (54) ; la complétude est de 100 % sauf la taille (27,5 %).
