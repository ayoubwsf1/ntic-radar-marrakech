# ==============================================================================
# Script : clean_data.py
# Rôle : Nettoyer un fichier Excel d'agences brut et générer un fichier propre
#        accompagné d'un rapport de corrections.
# ==============================================================================

# Permet d'utiliser les annotations de type modernes
from __future__ import annotations

# Module système pour lire les arguments de la ligne de commande
import sys
# Module pour manipuler les chemins de fichiers (dossiers et fichiers)
from pathlib import Path

# Bibliothèque Pandas pour la manipulation et l'analyse de données tabulaires
import pandas as pd

# Importer la fonction principale de nettoyage depuis stageradar
from stageradar.cleaning import nettoyer
# Importer les chemins par défaut des fichiers Excel brut et nettoyé
from stageradar.config import CLEAN_XLSX_PATH, RAW_XLSX_PATH


# ------------------------------------------------------------------------------
# Fonction principale : main
# Paramètres :
#   - src : chemin du fichier Excel brut en entrée (par défaut data/raw/...)
#   - dst : chemin du fichier Excel nettoyé en sortie (par défaut data/cleaned/...)
# ------------------------------------------------------------------------------
def main(src: Path = RAW_XLSX_PATH, dst: Path = CLEAN_XLSX_PATH) -> None:
    # 1. Lire la première feuille du fichier Excel brut avec pandas
    df = pd.read_excel(src, sheet_name=0)

    # 2. Appliquer tout l'algorithme de nettoyage
    #    'propre' contient le tableau nettoyé
    #    'rap' contient le rapport avec le compteur des corrections
    propre, rap = nettoyer(df)

    # 3. Créer le dossier de destination s'il n'existe pas encore
    dst.parent.mkdir(parents=True, exist_ok=True)

    # 4. Écrire les résultats dans un nouveau fichier Excel avec deux feuilles
    with pd.ExcelWriter(dst) as xw:
        # Première feuille : la liste des agences nettoyées
        propre.to_excel(xw, sheet_name="Agences", index=False)
        # Deuxième feuille : le rapport des opérations effectuées
        rap.to_frame().to_excel(xw, sheet_name="Rapport", index=False)

    # 5. Afficher le rapport textuel dans le terminal
    print(rap.to_frame().to_string(index=False))

    # 6. Afficher un message de confirmation avec le nombre d'agences enregistrées
    print(f"\n✅ {len(propre)} agences écrites dans {dst}")


# Point d'entrée : s'exécute quand on lance le script directement depuis le terminal
if __name__ == "__main__":
    # Récupérer les chemins optionnels passés dans le terminal (s'il y en a)
    args = [Path(a) for a in sys.argv[1:]]
    # Lancer la fonction avec les arguments fournis, sinon avec les chemins par défaut
    main(*args) if args else main()
