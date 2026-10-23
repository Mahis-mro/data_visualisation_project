"""Cleaning, validation, feature engineering and filtering."""
import pandas as pd

from utils.constants import RATING_ORDER, UNFAVORABLE_RATINGS

RAW_COLUMNS = [
    "Numero_inspection", "SIRET", "APP_Libelle_etablissement",
    "APP_Libelle_activite_etablissement", "Synthese_eval_sanit",
    "Date_inspection", "Contexte_inspection", "reg_name", "dep_name",
    "com_name", "Code_postal", "geores",
]
UNKNOWN_FILL_COLUMNS = [
    "APP_Libelle_activite_etablissement", "reg_name", "dep_name", "com_name",
]


def clean_raw(raw: pd.DataFrame) -> pd.DataFrame:
    """Raw Alim'confiance export -> analysis-ready table (same rules as the notebook)."""
    missing_cols = [c for c in RAW_COLUMNS if c not in raw.columns]
    if missing_cols:
        raise ValueError(
            f"Raw file is missing expected columns {missing_cols}. The portal export may "
            "use column labels instead of field names (check the CSV header), or the "
            "separator is not ';'."
        )
    df = raw[RAW_COLUMNS].copy()
    # An inspection without rating cannot be analysed.
    df = df.dropna(subset=["Synthese_eval_sanit"]).copy()
    df[UNKNOWN_FILL_COLUMNS] = df[UNKNOWN_FILL_COLUMNS].fillna("Unknown")
    df["Date_inspection"] = pd.to_datetime(
        df["Date_inspection"].astype(str).str[:10], errors="coerce"
    )
    coords = df["geores"].astype("string").str.split(",", n=1, expand=True)
    if coords.shape[1] < 2:           # no coordinate at all
        coords[1] = pd.NA
    df["latitude"] = pd.to_numeric(coords[0], errors="coerce")
    df["longitude"] = pd.to_numeric(coords[1], errors="coerce")
    # Out-of-range coordinates are treated as missing.
    bad = ~df["latitude"].between(-90, 90) | ~df["longitude"].between(-180, 180)
    df.loc[bad, ["latitude", "longitude"]] = float("nan")
    # Feature engineering: binary target used by every KPI.
    df["unfavorable"] = df["Synthese_eval_sanit"].isin(UNFAVORABLE_RATINGS)
    return df


def build_quality_report(raw: pd.DataFrame, clean: pd.DataFrame) -> dict:
    """Raw-vs-clean figures that cannot be recomputed from the clean file alone."""
    raw_missing = raw[RAW_COLUMNS].isna().sum()
    return {
        "raw_rows": int(len(raw)),
        "raw_columns": int(raw.shape[1]),
        "raw_duplicate_rows": int(raw.duplicated().sum()),
        "raw_duplicate_ids": int(raw["Numero_inspection"].duplicated().sum()),
        "raw_missing_by_column": {k: int(v) for k, v in raw_missing.items() if v > 0},
        "clean_rows": int(len(clean)),
        "clean_columns": int(clean.shape[1]),
        "removed_rows": int(len(raw) - len(clean)),
        "removed_reason": "Missing sanitary evaluation (Synthese_eval_sanit)",
    }


def validation_checks(df: pd.DataFrame) -> pd.DataFrame:
    """Live validation checks on the cleaned data (each returns a count; 0 = pass)."""
    checks = [
        ("Duplicate inspection IDs", int(df["Numero_inspection"].duplicated().sum()), True),
        ("Missing inspection dates", int(df["Date_inspection"].isna().sum()), True),
        ("Missing sanitary ratings", int(df["Synthese_eval_sanit"].isna().sum()), True),
        ("Unexpected rating categories",
         int((~df["Synthese_eval_sanit"].isin(RATING_ORDER)).sum()), True),
        ("Dates in the future", int((df["Date_inspection"] > pd.Timestamp.today()).sum()), True),
        ("Coordinates outside France + overseas bounding box",
         int((df["latitude"].notna() & ~df["latitude"].between(-22, 52)).sum()), True),
        ("Missing coordinates (kept; excluded from the map only)",
         int(df["latitude"].isna().sum()), False),
        ("Unknown region (kept in national KPIs; excluded from regional charts)",
         int((df["reg_name"] == "Unknown").sum()), False),
    ]
    out = pd.DataFrame(checks, columns=["Check", "Count", "Must be zero"])
    out["Status"] = out.apply(
        lambda r: ("Pass" if r["Count"] == 0 else "FAIL") if r["Must be zero"]
        else ("None" if r["Count"] == 0 else "Documented limitation"),
        axis=1,
    )
    out["Share of inspections (%)"] = (out["Count"] / len(df) * 100).round(2)
    return out[["Check", "Count", "Share of inspections (%)", "Status"]]


def missingness_table(df: pd.DataFrame) -> pd.DataFrame:
    """Per-column missing and 'Unknown' counts."""
    rows = []
    for col in df.columns:
        missing = int(df[col].isna().sum())
        unknown = int((df[col] == "Unknown").sum()) if df[col].dtype == object else 0
        rows.append((col, missing, unknown))
    t = pd.DataFrame(rows, columns=["Column", "Missing", "'Unknown' label"])
    t["Affected (%)"] = ((t["Missing"] + t["'Unknown' label"]) / len(df) * 100).round(2)
    return t.sort_values("Affected (%)", ascending=False).reset_index(drop=True)


def group_stats(df: pd.DataFrame, by: str) -> pd.DataFrame:
    """Inspections, unfavorable count and unfavorable rate (%) per group."""
    out = (
        df.groupby(by)
        .agg(
            total_inspections=("Numero_inspection", "count"),
            unfavorable_inspections=("unfavorable", "sum"),
            unfavorable_rate=("unfavorable", "mean"),
        )
        .reset_index()
    )
    out["unfavorable_rate"] *= 100
    return out


def filter_data(df, selected_regions, selected_activities, selected_contexts, date_range):
    """Apply sidebar filters without modifying the original dataset."""
    mask = pd.Series(True, index=df.index)
    if selected_regions:
        mask &= df["reg_name"].isin(selected_regions)
    if selected_activities:
        mask &= df["APP_Libelle_activite_etablissement"].isin(selected_activities)
    if selected_contexts:
        mask &= df["Contexte_inspection"].isin(selected_contexts)
    if len(date_range) == 2:
        start, end = date_range
        mask &= df["Date_inspection"].dt.date.between(start, end)
    return df[mask]
