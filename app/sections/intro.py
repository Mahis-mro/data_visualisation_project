"""Chapter 1: context, hook, audience and the shape of the story."""
import pandas as pd
import streamlit as st

from utils.constants import DATASET_URL
from utils.viz import chapter_header

STEPS = [
    ("1", "Context", "Why inspections matter"),
    ("2", "Overview", "How they turn out overall"),
    ("3", "Deep dives", "Who, why, where, when"),
    ("4", "Findings", "What we learn, what it means"),
    ("5", "Data & limits", "How far to trust it"),
]


def render_intro(df):
    chapter_header(1, 5, "Context", "Why look at food-safety inspections?")

    n = len(df)
    start, end = df["Date_inspection"].min(), df["Date_inspection"].max()
    ctx = df.groupby("Contexte_inspection")["unfavorable"].mean() * 100
    rate = df["unfavorable"].mean() * 100

    st.markdown(
        f"Between **{start:%d %B %Y}** and **{end:%d %B %Y}**, French inspectors published "
        f"**{n:,} official food-safety inspections** of restaurants, bakeries, canteens and "
        "shops. Behind each result is a kitchen you might eat in. But a high share of bad "
        "results does not automatically mean a *dangerous* place: it can also mean "
        "*where inspectors choose to look*. That tension is the story."
    )

    st.markdown("**Three numbers to keep in mind** (full dataset, not affected by filters)")
    c1, c2, c3 = st.columns(3)
    c1.metric("Inspections ending badly", f"{rate:.1f}%",
              help="Rated 'A améliorer' or 'A corriger de manière urgente'.")
    if pd.notna(ctx.get("Plainte / Signalement")):
        c2.metric("After a complaint or report", f"{ctx['Plainte / Signalement']:.1f}%")
    if pd.notna(ctx.get("Programmation")):
        c3.metric("On a scheduled inspection", f"{ctx['Programmation']:.1f}%")

    st.markdown("**The story in five chapters**")
    for col, (num, title, sub) in zip(st.columns(5), STEPS):
        with col, st.container(border=True):
            st.markdown(f'<p class="step-num">{num}</p>', unsafe_allow_html=True)
            st.markdown(f"**{title}**")
            st.caption(sub)

    left, right = st.columns(2)
    with left:
        st.markdown(
            "**Who is this for?** Curious consumers and students. No expertise needed.\n\n"
            "**Questions answered**\n"
            "1. How often does an inspection go wrong?\n"
            "2. Do some activities, inspection reasons, regions or months stand out?\n"
            "3. How far can we trust those differences?"
        )
    with right:
        st.info(
            "**Reading guide.** An *unfavorable* inspection is rated **A améliorer** or "
            "**A corriger de manière urgente**. Percentages refer to recorded inspections, "
            "not to all food businesses in France. Use the sidebar filters: the KPIs and "
            "chapters 2 and 3 update. Chapter 4 always uses the full dataset."
        )

    st.caption(
        "Source: Alim’confiance — French Ministry of Agriculture — data.gouv.fr — "
        f"Licence Ouverte / Open Licence. [Official dataset]({DATASET_URL})"
    )
