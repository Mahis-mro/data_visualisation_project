"""Download the Alim'confiance export (cached) and build the cleaned CSV.

    python scripts/build_data.py            # use cached raw file if present
    python scripts/build_data.py --refresh  # re-download from data.gouv.fr
    python scripts/build_data.py --url URL  # use a specific CSV URL
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.io import build_clean_files  # noqa: E402

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--refresh", action="store_true", help="re-download the raw CSV")
    p.add_argument("--url", help="explicit CSV URL (skips API discovery)")
    args = p.parse_args()
    build_clean_files(force_download=args.refresh, url=args.url)
