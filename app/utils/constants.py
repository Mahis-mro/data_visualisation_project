"""Project-wide constants (single place for seeds, thresholds, palette, paths)."""
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = APP_DIR / "data"
RAW_PATH = DATA_DIR / "raw" / "export_alimconfiance.csv"
RAW_META_PATH = DATA_DIR / "raw" / "download_info.json"
CLEAN_PATH = DATA_DIR / "alimconfiance_clean.csv"
QUALITY_PATH = DATA_DIR / "quality_report.json"

# Reproducibility
SEED = 42                 # random_state used to sample map points
MAP_MAX_POINTS = 5000     # max points drawn on the map
MIN_GROUP_SIZE = 100      # min inspections for a rate to be ranked

# data.gouv.fr
DATASET_ID = "5593aab9c751df35d8a453ba"   # Alim'confiance main dataset
DATASET_SEARCH_QUERY = "alimconfiance export"
DATASET_URL = (
    "https://www.data.gouv.fr/datasets/"
    "resultats-des-controles-officiels-sanitaires-dispositif-dinformation-alimconfiance"
)

# Ratings
RATING_ORDER = [
    "Très satisfaisant",
    "Satisfaisant",
    "A améliorer",
    "A corriger de manière urgente",
]
UNFAVORABLE_RATINGS = ["A améliorer", "A corriger de manière urgente"]

# Colour palette (all >= 3:1 contrast against white for graphical objects)
RATING_COLORS = {
    "Très satisfaisant": "#1B6F68",
    "Satisfaisant": "#3A6EA5",
    "A améliorer": "#B86E00",
    "A corriger de manière urgente": "#B3261E",
}
BAR_COLOR = "#3A6EA5"
FULL_MONTH_COLOR = "#3A6EA5"
PARTIAL_MONTH_COLOR = "#767676"
REFERENCE_COLOR = "#333333"

# Author header
AUTHOR_NAME = "MATHIS MOREAU"
LINKEDIN_URL = "https://www.linkedin.com/in/mathis-moreau-efrei"
PROFESSOR_NAME = "Mano Joseph MATHEW"
COURSE_TAG = "Data Storytelling Project 2026"
LOGO_CANDIDATES = [APP_DIR / "assets" / f"efrei_logo.{ext}" for ext in ("png", "jpg", "jpeg", "svg", "webp")]
