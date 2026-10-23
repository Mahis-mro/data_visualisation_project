"""Chapter 4 (findings + implications) and chapter 5 (data quality + limits)."""
import pandas as pd
import streamlit as st

from utils.constants import MIN_GROUP_SIZE
from utils.io import load_download_info
from utils.prep import group_stats, missingness_table, validation_checks


@st.cache_data(show_spinner=False)
def _findings(df: pd.DataFrame) -> dict:
    """Pre-aggregate everything the static sections need (computed once)."""
    out = {"n": len(df), "unfav": int(df["unfavorable"].sum())}
    out["rate"] = out["unfav"] / out["n"] * 100
    act = group_stats(df, "APP_Libelle_activite_etablissement")
    out["activity"] = act.set_index("APP_Libelle_activite_etablissement")
    out["top_activity_count"] = act.sort_values("total_inspections").iloc[-1]
    ranked = act[act["total_inspections"] >= MIN_GROUP_SIZE].sort_values("unfavorable_rate")
    out["top_activity_rate"] = ranked.iloc[-1]
    out["ctx"] = group_stats(df, "Contexte_inspection").set_index("Contexte_inspection")
    reg = group_stats(df[df["reg_name"] != "Unknown"], "reg_name")
    out["reg_small"] = reg[reg["total_inspections"] < MIN_GROUP_SIZE].sort_values(
        "unfavorable_rate", ascending=False
    )
    out["reg_big"] = reg[reg["total_inspections"] >= MIN_GROUP_SIZE].sort_values(
        "unfavorable_rate", ascending=False
    )
    months = group_stats(df, df["Date_inspection"].dt.to_period("M")).rename(
        columns={"Date_inspection": "month"}
    )
    out["months"] = months.iloc[1:-1]          # first and last months are partial
    return out


def _card(title: str, body: str):
    with st.container(border=True):
        st.markdown(f"**{title}**")
        st.markdown(body)


def render_findings(df):
    """Chapter 4: what the data says (full dataset) and what it implies."""
    f = _findings(df)
    start, end = df["Date_inspection"].min(), df["Date_inspection"].max()
    ctx = f["ctx"]["unfavorable_rate"]
    top_c, top_r = f["top_activity_count"], f["top_activity_rate"]

    st.subheader("What the data says")
    _card(
        "1. Most inspections end well",
        f"Of **{f['n']:,}** inspections, **{100 - f['rate']:.2f}%** are satisfactory or very "
        f"satisfactory. **{f['unfav']:,} ({f['rate']:.2f}%)** need improvement or urgent action.",
    )
    _card(
        "2. Volume and failure rate tell different stories",
        f"The most inspected activity is **{top_c['APP_Libelle_activite_etablissement']}** "
        f"({int(top_c['total_inspections']):,} inspections, {top_c['unfavorable_rate']:.2f}% unfavorable). "
        f"Among activities with at least {MIN_GROUP_SIZE} inspections, "
        f"**{top_r['APP_Libelle_activite_etablissement']}** has the highest rate "
        f"({top_r['unfavorable_rate']:.2f}%, from {int(top_r['total_inspections']):,} inspections).",
    )
    _card(
        "3. Inspection outcomes vary by inspection context",
        f"Complaints and reports: **{ctx.get('Plainte / Signalement', float('nan')):.2f}%** unfavorable. "
        f"Scheduled inspections: **{ctx.get('Programmation', float('nan')):.2f}%**. "
        f"Follow-ups: **{ctx.get('Re-contrôle', float('nan')):.2f}%**. These groups are not randomly "
        "selected, so the differences are **not causal**.",
    )
    reg_txt = ", ".join(
        f"{r.reg_name} ({r.unfavorable_rate:.1f}%, {int(r.unfavorable_inspections)} of {int(r.total_inspections)})"
        for r in f["reg_big"].head(2).itertuples()
    )
    _card(
        "4. Regional differences need caution",
        f"Among regions with at least {MIN_GROUP_SIZE} inspections, observed rates range from "
        f"{f['reg_big']['unfavorable_rate'].min():.1f}% to {f['reg_big']['unfavorable_rate'].max():.1f}%. "
        f"The highest are {reg_txt}, yet volumes are small and selection practices may differ. "
        f"{len(f['reg_small'])} territories have fewer than {MIN_GROUP_SIZE} inspections and are "
        "left out of rate rankings.",
    )
    m = f["months"]
    if len(m) >= 2:
        first, last = m.iloc[0], m.iloc[-1]
        peak = m.sort_values("unfavorable_rate").iloc[-1]
        peak_txt = (
            "" if peak["month"] == last["month"]
            else f", peaking at {peak['unfavorable_rate']:.2f}% ({peak['month']})"
        )
        _card(
            "5. The monthly pattern raises questions, not conclusions",
            f"Between full months, the rate goes from **{first['unfavorable_rate']:.2f}% "
            f"({first['month']})** to **{last['unfavorable_rate']:.2f}% ({last['month']})**{peak_txt}. "
            "A steady climb inside a one-year publication window can also be produced by "
            "inspection targeting or reporting effects, so it should be verified before being "
            "read as a real deterioration.",
        )

    st.caption(
        f"Snapshot from {start:%d %B %Y} to {end:%d %B %Y}. Unlike the KPIs and chapters 2 and 3, "
        "these findings do not change with the sidebar filters."
    )

    st.subheader("What it means")
    st.success(
        "Read an unfavorable rate as *\"how often inspectors found problems where they looked\"*, "
        "not *\"how risky this kind of place is\"*. Rates are most useful when compared within "
        "the same inspection context."
    )
    st.markdown(
        "**Next steps**\n"
        "- Compare activities **within the same region and inspection context**.\n"
        "- Add earlier snapshots (public archives of the same dataset exist) to test whether the "
        "monthly climb is real or a window effect.\n"
        "- Model the probability of an unfavorable result from activity, context and region, "
        "to separate their effects."
    )


