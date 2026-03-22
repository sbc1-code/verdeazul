"""
VerdeAzul Dashboard
Community longevity potential index.
Verde = greens + money well spent. Azul = Blue Zone health.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from src import analytics

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="VerdeAzul",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Brand colors
VERDE = "#8a9a7b"
AZUL = "#5b8a9a"
BG = "#0b0b0b"
SURFACE = "#141414"
BORDER = "#222222"
TEXT = "#e0e0e0"
MUTED = "#777777"
CRITICAL = "#c45c5c"
THRIVING = "#8a9a7b"

QUADRANT_COLORS = {
    "thriving": THRIVING,
    "cultural_longevity": AZUL,
    "wealth_not_helping": "#c4a35c",
    "critical": CRITICAL,
}

QUADRANT_LABELS = {
    "thriving": "Thriving",
    "cultural_longevity": "Cultural Longevity",
    "wealth_not_helping": "Wealth Not Helping",
    "critical": "Critical Priority",
}

TIER_LABELS = {
    "proven": "Proven Blue Zone",
    "certified": "BZ Project Certified",
    "high_potential": "High Longevity",
    "emerging": "Emerging Potential",
    "unscored": "Baseline",
}

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------

st.markdown("""
<style>
    /* Hide default streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 400;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #777;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        border-bottom: 1px solid #222;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 20px;
        font-size: 0.85rem;
    }

    /* Brand header */
    .brand-header {
        font-size: 0.65rem;
        letter-spacing: 0.25em;
        text-transform: uppercase;
        color: #555;
        margin-bottom: 4px;
    }
    .brand-title {
        font-size: 1.6rem;
        font-weight: 300;
        color: #e0e0e0;
        margin-bottom: 4px;
    }
    .brand-sub {
        font-size: 0.85rem;
        color: #666;
        margin-bottom: 24px;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        border-right: 1px solid #222;
    }
</style>
""", unsafe_allow_html=True)


def plotly_layout(fig, height=400):
    """Apply VerdeAzul brand to any plotly figure."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=BG,
        plot_bgcolor=SURFACE,
        font=dict(color=TEXT, size=12),
        margin=dict(l=40, r=20, t=40, b=40),
        height=height,
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=11),
        ),
    )
    fig.update_xaxes(gridcolor=BORDER, zerolinecolor=BORDER)
    fig.update_yaxes(gridcolor=BORDER, zerolinecolor=BORDER)
    return fig


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.markdown('<p class="brand-header">community longevity potential index</p>', unsafe_allow_html=True)
st.markdown('<p class="brand-title">VerdeAzul</p>', unsafe_allow_html=True)
st.markdown('<p class="brand-sub">Verde = greens + money well spent | Azul = Blue Zone health. Any community can move the needle.</p>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_overview, tab_gap, tab_profile, tab_sql = st.tabs([
    "Pulse Overview", "Gap Analysis", "Community Profile", "SQL Lab"
])


