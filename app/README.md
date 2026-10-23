# Behind the Kitchen Door: How Safe Is Our Food?

**Interactive data storytelling with Streamlit — French food safety inspections**

This project explores official sanitary inspection results published through **Alim'confiance**. Its intended audience is the general public, especially consumers and students interested in food safety. Rather than claiming to rank every food establishment in France, the dashboard examines patterns **among the inspections recorded in the dataset**.

The story answers the following questions:

1. How frequently do inspections result in favorable or unfavorable sanitary evaluations?
2. How do results differ between establishment activities and inspection contexts?
3. How do inspection counts and unfavorable rates vary across French regions?
4. Where are geolocated inspections recorded?
5. How do inspection volumes and outcomes change over time, and what are the limitations of these comparisons?

## 1. Data source and attribution

| Item | Details |
|---|---|
| Dataset | *Résultats des contrôles officiels sanitaires — dispositif d'information Alim'confiance* |
| Publisher | French Ministry of Agriculture |
| Portal | [data.gouv.fr — official dataset](https://www.data.gouv.fr/datasets/resultats-des-controles-officiels-sanitaires-dispositif-dinformation-alimconfiance) |
| Licence | Licence Ouverte / Open Licence — attribution required |
| Source FAQ | [Alim'confiance FAQ](https://alimconfiance.agriculture.gouv.fr/faq) |
| Extraction date | **22 October 2026**, according to the `Date_extraction` field of the raw CSV (71,325 non-null entries) |
| Actual download date | Not recorded for the committed file; new downloads write `data/raw/download_info.json` |
| Inspection dates covered | **23 October 2025 – 21 October 2026** (inclusive) |

**Attribution:** Alim'confiance — French Ministry of Agriculture — data.gouv.fr — Licence Ouverte / Open Licence.

This is a **dated snapshot** of a regularly updated public dataset. Downloading the source again may result in different inspection records or totals; the CSV files included in this project are the reference for all figures below.

## 2. Dataset preparation

The raw export, `app/data/raw/export_alimconfiance.csv` (included in the submission zip; git-ignored in the repository, where it is rebuilt by `scripts/build_data.py`), contains **71,326 inspections and 53 columns**. During preparation, relevant variables are selected, inspection dates and geographic coordinates are parsed, missing labels are handled, and key data-quality checks are performed.

**One record with no sanitary evaluation was excluded.** The processed file, `app/data/alimconfiance_clean.csv`, contains **71,325 inspections and 15 columns** and is the file loaded by Streamlit.

The derived Boolean column `unfavorable` equals `True` for either of these official sanitary evaluation categories:

- `A améliorer`
- `A corriger de manière urgente`

`Très satisfaisant` and `Satisfaisant` are treated as favorable. Rates always use the number of **recorded inspections in the relevant group** as their denominator. Multiple inspections can concern the same establishment.

### Data dictionary — cleaned CSV

| Column | Description |
|---|---|
| `Numero_inspection` | Unique inspection identifier in the analyzed extract |
| `SIRET` | Establishment SIRET identifier |
| `APP_Libelle_etablissement` | Establishment name |
| `APP_Libelle_activite_etablissement` | Establishment activity label |
| `Synthese_eval_sanit` | Official sanitary evaluation category |
| `Date_inspection` | Date of inspection |
| `Contexte_inspection` | Inspection context/reason |
| `reg_name` | Region name, or `Unknown` if unavailable |
| `dep_name` | Department name, or `Unknown` if unavailable |
| `com_name` | Municipality name, or `Unknown` if unavailable |
| `Code_postal` | Postal code |
| `geores` | Original geographic coordinate text |
| `latitude` | Parsed latitude, in decimal degrees |
| `longitude` | Parsed longitude, in decimal degrees |
| `unfavorable` | Boolean indicator for evaluations requiring improvement or urgent correction |

## 3. Main findings from this snapshot

| Indicator | Result |
|---|---:|
| Recorded inspections after cleaning | **71,325** |
| Favorable sanitary evaluations | **66,815 (93.68%)** |
| Unfavorable sanitary evaluations | **4,510 (6.32%)** |
| Restaurant inspections | **33,165** |
| Unfavorable restaurant inspections | **2,194 (6.62%)** |
| Unfavorable rate — bakeries/pastry shops | **9.01%** |
| Unfavorable rate — butcher shops | **8.47%** |
| Unfavorable rate — complaints/reports | **19.98%** |
| Unfavorable rate — scheduled inspections | **6.90%** |
| Unfavorable rate — follow-up inspections | **1.54%** |
| Unfavorable rate — September 2026 | **15.47%** |

These figures describe the **complete analyzed snapshot**, not the currently selected dashboard filters. They should not be interpreted as the proportion of all food establishments that are unsafe, nor as evidence that an inspection context, region, or activity causes an unfavorable outcome.

## 4. Project structure

```text
data_visu_project/
├── project_data_visu.ipynb            # Exploration, cleaning and EDA (kept separately)
└── app/
    ├── app.py                         # Streamlit entry point and sidebar filters
    ├── README.md  requirements.txt  Makefile  .gitignore
    ├── scripts/
    │   └── build_data.py              # download (cached) + clean + quality report
    ├── data/
    │   ├── alimconfiance_clean.csv    # processed data read by Streamlit (committed)
    │   ├── quality_report.json        # raw-vs-clean figures written by build_data.py
    │   └── raw/                       # raw export (in the zip, git-ignored in the repo) + download_info.json
    ├── sections/
    │   ├── header.py                  # logo, author name, LinkedIn link, title
    │   ├── intro.py                   # chapter 1: hook, key numbers, story outline, source
    │   ├── overview.py                # KPI row (always visible) with deltas vs all inspections
    │   ├── deep_dives.py              # chapters 2-3: six analyses, 7 charts, headline per analysis
    │   └── conclusions.py             # chapter 4 findings + implications, chapter 5 quality + limits
    ├── utils/
    │   ├── constants.py               # seed, thresholds, palette, paths
    │   ├── io.py                      # fetch_and_cache(), build_clean_files(), load_data()
    │   ├── prep.py                    # clean_raw(), validation_checks(), filters, group_stats()
    │   └── viz.py                     # plot_chart() with text alternative, reference lines
    └── assets/                        # reserved for optional visual assets
```

The cleaning rules exist in `utils/prep.py::clean_raw`. On the 22 October 2026 extraction
(71,326 raw rows) they rebuild the committed `alimconfiance_clean.csv` with no difference in any of
the 15 columns. Anyone can re-check this with `python scripts/check_clean.py` (needs the raw file in
`data/raw/`). A fresh download may differ because the portal data is a rolling window. The notebook
remains the exploratory record.

## 5. Installation and launch

Requires **Python 3.11+** (pandas 3). Dependencies are pinned in `requirements.txt`
(`streamlit==1.66.1`, `pandas==3.0.2`, `plotly==7.1.0`).

```bash
cd app
python -m pip install -r requirements.txt
python -m streamlit run app.py        # or: make install && make run
```

Open the local URL displayed by Streamlit (usually `http://localhost:8501`). The cleaned CSV is
committed, so the app runs from a clean checkout without downloading anything. An internet
connection is only needed for the OpenStreetMap basemap.

### Rebuilding the data from the source

```bash
python scripts/build_data.py            # uses data/raw/ if cached, otherwise downloads
python scripts/build_data.py --refresh  # force a new download from data.gouv.fr
python scripts/build_data.py --url URL  # use an explicit CSV URL
python scripts/check_clean.py           # rebuild in memory and compare with the committed CSV
```

The script finds the export CSV through the data.gouv.fr API instead of hard-coding a file URL,
saves it in `data/raw/` with a `download_info.json` (URL + UTC download time), then writes
`alimconfiance_clean.csv` and `quality_report.json`. If the cleaned CSV is missing, the app
calls the same function at start-up.

> **Note.** When this README was updated (23 Oct 2026), the main data.gouv.fr dataset page
> displayed a maintenance notice pointing to a transitional export dataset. The download
> step depends on the publisher's availability; the committed cleaned CSV is the reference for
> every figure below. The API-discovery code has not been exercised against the live portal
> from the development environment: test `make data` once before submission.

## 6. Dashboard functionality

The app is organised as **five chapters (tabs)** that follow the story arc:
1 Context (hook) → 2 Overview → 3 Deep dives (by activity, by reason, by region, map, over time)
→ 4 Findings & implications → 5 Data quality & limits. A KPI row stays visible above the tabs, and
each chapter opens with its question and ends with a pointer to the next one.

**Header.** Author, professor and LinkedIn link are set in `utils/constants.py`
(`AUTHOR_NAME`, `PROFESSOR_NAME`, `LINKEDIN_URL`). The school logo is read from
`assets/efrei_logo.svg` (`.png`, `.jpg` and `.webp` also work); without a logo file the header shows
the school name.

Sidebar: four filters (region, activity, inspection context, date range) and a comparison metric
(unfavorable rate % or number of inspections).

- **KPI header:** inspections, unfavorable inspections and unfavorable rate, with a delta against
  the unfiltered dataset.
- **Seven interactive Plotly visuals** with hover: ratings, activities, contexts, regions, map,
  monthly volume, monthly rate. Each analysis opens with a **one-sentence headline computed from
  the current selection**.
- **Reference lines** (selection average / France) on rate charts.
- **Accessibility:** a short chart description under every chart, one rating palette shared by the bar
  chart and the map, labelled axes and units, graphical colours at 3:1 contrast or better.
- **Chapter 5 — Data Quality & Limits:** data-driven validation checks with pass/fail, missing
  values per column, raw-vs-clean figures.
- **Minimum group size** of 100 inspections for rate rankings (`MIN_GROUP_SIZE`).
- **Map sampling:** at most 5,000 points, `SEED = 42` (`utils/constants.py`).
- **Performance:** `st.cache_data` on loading and on the aggregations used by the findings.
- **Key Findings** are computed from the full dataset and do not change with the filters.
- Empty selections show explanatory messages instead of empty charts.

## 7. Data quality and limitations

The app computes these checks live in **Chapter 5 — Data Quality & Limits**. Figures for this snapshot:

| Check | Result |
|---|---:|
| Raw rows | 71,326 |
| Cleaned rows | 71,325 |
| Excluded rows (missing sanitary evaluation) | 1 |
| Duplicate inspection identifiers | 0 |
| Missing inspection dates / sanitary evaluations | 0 / 0 |
| Missing coordinates after cleaning | 1,738 |
| Regions labeled `Unknown` after cleaning | 1,775 |

**Interpretation limits:**

- **Inspection selection bias:** inspections can be scheduled, targeted, complaint-driven, investigative or follow-ups; the data do not represent a random sample of all establishments.
- **Unequal group sizes:** large differences in regional/activity counts make some observed rates less stable.
- **Geographic coverage:** records without a valid location remain in non-map statistics; unknown regions are excluded from regional comparisons but included in national totals.
- **Partial months:** the snapshot begins in October 2025 and ends in October 2026, so both October months are incomplete.
- **Publication lag:** results may not appear immediately after an inspection. Short-term changes, especially near the end of the snapshot, may reflect reporting timing and inspection targeting.
- **No causal inference:** differences in observed rates do not establish why particular groups have more unfavorable inspection results.

## 8. Reproducibility notes

- Dependencies are pinned; the cleaned CSV and `quality_report.json` are committed.
- `scripts/build_data.py` rebuilds both from the portal; a fresh download can give different
  counts because the official dataset is a rolling window that is updated regularly.
- Public Alim'confiance results are displayed for about one year, which explains the one-year
  inspection window. Earlier snapshots exist in third-party public archives of this dataset and
  are a natural extension (not used here).
- The notebook has not been re-run from scratch in a clean environment.

---

**Data source and credit:** Alim'confiance — French Ministry of Agriculture — data.gouv.fr — Licence Ouverte / Open Licence.
