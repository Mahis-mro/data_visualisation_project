import streamlit as st

from utils.viz import headline


def render_overview(filtered_df, baseline_df):
    """KPI header tied to the filters, with a delta against the unfiltered dataset."""
    total = len(filtered_df)
    unfav = int(filtered_df["unfavorable"].sum())
    rate = unfav / total * 100 if total else 0.0
    base_rate = baseline_df["unfavorable"].mean() * 100

    if filtered_df.empty:
        st.warning("No inspections match the selected filters. Try a broader selection.")

    filtered = total != len(baseline_df)
    compare = f" (all inspections, filters off: {base_rate:.1f}%)" if filtered else ""
    headline(
        f"**Headline: {rate:.1f}% of the selected inspections were unfavorable{compare}.**"
    )

    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Total Inspections", f"{total:,}",
        delta=f"{total / len(baseline_df) * 100:.1f}% of all inspections" if filtered else None,
        delta_color="off",
        help="Number of recorded inspections matching the sidebar filters.",
    )
    col2.metric(
        "Unfavorable Inspections", f"{unfav:,}",
        help="Rated 'A améliorer' or 'A corriger de manière urgente'.",
    )
    col3.metric(
        "Unfavorable Rate", f"{rate:.2f}%",
        delta=f"{rate - base_rate:+.2f} pp vs all inspections" if filtered and total else None,
        delta_color="inverse",
        help="Unfavorable inspections / recorded inspections. pp = percentage points.",
    )
