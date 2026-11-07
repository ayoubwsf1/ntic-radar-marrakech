"""Exploration des données : statistiques et figures (docs/figures/*.png) à partir de data/agences_maroc.xlsx.

    python -m scripts.explore
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from stageradar import analytics
from stageradar.config import FIGURES_DIR, VILLE_CIBLE, XLSX_PATH

TERRACOTTA, OCRE, SOMBRE = "#B85042", "#C9962B", "#2B1B17"


def _barh(serie: pd.Series, titre: str, fichier: str, couleur: str = TERRACOTTA) -> None:
    fig, ax = plt.subplots(figsize=(7, 4))
    s = serie.sort_values()
    ax.barh(s.index.astype(str), s.values, color=couleur)
    for y, v in enumerate(s.values):
        ax.text(v + max(s.values) * 0.01, y, str(int(v)), va="center", fontsize=9, color=SOMBRE)
    ax.set_title(titre, loc="left", fontsize=12, fontweight="bold", color=SOMBRE)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / fichier, dpi=150)
    plt.close(fig)


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_excel(XLSX_PATH, sheet_name="Agences").fillna("")
    df = df.rename(columns={"Nom": "nom", "Type": "type", "Ville": "ville", "Taille": "taille",
                            "Services": "services", "Site web": "site", "Source": "source", "Statut": "statut"})

    print(f"{len(df)} lignes · {df['ville'].nunique()} villes · {df['type'].nunique()} types")
    _barh(analytics.compter(df, "ville", 10), "Agences par ville (top 10)", "agences_par_ville.png")
    _barh(analytics.compter(df, "type"), "Agences par type", "agences_par_type.png", OCRE)
    _barh(analytics.compter(df, "source"), "Sources de collecte", "sources.png", SOMBRE)
    m = df[df["ville"] == VILLE_CIBLE]
    _barh(analytics.compter(m, "type"), f"{VILLE_CIBLE} : agences par type", "marrakech_par_type.png")
    _barh(analytics.mots_services(df, 12), "Termes fréquents dans les services", "services_termes.png", OCRE)

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

    print("\nComplétude (%) :")
    print(analytics.qualite(df).to_string(index=False))
    print(f"\n{VILLE_CIBLE} : {len(m)} agences ({len(m) / len(df):.1%})")
    print(f"✅ Figures écrites dans {FIGURES_DIR}")


if __name__ == "__main__":
    main()