def render_quality(df, quality=None):
    """Chapter 5: data quality checks and methodological limits."""
    start, end = df["Date_inspection"].min(), df["Date_inspection"].max()
    st.write(
        "Every figure below is recomputed from the cleaned file when the app starts, "
        "except the raw-file numbers, which come from `data/quality_report.json` "
        "written by `scripts/build_data.py`."
    )

    if quality:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Raw inspections", f"{quality['raw_rows']:,}")
        c2.metric("After cleaning", f"{quality['clean_rows']:,}")
        c3.metric("Removed", f"{quality['removed_rows']:,}", help=quality["removed_reason"])
        c4.metric("Duplicate rows in raw file", f"{quality['raw_duplicate_rows']:,}")
    else:
        st.warning("quality_report.json not found: run `python scripts/build_data.py`.")

    left, right = st.columns(2)
    with left:
        st.subheader("Validation checks")
        checks = validation_checks(df)
        st.dataframe(checks, hide_index=True, width="stretch")
        if (checks["Status"] == "FAIL").any():
            st.error("At least one validation check failed.")
    with right:
        st.subheader("Missing values by column")
        st.dataframe(missingness_table(df), hide_index=True, width="stretch")

    info = load_download_info()
    st.caption(
        "Raw file downloaded "
        + (f"on {info['downloaded_at_utc']} (UTC) from {info['url']}." if info
           else "before download tracking was added; see the README for the extraction date.")
    )

    st.subheader("Methodological limitations")
    st.markdown(f"""
**Selection bias.** Inspections are not a random sample of French food businesses:
some are prompted by complaints, investigations or earlier findings.

**Different sample sizes.** Rates from small groups are unstable, so rankings use a
minimum of {MIN_GROUP_SIZE} inspections.

**Limited time window.** Results cover {start:%d %B %Y} to {end:%d %B %Y}. Public
Alim'confiance results are displayed for about one year, so this is a rolling window,
not a historical archive. First and last months are partial.

**Publication delays.** Recent results may not be fully published yet.

**Unit of analysis.** A row is an inspection, not a distinct establishment. Names and
SIRET numbers are published by the ministry; for sole traders they may identify a
person, so the app only shows them in map tooltips and never ranks individual businesses.

**No causal claims.** Differences describe records, not causes.
""")
    st.caption(
        "Source: Alim'confiance — French Ministry of Agriculture — "
        "data.gouv.fr — Licence Ouverte / Open Licence."
    )
