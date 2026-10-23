"""Data access: download (with cache), build the clean file, load it for the app."""
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from utils import constants as C
from utils.prep import build_quality_report, clean_raw

API = "https://www.data.gouv.fr/api/1"
HEADERS = {"User-Agent": "efrei-streamlit-student-project/1.0"}


def _get_json(url: str) -> dict:
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=60) as r:
        return json.load(r)


def _csv_resources(dataset: dict):
    for res in dataset.get("resources", []):
        text = f"{res.get('title', '')} {res.get('url', '')}".lower()
        if (res.get("format") or "").lower() == "csv" and "export" in text:
            yield res


def discover_csv_url() -> str:
    """Find the export CSV through the data.gouv.fr API (URL is not hard-coded:
    the publisher moves resources between datasets, e.g. during maintenance)."""
    try:
        for res in _csv_resources(_get_json(f"{API}/datasets/{C.DATASET_ID}/")):
            return res["url"]
    except Exception as exc:  # fall through to the search API
        print(f"Main dataset lookup failed: {exc}")
    query = urllib.parse.quote(C.DATASET_SEARCH_QUERY)
    for ds in _get_json(f"{API}/datasets/?q={query}&page_size=10").get("data", []):
        for res in _csv_resources(ds):
            return res["url"]
    raise RuntimeError(
        "Could not locate the export CSV on data.gouv.fr. Download it manually "
        f"from {C.DATASET_URL} and save it as {C.RAW_PATH}."
    )


def _download(url: str, dest):
    """Stream `url` to `dest`; transparently un-gzip (the portal may serve .csv.gz)."""
    import gzip
    import shutil
    import tempfile

    req = urllib.request.Request(url, headers={**HEADERS, "Accept-Encoding": "identity"})
    with tempfile.NamedTemporaryFile(delete=False, suffix=".part") as tmp:
        tmp_path = tmp.name
        with urllib.request.urlopen(req, timeout=300) as r:
            shutil.copyfileobj(r, tmp, length=1 << 20)
    try:
        with open(tmp_path, "rb") as f:
            is_gzip = f.read(2) == b"\x1f\x8b"
        if is_gzip:
            with gzip.open(tmp_path, "rb") as src, open(dest, "wb") as out:
                shutil.copyfileobj(src, out, length=1 << 20)
        else:
            shutil.move(tmp_path, dest)
    finally:
        import os
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def fetch_and_cache(url: str | None = None, force: bool = False):
    """Download the raw export once; later calls reuse the cached file.

    The file is only replaced once the download (and decompression) succeeded,
    so a failed refresh never destroys a good cached copy.
    """
    if C.RAW_PATH.exists() and not force:
        return C.RAW_PATH
    url = url or discover_csv_url()
    C.RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {url}")
    _download(url, C.RAW_PATH)
    C.RAW_META_PATH.write_text(json.dumps({
        "url": url,
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }, indent=2))
    return C.RAW_PATH


def build_clean_files(force_download: bool = False, url: str | None = None):
    """raw CSV -> cleaned CSV + quality_report.json (run via scripts/build_data.py)."""
    raw_path = fetch_and_cache(url=url, force=force_download)
    raw = pd.read_csv(raw_path, sep=";", low_memory=False)
    clean = clean_raw(raw)
    clean.to_csv(C.CLEAN_PATH, sep=";", index=False, encoding="utf-8-sig")
    C.QUALITY_PATH.write_text(json.dumps(build_quality_report(raw, clean), indent=2))
    print(f"Raw {raw.shape} -> clean {clean.shape}")
    return clean


@st.cache_data(show_spinner="Loading inspections...")
def load_data() -> pd.DataFrame:
    """Read the cleaned CSV (built from the raw export if it is missing)."""
    if not C.CLEAN_PATH.exists():
        build_clean_files()
    df = pd.read_csv(
        C.CLEAN_PATH, sep=";", encoding="utf-8-sig", parse_dates=["Date_inspection"]
    )
    if df["unfavorable"].dtype != bool:
        mapping = {"true": True, "false": False, "1": True, "0": False}
        norm = df["unfavorable"].astype(str).str.strip().str.lower()
        if not norm.isin(mapping).all():
            raise ValueError("Invalid values in 'unfavorable' column.")
        df["unfavorable"] = norm.map(mapping).astype(bool)
    return df


@st.cache_data(show_spinner=False)
def load_quality_report() -> dict | None:
    """Raw-vs-clean figures saved at build time (None if the file is absent)."""
    if C.QUALITY_PATH.exists():
        return json.loads(C.QUALITY_PATH.read_text())
    return None


@st.cache_data(show_spinner=False)
def load_download_info() -> dict | None:
    if C.RAW_META_PATH.exists():
        return json.loads(C.RAW_META_PATH.read_text())
    return None
