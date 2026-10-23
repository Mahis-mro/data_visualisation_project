"""Behind the Kitchen Door: food-safety inspection storytelling dashboard."""
import streamlit as st

from sections.conclusions import render_findings, render_quality
from sections.deep_dives import render_deep_dives
from sections.header import render_header
from sections.intro import render_intro
from sections.overview import render_overview
from utils.io import load_data, load_quality_report
from utils.prep import filter_data
from utils.viz import chapter_header, inject_css, next_hint

st.set_page_config(page_title="Behind the Kitchen Door", layout="wide")
inject_css()

df = load_data()
full_range = (df["Date_inspection"].min().date(), df["Date_inspection"].max().date())

DEFAULTS = {
    "f_metric": "Unfavorable Rate (%)", "f_regions": [], "f_activities": [],
    "f_contexts": [], "f_dates": full_range,
}


def reset_filters():
    st.session_state.update(DEFAULTS)


for key, default in DEFAULTS.items():      # initial values live in session state
    st.session_state.setdefault(key, default)


# ----------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("Filters")
    st.caption("Filters update the KPIs and chapters 2 and 3.")

    selected_metric = st.selectbox(
        "Comparison Metric",
        options=["Unfavorable Rate (%)", "Number of Inspections"],
        key="f_metric",
        help="Choose the measure displayed in the activity, context and regional comparison charts.",
    )
    selected_regions = st.multiselect(
        "Regions", sorted(df["reg_name"].dropna().unique()), key="f_regions"
    )
    selected_activities = st.multiselect(
        "Establishment Activities",
        sorted(df["APP_Libelle_activite_etablissement"].dropna().unique()),
        key="f_activities",
    )
    selected_contexts = st.multiselect(
        "Inspection Contexts", sorted(df["Contexte_inspection"].dropna().unique()),
        key="f_contexts",
    )
    date_range = st.date_input(
        "Inspection Period",
        min_value=full_range[0], max_value=full_range[1], key="f_dates",
    )
    st.button("Reset all filters", on_click=reset_filters, width="stretch")

filtered_df = filter_data(
    df, selected_regions, selected_activities, selected_contexts, date_range
)
# Same filters as the selection except the region: a selected region is compared
# with France over the same period, activities and inspection contexts.
national_reference_df = filter_data(
    df, [], selected_activities, selected_contexts, date_range
)

# ------------------------------------------------------------------ layout
render_header()
render_overview(filtered_df, df)      # KPI row, always visible, tied to the filters

tab_ctx, tab_over, tab_deep, tab_find, tab_data = st.tabs([
    "1 · Context", "2 · Overview", "3 · Deep dives", "4 · Findings", "5 · Data & limits",
])

with tab_ctx:
    render_intro(df)
    next_hint("see how inspections turn out overall (chapter 2).")

with tab_over:
    chapter_header(2, 5, "Overview", "How do inspections turn out, overall?")

with tab_deep:
    chapter_header(3, 5, "Deep dives", "Who fails more often, why, where and when?")
    t_act, t_ctx, t_reg, t_map, t_time = st.tabs(
        ["By activity", "By reason", "By region", "Map", "Over time"]
    )

render_deep_dives(
    filtered_df, selected_metric, national_reference_df,
    containers={
        "ratings": tab_over, "activity": t_act, "context": t_ctx,
        "region": t_reg, "map": t_map, "time": t_time,
    },
)
with tab_over:
    next_hint("zoom in on who fails more often, and why (chapter 3).")
with tab_deep:
    next_hint("what we learn from all this, and what it means (chapter 4).")

with tab_find:
    chapter_header(4, 5, "Findings & implications", "What do we learn, and what does it mean?")
    render_findings(df)
    next_hint("how far can we trust these numbers? (chapter 5).")

with tab_data:
    chapter_header(5, 5, "Data quality & limits", "How far can we trust these results?")
    render_quality(df, load_quality_report())
