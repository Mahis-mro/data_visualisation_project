"""Check that the cleaning code rebuilds the committed cleaned CSV exactly.

    python scripts/check_clean.py

Reads data/raw/export_alimconfiance.csv, applies utils.prep.clean_raw in memory and
compares every column with data/alimconfiance_clean.csv. Nothing is written.
Exit code 0 = identical, 1 = differences (or missing file).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from utils import constants as C  # noqa: E402
from utils.prep import clean_raw  # noqa: E402


def same_column(new: pd.Series, old: pd.Series, name: str) -> pd.Series:
    both_missing = new.isna() & old.isna()          # missing == missing, whatever the dtype
    if name in ("latitude", "longitude"):
        return both_missing | ((new - old).abs() < 1e-9)
    if name == "unfavorable":
        return new.astype(bool) == old.astype(bool)
    if name == "Date_inspection":
        return both_missing | (new == old)
    return both_missing | (new.astype(str) == old.astype(str))


def main() -> int:
    for path in (C.RAW_PATH, C.CLEAN_PATH):
        if not path.exists():
            print(f"Missing file: {path}")
            return 1
    raw = pd.read_csv(C.RAW_PATH, sep=";", low_memory=False)
    rebuilt = clean_raw(raw).reset_index(drop=True)
    shipped = pd.read_csv(
        C.CLEAN_PATH, sep=";", encoding="utf-8-sig", parse_dates=["Date_inspection"]
    )
    print(f"raw {raw.shape} -> rebuilt {rebuilt.shape} | committed {shipped.shape}")
    if rebuilt.shape != shipped.shape or list(rebuilt.columns) != list(shipped.columns):
        print("Shape or columns differ.")
        return 1
    total = 0
    for col in shipped.columns:
        diff = int((~same_column(rebuilt[col], shipped[col], col)).sum())
        total += diff
        print(f"  {col:38s} {'OK' if diff == 0 else f'{diff} differences'}")
    print("IDENTICAL" if total == 0 else f"{total} differences in total")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