# ===== TAB 1: OVERVIEW =====
with tab_overview:
    stats = analytics.get_overview_stats()
    s = stats.iloc[0]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Communities", int(s["total_communities"]))
    c2.metric("Avg Vida Index", s["avg_vida_index"])
    c3.metric("Avg Life Expectancy", f"{s['avg_life_expectancy']} yr")
    c4.metric("Thriving", int(s["thriving_count"]))
    c5.metric("Critical", int(s["critical_count"]))

    st.markdown("---")

    # Map
    map_df = analytics.get_community_map()

    fig_map = px.scatter_geo(
        map_df,
        lat="latitude",
        lon="longitude",
        color="quadrant",
        size="population",
        size_max=30,
        hover_name="name",
        hover_data={
            "state": True,
            "vida_index": ":.1f",
            "health_score": ":.1f",
            "wealth_score": ":.1f",
            "life_expectancy": ":.1f",
            "quadrant": True,
            "latitude": False,
            "longitude": False,
            "population": ":,",
        },
        color_discrete_map=QUADRANT_COLORS,
        category_orders={"quadrant": ["thriving", "cultural_longevity", "wealth_not_helping", "critical"]},
    )
    fig_map.update_geos(
        scope="north america",
        showland=True,
        landcolor="#1a1a1a",
        showocean=True,
        oceancolor="#0d1117",
        showcountries=True,
        countrycolor="#333",
        showlakes=True,
        lakecolor="#0d1117",
        bgcolor=BG,
        projection_type="natural earth",
    )
    fig_map = plotly_layout(fig_map, height=520)
    fig_map.update_layout(
        geo=dict(bgcolor=BG),
        legend_title_text="Quadrant",
    )
    # Rename legend entries
    for trace in fig_map.data:
        if trace.name in QUADRANT_LABELS:
            trace.name = QUADRANT_LABELS[trace.name]
    st.plotly_chart(fig_map, use_container_width=True)

    # Rankings table
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("##### Top 10 by Vida Index")
        rankings = analytics.get_rankings(limit=10)
        st.dataframe(
            rankings[["rank", "name", "state", "vida_index", "health_score", "wealth_score", "life_expectancy", "blue_zone_tier"]].rename(columns={
                "rank": "#", "name": "Community", "state": "State",
                "vida_index": "Vida", "health_score": "Health",
                "wealth_score": "Wealth", "life_expectancy": "Life Exp",
                "blue_zone_tier": "Tier",
            }),
            hide_index=True,
            use_container_width=True,
        )

    with col_right:
        st.markdown("##### Tier Benchmarks")
        tiers = analytics.get_tier_benchmarks()
        tiers["tier"] = tiers["tier"].map(TIER_LABELS)
        st.dataframe(
            tiers.rename(columns={
                "tier": "Tier", "communities": "N",
                "avg_vida": "Avg Vida", "avg_life_exp": "Life Exp",
                "avg_walkability": "Walk", "avg_food_access": "Food",
                "avg_income": "Income", "avg_poverty": "Poverty %",
                "avg_medical_debt": "Med Debt %",
            }),
            hide_index=True,
            use_container_width=True,
        )

    # Border comparison
    st.markdown("##### Border vs Non-Border Communities")
    border = analytics.get_border_comparison()
    st.dataframe(
        border.rename(columns={
            "category": "Type", "communities": "N",
            "avg_health": "Health", "avg_wealth": "Wealth",
            "avg_vida": "Vida", "avg_gap": "Gap",
            "avg_life_exp": "Life Exp", "avg_income": "Income",
            "avg_unbanked": "Unbanked %",
        }),
        hide_index=True,
        use_container_width=True,
    )


# ===== TAB 2: GAP ANALYSIS =====
with tab_gap:
    st.markdown("##### Health Score vs Wealth Score")
    st.markdown(
        '<p style="color: #666; font-size: 0.8rem;">'
        "Each dot is a community. Quadrants reveal where the imbalance is, "
        "and what type of intervention matters most."
        "</p>",
        unsafe_allow_html=True,
    )

    gap_df = analytics.get_gap_analysis()

    # Scatter: health vs wealth
    fig_gap = px.scatter(
        gap_df,
        x="wealth_score",
        y="health_score",
        color="quadrant",
        size="gap_score",
        size_max=25,
        hover_name="name",
        hover_data={
            "state": True,
            "vida_index": ":.1f",
            "gap_score": ":.1f",
            "gap_direction": True,
            "blue_zone_tier": True,
            "wealth_score": ":.1f",
            "health_score": ":.1f",
        },
        color_discrete_map=QUADRANT_COLORS,
        category_orders={"quadrant": ["thriving", "cultural_longevity", "wealth_not_helping", "critical"]},
    )

    # Quadrant lines
    fig_gap.add_hline(y=55, line_dash="dot", line_color="#444", line_width=1)
    fig_gap.add_vline(x=50, line_dash="dot", line_color="#444", line_width=1)

    # Quadrant labels
    label_style = dict(font=dict(size=10, color="#555"), showarrow=False, bgcolor="rgba(0,0,0,0)")
    fig_gap.add_annotation(x=25, y=78, text="Cultural Longevity", **label_style)
    fig_gap.add_annotation(x=75, y=78, text="Thriving", **label_style)
    fig_gap.add_annotation(x=75, y=35, text="Wealth Not Helping", **label_style)
    fig_gap.add_annotation(x=25, y=35, text="Critical Priority", **label_style)

    fig_gap = plotly_layout(fig_gap, height=550)
    fig_gap.update_layout(
        xaxis_title="Wealth Score",
        yaxis_title="Health Score",
        legend_title_text="Quadrant",
    )
    for trace in fig_gap.data:
        if trace.name in QUADRANT_LABELS:
            trace.name = QUADRANT_LABELS[trace.name]
    st.plotly_chart(fig_gap, use_container_width=True)

    # Quadrant summary
    st.markdown("##### Quadrant Summary")
    quad_df = analytics.get_quadrant_summary()
    quad_df["quadrant"] = quad_df["quadrant"].map(QUADRANT_LABELS)
    st.dataframe(
        quad_df.rename(columns={
            "quadrant": "Quadrant", "count": "Communities",
            "avg_vida": "Avg Vida", "avg_health": "Avg Health",
            "avg_wealth": "Avg Wealth", "avg_gap": "Avg Gap",
        }),
        hide_index=True,
        use_container_width=True,
    )

    # Highest-gap communities
    st.markdown("##### Largest Health-Wealth Gaps")
    gap_top = gap_df.nlargest(10, "gap_score")[
        ["name", "state", "health_score", "wealth_score", "gap_score", "gap_direction", "quadrant"]
    ].copy()
    gap_top["quadrant"] = gap_top["quadrant"].map(QUADRANT_LABELS)
    gap_top["gap_direction"] = gap_top["gap_direction"].str.replace("_", " ").str.title()
    st.dataframe(
        gap_top.rename(columns={
            "name": "Community", "state": "State",
            "health_score": "Health", "wealth_score": "Wealth",
            "gap_score": "Gap", "gap_direction": "Direction",
            "quadrant": "Quadrant",
        }),
        hide_index=True,
        use_container_width=True,
    )


