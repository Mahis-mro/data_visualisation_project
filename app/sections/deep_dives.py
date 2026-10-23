import streamlit as st
import pandas as pd
import plotly.express as px
from utils.constants import (
    BAR_COLOR, FULL_MONTH_COLOR, MAP_MAX_POINTS, MIN_GROUP_SIZE,
    PARTIAL_MONTH_COLOR, RATING_COLORS, RATING_ORDER, SEED,
)
from utils.io import load_data
from utils.viz import add_reference, headline, plot_chart


def render_deep_dives(filtered_df, selected_metric, national_reference_df, containers):
    """Render each analysis inside its own container (tab) from `containers`."""
    # Avoid generating misleading empty charts when no inspections match filters.
    if filtered_df.empty:
        for box in containers.values():
            with box:
                st.info(
                    "No charts to display: no inspections match the selected filters. "
                    "Please broaden the region, activity, context or date selection."
                )
        return

    # Reference values used for headlines and reference lines.
    sel_rate = filtered_df["unfavorable"].mean() * 100
    national_rate = (
        national_reference_df["unfavorable"].mean() * 100
        if len(national_reference_df) else float("nan")
    )

    # Display the distribution of sanitary evaluation results
    with containers["ratings"]:
        st.subheader("Rating distribution")
        headline(
            f"**Headline: {100 - sel_rate:.1f}% of the {len(filtered_df):,} selected "
            "inspections are rated favorable; the unfavorable minority is the story below.**"
        )
        st.write(
            "**Question:** How are recorded inspections rated? "
            "The chart shows counts for each of the four official evaluation categories."
        )

        rating_order = RATING_ORDER

        rating_counts = (
            filtered_df["Synthese_eval_sanit"]
            .value_counts()
            .reindex(rating_order, fill_value=0)
            .reset_index()
        )

        rating_counts.columns = ["Sanitary Evaluation", "Inspections"]

        fig_ratings = px.bar(
            rating_counts,
            x="Sanitary Evaluation",
            y="Inspections",
            color="Sanitary Evaluation",
            title="Distribution of Sanitary Evaluations",
            text="Inspections",
            color_discrete_map=RATING_COLORS
        )

        fig_ratings.update_layout(
            xaxis_title="Sanitary Evaluation",
            yaxis_title="Number of Inspections",
            showlegend=False
        )

        plot_chart(
            fig_ratings,
        
            alt=(f"Bar chart of inspections per rating. Unfavorable ratings (A améliorer + "
                 f"A corriger de manière urgente) represent {sel_rate:.1f}% of the selection."),
            key="sanitary_evaluation_chart"
        )

        st.caption(
            "Each bar represents an inspection count, not the number of unique establishments. "
            "Values and counts change with the sidebar filters."
        )


        # Compare establishment activities using the selected metric
    with containers["activity"]:
        st.subheader("Establishment activity")

        activity_stats = (
            filtered_df.groupby("APP_Libelle_activite_etablissement")
            .agg(
                total_inspections=("Numero_inspection", "count"),
                unfavorable_inspections=("unfavorable", "sum"),
                unfavorable_rate=("unfavorable", "mean")
            )
            .reset_index()
        )
        activity_stats["unfavorable_rate"] *= 100

        # Choose the comparison metric while retaining the full group statistics.
        if selected_metric == "Unfavorable Rate (%)":
            chart_metric = "unfavorable_rate"
            metric_label = "Unfavorable Rate (%)"
            # The sample-size threshold applies to rankings, not single-activity summaries.
            ranked_activities = activity_stats[
                activity_stats["total_inspections"] >= MIN_GROUP_SIZE
            ].copy()
        else:
            chart_metric = "total_inspections"
            metric_label = "Number of Inspections"
            ranked_activities = activity_stats.copy()

        ranked_activities = (
            ranked_activities.sort_values(chart_metric, ascending=False).head(10)
        )
        if not ranked_activities.empty:
            top = ranked_activities.iloc[0]
            top_name = top["APP_Libelle_activite_etablissement"]
            if chart_metric == "unfavorable_rate":
                headline(
                    f"**Headline: among activities with at least {MIN_GROUP_SIZE} inspections, "
                    f"{top_name} has the highest unfavorable rate ({top['unfavorable_rate']:.1f}%), "
                    f"against {sel_rate:.1f}% for the whole selection.**"
                )
            else:
                headline(
                    f"**Headline: {top_name} is the most inspected activity "
                    f"({int(top['total_inspections']):,} inspections); compare counts with rates "
                    "before concluding anything.**"
                )

        if activity_stats.empty:
            st.info("No establishment activities match the selected filters.")

        elif len(activity_stats) == 1 or len(ranked_activities) == 1:
            # A one-bar 'Top 10' chart would be visually unhelpful: show compact KPIs.
            # When several activities exist but only one meets the minimum sample size,
            # clearly explain why the other groups are excluded from the ranking.
            activity = (activity_stats if len(activity_stats) == 1 else ranked_activities).iloc[0]
            activity_name = str(activity["APP_Libelle_activite_etablissement"])
            activity_count = int(activity["total_inspections"])
            unfavorable_count = int(activity["unfavorable_inspections"])
            activity_rate = float(activity["unfavorable_rate"])

            st.write(
                "**Selected activity at a glance.** The indicators below summarize "
                "recorded inspections instead of displaying a single oversized bar."
            )
            st.markdown(f"**Activity:** {activity_name}")
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Inspections", f"{activity_count:,}")
            col2.metric("Unfavorable Inspections", f"{unfavorable_count:,}")
            col3.metric("Unfavorable Rate", f"{activity_rate:.2f}%")

            if len(activity_stats) > 1:
                st.caption(
                    "Only one activity meets the 100-inspection threshold under the current "
                    "filters. The other activities are excluded from the rate ranking."
                )
            if activity_count < 100:
                st.warning(
                    "Fewer than 100 inspections match these filters for this activity. "
                    "Interpret its unfavorable rate cautiously."
                )
            else:
                st.caption(
                    "The indicators use the current region, activity, context and date filters. "
                    "They describe inspections, not unique establishments."
                )

        elif ranked_activities.empty:
            st.info(
                "No establishment activity meets the 100-inspection threshold "
                "under the current filters. Try a broader date range or fewer filters."
            )

        else:
            st.write(
                "**Question:** Do the most frequently inspected activities also have the highest "
                "unfavorable rates? Choose a metric in the sidebar to compare counts and percentages."
            )
            fig_activities = px.bar(
                ranked_activities,
                x=chart_metric,
                y="APP_Libelle_activite_etablissement",
                orientation="h",
                title=f"Top {len(ranked_activities)} Activities by {metric_label}",
                labels={
                    chart_metric: metric_label,
                    "APP_Libelle_activite_etablissement": "Establishment Activity"
                },
                hover_data={
                    "total_inspections": True,
                    "unfavorable_inspections": True,
                    "unfavorable_rate": ":.2f"
                },
            )
            fig_activities.update_layout(yaxis={"categoryorder": "total ascending"})
            fig_activities.update_traces(marker_color=BAR_COLOR)
            if chart_metric == "unfavorable_rate":
                add_reference(fig_activities, sel_rate, f"Selection average {sel_rate:.1f}%")
            plot_chart(
                fig_activities,
                alt=(f"Horizontal bars of the top {len(ranked_activities)} establishment activities by "
                     f"{metric_label}; the busiest or highest bar is {top_name}."),
                key="establishment_type_chart"
            )
            if selected_metric == "Unfavorable Rate (%)":
                st.caption(
                    "Only activities with at least 100 inspections in the selected data "
                    "are included in the unfavorable rate ranking."
                )
            else:
                st.caption(
                    "Activities are ranked by the number of inspections in the selected data."
                )


        # Compare inspection contexts using the selected metric
    with containers["context"]:
        st.subheader("Reason for inspection")
        st.write(
            "**Question:** How do inspection results differ between scheduled inspections, "
            "complaints, targeted inspections and follow-ups? "
            "TIAC refers to collective foodborne illness investigations."
        )

        context_stats = (
            filtered_df.groupby("Contexte_inspection")
            .agg(
                total_inspections=("Numero_inspection", "count"),
                unfavorable_rate=("unfavorable", "mean")
            )
            .reset_index()
        )

        context_stats["unfavorable_rate"] *= 100
        context_stats = context_stats.sort_values(chart_metric, ascending=False)
        if not context_stats.empty:
            by_rate = context_stats.sort_values("unfavorable_rate", ascending=False)
            hi, lo = by_rate.iloc[0], by_rate.iloc[-1]
            if len(by_rate) == 1:   # one context only: nothing to compare
                headline(
                    f"**Headline: '{hi['Contexte_inspection']}' inspections: "
                    f"{hi['unfavorable_rate']:.1f}% unfavorable, out of "
                    f"{int(hi['total_inspections']):,} inspections.**"
                )
            else:
                headline(
                    f"**Headline: '{hi['Contexte_inspection']}' inspections have the highest unfavorable "
                    f"rate ({hi['unfavorable_rate']:.1f}%) versus {lo['unfavorable_rate']:.1f}% for "
                    f"'{lo['Contexte_inspection']}': outcomes differ widely by inspection context.**"
                )

        if context_stats.empty:
            st.info("No inspection contexts match the selected filters.")
        elif len(context_stats) == 1:
            # A single context has nothing to be compared with: show its figures instead of a lone bar.
            only = context_stats.iloc[0]
            m1, m2, _ = st.columns(3)
            m1.metric(f"Unfavorable rate: {only['Contexte_inspection']}",
                      f"{only['unfavorable_rate']:.2f}%")
            m2.metric("Inspections", f"{int(only['total_inspections']):,}")
            st.caption("Select several contexts, or none, in the sidebar to compare them.")
        else:
            fig_context = px.bar(
                context_stats,
                x="Contexte_inspection",
                y=chart_metric,
                color_discrete_sequence=[BAR_COLOR],
                title=f"Inspection Context Comparison — {metric_label}",
                labels={
                    "Contexte_inspection": "Inspection Context",
                    chart_metric: metric_label
                },
                hover_data=["total_inspections", "unfavorable_rate"]
                if chart_metric == "unfavorable_rate"
                else ["unfavorable_rate"]
            )

            fig_context.update_layout(showlegend=False)
            if chart_metric == "unfavorable_rate":
                add_reference(fig_context, sel_rate, f"Selection average {sel_rate:.1f}%", "h")

            plot_chart(
                fig_context,
                alt=(f"Bar chart of {metric_label} for each inspection context; "
                     f"highest unfavorable rate: {hi['Contexte_inspection']}."),
                key="inspection_context_chart"
            )

        st.caption(
            "Inspection contexts may involve different selection criteria. "
            "Higher unfavorable rates do not establish a causal relationship."
        )


        # Compare inspection volumes and unfavorable rates across regions
    with containers["region"]:
        st.subheader("Regions")

        st.write(
            "**Question:** How do inspection outcomes differ across regions? "
            "Compare both percentages and inspection counts. "
            "Regional rates should not be interpreted as a ranking of food safety."
        )

        regional_data = filtered_df[
            filtered_df["reg_name"].notna()
            & (filtered_df["reg_name"] != "Unknown")
        ]

        regional_stats = (
            regional_data.groupby("reg_name")
            .agg(
                total_inspections=("Numero_inspection", "count"),
                unfavorable_inspections=("unfavorable", "sum"),
                unfavorable_rate=("unfavorable", "mean")
            )
            .reset_index()
        )

        regional_stats["unfavorable_rate"] *= 100

        eligible_regions = regional_stats[regional_stats["total_inspections"] >= MIN_GROUP_SIZE]
        if len(eligible_regions) >= 2:
            if selected_metric == "Unfavorable Rate (%)":
                r_hi = eligible_regions.sort_values("unfavorable_rate").iloc[-1]
                r_lo = eligible_regions.sort_values("unfavorable_rate").iloc[0]
                headline(
                    f"**Headline: among regions with at least {MIN_GROUP_SIZE} inspections, unfavorable "
                    f"rates range from {r_lo['unfavorable_rate']:.1f}% ({r_lo['reg_name']}) to "
                    f"{r_hi['unfavorable_rate']:.1f}% ({r_hi['reg_name']}). Treat this as a difference "
                    "in inspection records, not a ranking of food safety.**"
                )
            else:
                r_top = eligible_regions.sort_values("total_inspections").iloc[-1]
                headline(
                    f"**Headline: {r_top['reg_name']} accounts for the most inspections "
                    f"({int(r_top['total_inspections']):,}); volumes differ widely between regions.**"
                )

        # With one region, a comparison bar chart contains only one oversized bar.
        # Use compact indicators and a France-wide reference instead. The reference
        # uses the same activity, context and date filters but ignores region selection.
        if len(regional_stats) == 1:
            region = regional_stats.iloc[0]
            region_name = str(region["reg_name"])
            region_inspections = int(region["total_inspections"])
            region_rate = float(region["unfavorable_rate"])

            national_inspections = len(national_reference_df)
            national_rate = (
                national_reference_df["unfavorable"].mean() * 100
                if national_inspections > 0 else 0.0
            )

            st.markdown(f"**Selected region:** {region_name}")
            col1, col2, col3 = st.columns(3)

            if selected_metric == "Unfavorable Rate (%)":
                col1.metric("Region — Unfavorable Rate", f"{region_rate:.2f}%")
                col2.metric("France — Unfavorable Rate", f"{national_rate:.2f}%")
                col3.metric("Difference vs France", f"{region_rate - national_rate:+.2f} pp")
            else:
                national_share = (
                    100 * region_inspections / national_inspections
                    if national_inspections > 0 else 0.0
                )
                col1.metric("Inspections in Region", f"{region_inspections:,}")
                col2.metric("Inspections in France", f"{national_inspections:,}")
                col3.metric("Share of Inspections", f"{national_share:.2f}%")
                st.caption(
                    f"Unfavorable rate in {region_name}: {region_rate:.2f}% "
                    f"(France: {national_rate:.2f}%)."
                )

            st.caption(
                f"Based on {region_inspections:,} inspections in {region_name}. "
                "The France-wide reference includes all regions while keeping "
                "the same activity, inspection context and date filters."
            )
            if region_inspections < 100:
                st.warning(
                    "Fewer than 100 inspections match these filters in this region. "
                    "Interpret its unfavorable rate cautiously."
                )

        else:
            # Use a minimum of 100 inspections only for comparisons of rates.
            if selected_metric == "Unfavorable Rate (%)":
                regional_stats = regional_stats[
                    regional_stats["total_inspections"] >= MIN_GROUP_SIZE
                ]

            regional_stats = regional_stats.sort_values(chart_metric, ascending=False)

            if regional_stats.empty:
                st.info("No region meets the selected filters and comparison criteria.")
            elif len(regional_stats) == 1:
                # If other regions fall below the minimum sample size, the remaining
                # region is not a meaningful ranking on its own.
                one = regional_stats.iloc[0]
                st.metric(
                    f"{one['reg_name']} — Unfavorable Rate",
                    f"{one['unfavorable_rate']:.2f}%",
                )
                st.caption(
                    "Only one region meets the 100-inspection threshold under these filters. "
                    "Adjust the sidebar filters to compare more regions."
                )
            else:
                fig_regions = px.bar(
                    regional_stats,
                    x=chart_metric,
                    y="reg_name",
                    orientation="h",
                    title=f"Regional Comparison — {metric_label}",
                    labels={
                        "reg_name": "Region",
                        chart_metric: metric_label
                    },
                    hover_data={
                        "total_inspections": True,
                        "unfavorable_inspections": True,
                        "unfavorable_rate": ":.2f"
                    }
                )
                fig_regions.update_layout(
                    yaxis={"categoryorder": "total ascending"},
                    height=max(430, 26 * len(regional_stats) + 100)
                )
                fig_regions.update_traces(marker_color=BAR_COLOR)
                if chart_metric == "unfavorable_rate" and national_rate == national_rate:
                    add_reference(fig_regions, national_rate, f"France {national_rate:.1f}%")
                plot_chart(
                    fig_regions,
                    alt=(f"Horizontal bars of {metric_label} by region for {len(regional_stats)} regions."),
                    key="regional_comparison_chart"
                )

        if len(regional_stats) != 1:
            st.caption(
                "Unknown regions are excluded from regional comparisons, not from the national KPIs. "
                + (
                    "Regions with fewer than 100 inspections in the filtered data are omitted from the rate comparison."
                    if selected_metric == "Unfavorable Rate (%)"
                    else "All identified regions matching the selected filters are included."
                )
            )

        # Display a geographic map of food safety inspections

    with containers["map"]:
        st.subheader("Map")

        st.write(
            "Explore the geographic distribution of food safety inspections "
            "across France. Each point represents one recorded inspection, not necessarily a unique business."
        )

        map_data = filtered_df.dropna(
            subset=["latitude", "longitude"]
        ).copy()

        map_data = map_data[
            map_data["latitude"].between(-90, 90)
            & map_data["longitude"].between(-180, 180)
        ]

        n_geolocated = len(map_data)
        headline(
            f"**Headline: {n_geolocated:,} of the {len(filtered_df):,} selected inspections "
            f"({n_geolocated / len(filtered_df) * 100:.0f}%) have valid coordinates and can be "
            "mapped; the others stay in every non-map statistic.**"
        )

        # Sample geographic points to improve dashboard performance.
        if len(map_data) > MAP_MAX_POINTS:
            map_data = map_data.sample(n=MAP_MAX_POINTS, random_state=SEED)

        if not map_data.empty:
            # Plotly sometimes starts the map around (0, 0) without an explicit
            # center. Compute a stable, data-driven initial view instead.
            # When mainland and overseas inspections are mixed, focus the initial
            # view on mainland France; overseas inspections remain in the data
            # and can be explored using the Regions filter.
            mainland_points = map_data[
                map_data["latitude"].between(41.0, 51.5)
                & map_data["longitude"].between(-6.0, 10.0)
            ]
            view_points = (
                mainland_points
                if len(mainland_points) > len(map_data) / 2
                else map_data
            )
            map_center = {
                "lat": float(view_points["latitude"].median()),
                "lon": float(view_points["longitude"].median()),
            }

            # Adapt the initial zoom to the extent of the filtered inspections.
            lat_span = float(
                view_points["latitude"].quantile(0.975)
                - view_points["latitude"].quantile(0.025)
            )
            lon_span = float(
                view_points["longitude"].quantile(0.975)
                - view_points["longitude"].quantile(0.025)
            )
            extent = max(lat_span, lon_span)
            if extent > 6:
                map_zoom = 4
            elif extent > 3:
                map_zoom = 5
            elif extent > 1.5:
                map_zoom = 6
            elif extent > 0.7:
                map_zoom = 7
            elif extent > 0.25:
                map_zoom = 8
            else:
                map_zoom = 10

            fig_map = px.scatter_map(
                map_data,
                lat="latitude",
                lon="longitude",
                color="Synthese_eval_sanit",
                color_discrete_map=RATING_COLORS,
                category_orders={"Synthese_eval_sanit": RATING_ORDER},
                hover_name="APP_Libelle_etablissement",
                hover_data={
                    "reg_name": True,
                    "Contexte_inspection": True,
                    "latitude": False,
                    "longitude": False
                },
                center=map_center,
                zoom=map_zoom,
                height=550,
                title="Geographic Distribution of Inspections"
            )

            fig_map.update_layout(
                map_style="open-street-map",
                margin=dict(l=0, r=0, t=45, b=0),
                legend_title_text="Sanitary Evaluation"
            )

            plot_chart(
                fig_map,
                alt=(f"Map of France: {len(map_data):,} dots, one per inspection, colored by "
                     "sanitary rating with the same colors as the first chart. Hover for the "
                     "establishment name, region and inspection context."),
                key="geographic_map"
            )

            st.caption(
                f"Displaying {len(map_data):,} inspection locations. "
                "A reproducible sample is used when more than 5,000 "
                "geolocated inspections match the filters."
            )
        else:
            st.info("No geographic data available for the selected filters.")


        # Calculate monthly inspection volumes and unfavorable rates

    with containers["time"]:
        st.subheader("Time")
        st.write(
            "**Question:** How do inspection volumes and unfavorable rates vary by month? "
            "The two charts present distinct indicators and should be read together."
        )

        monthly_stats = (
            filtered_df
            .groupby(filtered_df["Date_inspection"].dt.to_period("M"))
            .agg(
                total_inspections=("Numero_inspection", "count"),
                unfavorable_inspections=("unfavorable", "sum"),
                unfavorable_rate=("unfavorable", "mean")
            )
            .reset_index()
        )

        monthly_stats["unfavorable_rate"] *= 100

        monthly_stats["Date_inspection"] = (
            monthly_stats["Date_inspection"].dt.to_timestamp()
        )



        # Distinguish partial months at the boundaries of the source dataset.
        # Read from the cached full dataset so changing the region/activity/context
        # filters does not change which source months are considered incomplete.
        source_dates = load_data()["Date_inspection"]
        first_source_date = source_dates.min()
        last_source_date = source_dates.max()

        incomplete_months = set()
        if first_source_date.day != 1:
            incomplete_months.add(first_source_date.to_period("M"))
        if last_source_date.day != last_source_date.days_in_month:
            incomplete_months.add(last_source_date.to_period("M"))

        monthly_stats["partial_source_month"] = monthly_stats[
            "Date_inspection"
        ].dt.to_period("M").isin(incomplete_months)
        monthly_stats["Month Coverage"] = monthly_stats[
            "partial_source_month"
        ].map({False: "Full dataset month", True: "Partial dataset month"})

        # The volume chart still shows every available month. Partial source
        # months use a different color to make their limited coverage obvious.
        # The rate trend omits those months: a sharp fall in the last incomplete
        # month should not be mistaken for a confirmed change in food safety.
        complete_months = monthly_stats.loc[
            ~monthly_stats["partial_source_month"]
        ].copy()

        if len(complete_months) >= 2:
            m0, m1 = complete_months.iloc[0], complete_months.iloc[-1]
            headline(
                f"**Headline: across full months, the unfavorable rate went from "
                f"{m0['unfavorable_rate']:.1f}% ({m0['Date_inspection']:%b %Y}) to "
                f"{m1['unfavorable_rate']:.1f}% ({m1['Date_inspection']:%b %Y}). Check this against "
                "inspection targeting and publication timing before reading it as a real change.**"
            )

        if not monthly_stats.empty:
            fig_monthly_count = px.bar(
                monthly_stats,
                x="Date_inspection",
                y="total_inspections",
                color="Month Coverage",
                color_discrete_map={
                    "Full dataset month": FULL_MONTH_COLOR,
                    "Partial dataset month": PARTIAL_MONTH_COLOR,
                },
                title="Monthly Inspection Volume",
                labels={
                    "Date_inspection": "Month",
                    "total_inspections": "Number of Inspections",
                },
                hover_data={"Month Coverage": True},
            )
            fig_monthly_count.update_layout(
                legend_title_text="Source coverage",
                xaxis_title="Month",
                yaxis_title="Number of Inspections",
            )
            plot_chart(
                fig_monthly_count,
            
                alt="Bars of monthly inspection counts; gray bars are months only partly covered by the dataset.",
                key="monthly_inspection_volume"
            )

            if not complete_months.empty:
                fig_monthly_rate = px.line(
                    complete_months,
                    x="Date_inspection",
                    y="unfavorable_rate",
                    markers=True,
                    title="Monthly Unfavorable Inspection Rate — Full Dataset Months",
                    labels={
                        "Date_inspection": "Month",
                        "unfavorable_rate": "Unfavorable Rate (%)",
                    },
                )
                fig_monthly_rate.update_yaxes(rangemode="tozero")
                fig_monthly_rate.update_traces(line_color=BAR_COLOR)
                add_reference(fig_monthly_rate, sel_rate, f"Selection average {sel_rate:.1f}%", "h")
                plot_chart(
                    fig_monthly_rate,
                    alt="Line chart of the monthly unfavorable rate (%) for full months, with the selection average as a dashed line.",
                    key="monthly_unfavorable_rate"
                )
            else:
                st.info(
                    "No fully covered dataset month falls within the current filters. "
                    "The monthly rate trend is hidden to avoid a misleading comparison."
                )

            st.caption(
                "The volume chart includes all available months; gray bars mark "
                "months only partially covered by the original dataset. The "
                "unfavorable-rate trend excludes these partial source months. "
                "The KPIs and other charts still use all selected inspections. "
                "Date-range filters can also make the first or last selected month "
                "incomplete. Inspection targeting and publication delays may "
                "influence monthly comparisons."
            )

        else:
            st.info("No temporal data available for the selected filters.")
