"""Nettoie un fichier Excel d'agences et écrit le résultat + un rapport.

Usage :
    python -m scripts.clean_data                      # data/raw -> data/cleaned
    python -m scripts.clean_data entree.xlsx sortie.xlsx
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from stageradar.cleaning import nettoyer
from stageradar.config import CLEAN_XLSX_PATH, RAW_XLSX_PATH


def main(src: Path = RAW_XLSX_PATH, dst: Path = CLEAN_XLSX_PATH) -> None:
    df = pd.read_excel(src, sheet_name=0)
    propre, rap = nettoyer(df)
    dst.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(dst) as xw:
        propre.to_excel(xw, sheet_name="Agences", index=False)
        rap.to_frame().to_excel(xw, sheet_name="Rapport", index=False)
    print(rap.to_frame().to_string(index=False))
    print(f"\n✅ {len(propre)} agences écrites dans {dst}")


if __name__ == "__main__":
    args = [Path(a) for a in sys.argv[1:]]
    main(*args) if args else main()