# ===== TAB 3: COMMUNITY PROFILE =====
with tab_profile:
    map_df_for_select = analytics.get_community_map()
    community_options = dict(zip(
        map_df_for_select["name"] + ", " + map_df_for_select["state"],
        map_df_for_select["community_id"],
    ))

    selected_name = st.selectbox(
        "Select a community",
        options=list(community_options.keys()),
        index=list(community_options.keys()).index("El Paso, TX") if "El Paso, TX" in community_options else 0,
    )
    selected_id = community_options[selected_name]

    detail = analytics.get_community_detail(selected_id)
    if not detail.empty:
        d = detail.iloc[0]

        # Header metrics
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Vida Index", d["vida_index"])
        m2.metric("Health Score", d["health_score"])
        m3.metric("Wealth Score", d["wealth_score"])
        m4.metric("Life Expectancy", f"{d['life_expectancy']} yr")
        m5.metric("Percentile", f"{d['percentile_rank']}%")

        st.markdown(f"**Quadrant:** {QUADRANT_LABELS.get(d['quadrant'], d['quadrant'])} | "
                    f"**Gap:** {d['gap_score']} ({d['gap_direction'].replace('_', ' ')}) | "
                    f"**Tier:** {TIER_LABELS.get(d['blue_zone_tier'], d['blue_zone_tier'])} | "
                    f"**Region:** {d['region_name']}")

        st.markdown("---")

        col_health, col_wealth = st.columns(2)

        with col_health:
            st.markdown("##### Health Metrics")
            health_cats = ["Insurance", "Mental Health", "Preventive Care", "Walkability", "Food Access"]
            health_vals = [d["insurance_coverage_pct"], d["mental_health_score"],
                           d["preventive_care_pct"], d["walkability_score"], d["food_access_score"]]

            fig_h = go.Figure()
            fig_h.add_trace(go.Scatterpolar(
                r=health_vals + [health_vals[0]],
                theta=health_cats + [health_cats[0]],
                fill="toself",
                fillcolor=f"rgba(138,154,123,0.15)",
                line=dict(color=VERDE, width=2),
                name="This Community",
            ))
            fig_h = plotly_layout(fig_h, height=320)
            fig_h.update_layout(
                polar=dict(
                    bgcolor=SURFACE,
                    radialaxis=dict(visible=True, range=[0, 100], gridcolor=BORDER, color=MUTED),
                    angularaxis=dict(gridcolor=BORDER, color=TEXT),
                ),
            )
            st.plotly_chart(fig_h, use_container_width=True)

            st.markdown(f"""
            | Metric | Value |
            |--------|-------|
            | Diabetes Rate | {d['diabetes_rate']}% |
            | Heart Disease | {d['heart_disease_rate']}% |
            | Obesity Rate | {d['obesity_rate']}% |
            | Air Quality (AQI) | {d['air_quality_index']} |
            """)

        with col_wealth:
            st.markdown("##### Financial Metrics")
            wealth_cats = ["Income", "Low Poverty", "Banking Access", "Low Med Debt", "Small Biz"]
            inc_norm = min((d["median_income"] - 20000) / 100000 * 100, 100)
            pov_norm = 100 - d["poverty_rate"] * 2.2
            bank_norm = d["bank_branches_per_10k"] / 8 * 100
            debt_norm = 100 - d["medical_debt_rate"] * 2.2
            biz_norm = d["small_biz_density"] / 15 * 100
            wealth_vals = [inc_norm, pov_norm, bank_norm, debt_norm, biz_norm]

            fig_w = go.Figure()
            fig_w.add_trace(go.Scatterpolar(
                r=wealth_vals + [wealth_vals[0]],
                theta=wealth_cats + [wealth_cats[0]],
                fill="toself",
                fillcolor=f"rgba(91,138,154,0.15)",
                line=dict(color=AZUL, width=2),
                name="This Community",
            ))
            fig_w = plotly_layout(fig_w, height=320)
            fig_w.update_layout(
                polar=dict(
                    bgcolor=SURFACE,
                    radialaxis=dict(visible=True, range=[0, 100], gridcolor=BORDER, color=MUTED),
                    angularaxis=dict(gridcolor=BORDER, color=TEXT),
                ),
            )
            st.plotly_chart(fig_w, use_container_width=True)

            st.markdown(f"""
            | Metric | Value |
            |--------|-------|
            | Median Income | ${d['median_income']:,} |
            | Poverty Rate | {d['poverty_rate']}% |
            | Unbanked Rate | {d['unbanked_rate']}% |
            | Medical Debt | {d['medical_debt_rate']}% |
            | Cost of Living | {d['cost_of_living_index']} |
            """)

        # Trend chart
        st.markdown("---")
        st.markdown("##### Vida Index Trend")
        trend = analytics.get_community_trend(selected_id)
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=trend["period"], y=trend["vida_index"],
            mode="lines+markers", name="Vida Index",
            line=dict(color=VERDE, width=2),
            marker=dict(size=8),
        ))
        fig_trend.add_trace(go.Scatter(
            x=trend["period"], y=trend["health_score"],
            mode="lines", name="Health",
            line=dict(color=VERDE, width=1, dash="dot"),
        ))
        fig_trend.add_trace(go.Scatter(
            x=trend["period"], y=trend["wealth_score"],
            mode="lines", name="Wealth",
            line=dict(color=AZUL, width=1, dash="dot"),
        ))
        fig_trend = plotly_layout(fig_trend, height=280)
        fig_trend.update_layout(yaxis_title="Score (0-100)")
        st.plotly_chart(fig_trend, use_container_width=True)

        # Interventions
        st.markdown("---")
        st.markdown("##### Recommended Interventions")
        st.markdown(
            '<p style="color: #666; font-size: 0.8rem;">'
            "Ranked by estimated Vida Index impact. These are practical, "
            "council-level actions this community can take."
            "</p>",
            unsafe_allow_html=True,
        )
        interventions = analytics.get_interventions(selected_id)
        if not interventions.empty:
            for _, row in interventions.iterrows():
                cost_badge = {"low": "Low Cost", "medium": "Mid Cost", "high": "High Cost"}
                st.markdown(
                    f"**{row['priority_rank']}.** {row['title']}  \n"
                    f"*{row['category'].replace('_', ' ').title()}* | "
                    f"{cost_badge.get(row['cost_tier'], row['cost_tier'])} | "
                    f"+{row['estimated_impact']} pts projected  \n"
                    f"{row['description']}"
                )
                st.markdown("")
        else:
            st.info("No interventions generated for this community.")


