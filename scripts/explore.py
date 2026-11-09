# ==============================================================================
# Script : explore.py
# Rôle : Analyse exploratoire des données : générer les graphiques statistiques
#        enregistrés en images PNG dans docs/figures/.
# ==============================================================================

# Permet d'utiliser les annotations de type modernes
from __future__ import annotations

# Module Matplotlib pour dessiner des graphiques
import matplotlib

# Utiliser le moteur "Agg" pour générer les images sans ouvrir de fenêtre à l'écran
matplotlib.use("Agg")
# Module Pyplot pour créer les figures et les axes
import matplotlib.pyplot as plt
# Bibliothèque Pandas pour manipuler le tableau des données
import pandas as pd

# Importer les fonctions de calcul statistique depuis stageradar
from stageradar import analytics
# Importer le dossier de sortie des figures, la ville cible (Marrakech) et le chemin Excel
from stageradar.config import FIGURES_DIR, VILLE_CIBLE, XLSX_PATH

# Palette de couleurs
TERRACOTTA, OCRE, SOMBRE = "#B85042", "#C9962B", "#2B1B17"


# ------------------------------------------------------------------------------
# Fonction interne : _barh
# Rôle : Dessiner un graphique à barres horizontales et l'enregistrer en image PNG.
# Paramètres :
#   - serie : les données à afficher (valeurs et libellés)
#   - titre : le titre du graphique
#   - fichier : le nom du fichier image (ex: "agences_par_ville.png")
#   - couleur : la couleur des barres
# ------------------------------------------------------------------------------
def _barh(serie: pd.Series, titre: str, fichier: str, couleur: str = TERRACOTTA) -> None:
    # Créer une nouvelle figure avec une taille de 7x4 pouces
    fig, ax = plt.subplots(figsize=(7, 4))
    # Trier les valeurs de la plus petite à la plus grande
    s = serie.sort_values()
    # Dessiner les barres horizontales
    ax.barh(s.index.astype(str), s.values, color=couleur)
    # Ajouter le nombre exact au bout de chaque barre
    for y, v in enumerate(s.values):
        ax.text(v + max(s.values) * 0.01, y, str(int(v)), va="center", fontsize=9, color=SOMBRE)
    # Définir le titre du graphique aligné à gauche en gras
    ax.set_title(titre, loc="left", fontsize=12, fontweight="bold", color=SOMBRE)
    # Supprimer les bordures du haut et de droite pour un style moderne et épuré
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    # Ajuster automatiquement les marges de l'image
    fig.tight_layout()
    # Enregistrer l'image dans le dossier docs/figures/ avec une résolution de 150 DPI
    fig.savefig(FIGURES_DIR / fichier, dpi=150)
    # Fermer la figure pour libérer la mémoire de l'ordinateur
    plt.close(fig)


# ------------------------------------------------------------------------------
# Fonction principale : main
# Rôle : Charger les données Excel, calculer les statistiques et créer tous
#        les graphiques du projet.
# ------------------------------------------------------------------------------
def main() -> None:
    # 1. Créer le dossier docs/figures/ s'il n'existe pas encore
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Lire la feuille "Agences" du fichier Excel et remplacer les cases vides
    df = pd.read_excel(XLSX_PATH, sheet_name="Agences").fillna("")

    # 3. Renommer les colonnes en minuscules pour faciliter la manipulation
    df = df.rename(columns={
        "Nom": "nom", "Type": "type", "Ville": "ville", "Taille": "taille",
        "Services": "services", "Site web": "site", "Source": "source", "Statut": "statut"
    })

    # 4. Afficher un résumé textuel dans la console
    print(f"{len(df)} lignes · {df['ville'].nunique()} villes · {df['type'].nunique()} types")

    # 5. Graphique 1 : Top 10 des villes avec le plus d'agences
    _barh(analytics.compter(df, "ville", 10), "Agences par ville (top 10)", "agences_par_ville.png")

    # 6. Graphique 2 : Répartition des agences par secteur d'activité
    _barh(analytics.compter(df, "type"), "Agences par type", "agences_par_type.png", OCRE)

    # 7. Graphique 3 : Provenance des données (Tavily, Annuaires, etc.)
    _barh(analytics.compter(df, "source"), "Sources de collecte", "sources.png", SOMBRE)

    # 8. Graphique 4 : Focus sur la ville de Marrakech (répartition par type)
    m = df[df["ville"] == VILLE_CIBLE]
    _barh(analytics.compter(m, "type"), f"{VILLE_CIBLE} : agences par type", "marrakech_par_type.png")

    # 9. Graphique 5 : Mots les plus fréquents dans la description des services
    _barh(analytics.mots_services(df, 12), "Termes fréquents dans les services", "services_termes.png", OCRE)

    # 10. Graphique 6 : Tableau croisé villes x types (barres empilées)
    croise = analytics.croiser_ville_type(df, 6)
    ax = croise.plot(kind="bar", stacked=True, figsize=(8, 4.2), color=[TERRACOTTA, OCRE, SOMBRE, "#7a8a6a"])
    ax.set_title("Villes × types d'agence", loc="left", fontsize=12, fontweight="bold", color=SOMBRE)
    ax.set_xlabel("")
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.legend(frameon=False, fontsize=8)
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "ville_x_type.png", dpi=150)
    plt.close()

    # 11. Afficher l'analyse du taux de remplissage des colonnes (qualité des données)
    print("\nComplétude (%) :")
    print(analytics.qualite(df).to_string(index=False))

    # 12. Afficher la part de Marrakech dans l'ensemble du jeu de données
    print(f"\n{VILLE_CIBLE} : {len(m)} agences ({len(m) / len(df):.1%})")
    print(f"✅ Figures écrites dans {FIGURES_DIR}")


# Point d'entrée : s'exécute quand on lance le script depuis le terminal
if __name__ == "__main__":
    main()