# ===== TAB 4: SQL LAB =====
with tab_sql:
    st.markdown("##### SQL Analytics Showcase")
    st.markdown(
        '<p style="color: #666; font-size: 0.8rem;">'
        "The queries powering this dashboard. CTEs, window functions, "
        "percentile rankings, gap analysis."
        "</p>",
        unsafe_allow_html=True,
    )

    # Read queries.sql and split into individual queries
    from pathlib import Path
    queries_text = Path("queries.sql").read_text()
    query_blocks = []
    current_title = ""
    current_sql = ""

    for line in queries_text.split("\n"):
        if line.startswith("-- ") and line[3:4].isdigit():
            if current_sql.strip():
                query_blocks.append((current_title, current_sql.strip()))
            current_title = line.lstrip("- ").strip()
            current_sql = ""
        else:
            current_sql += line + "\n"
    if current_sql.strip():
        query_blocks.append((current_title, current_sql.strip()))

    selected_query = st.selectbox(
        "Select a query",
        options=[title for title, _ in query_blocks],
    )

    for title, sql in query_blocks:
        if title == selected_query:
            st.code(sql, language="sql")
            # Run it
            try:
                from sqlalchemy import text as sa_text
                from src.database import get_engine
                engine = get_engine()
                with engine.connect() as conn:
                    result_df = pd.read_sql(sa_text(sql), conn)
                st.dataframe(result_df, use_container_width=True, hide_index=True)
            except Exception as e:
                st.error(f"Query error: {e}")
            break


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.markdown("---")
st.markdown(
    '<p style="text-align: center; color: #444; font-size: 0.7rem; letter-spacing: 0.1em;">'
    "VERDEAZUL | Built with Python, SQL, Streamlit"
    "</p>",
    unsafe_allow_html=True,
)
