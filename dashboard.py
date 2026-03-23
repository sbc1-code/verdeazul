"""VerdeAzul Dashboard"""

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
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Theme system
# ---------------------------------------------------------------------------

THEMES = {
    "light": {
        "verde": "#6b7a5e",
        "azul": "#4a7a8a",
        "bg": "#ffffff",
        "surface": "#f8f8f7",
        "border": "#e5e5e5",
        "text": "#1d1d1f",
        "muted": "#86868b",
        "critical": "#bf4040",
        "warm": "#b8923e",
        "body_text": "#424245",
        "desc_text": "#6e6e73",
        "border_hover": "#d2d2d7",
        "grid": "#f0f0f0",
        "zeroline": "#e5e5e5",
        "annotation_bg": "rgba(255,255,255,0.7)",
        "annotation_text": "#b0b0b0",
        "marker_line": "#1d1d1f",
        "land": "#f0f0ed",
        "ocean": "#e8eef3",
        "country_line": "#d2d2d7",
        "lake": "#e8eef3",
        "plotly_template": "plotly_white",
        "verde_badge_bg": "rgba(107,122,94,0.08)",
        "verde_badge_border": "rgba(107,122,94,0.2)",
        "footer_color": "#d2d2d7",
    },
    "dark": {
        "verde": "#8a9a7b",
        "azul": "#5b8a9a",
        "bg": "#0b0b0b",
        "surface": "#141414",
        "border": "#222222",
        "text": "#e5e5e5",
        "muted": "#8a8a8e",
        "critical": "#d4605b",
        "warm": "#d4a84b",
        "body_text": "#b0b0b4",
        "desc_text": "#909094",
        "border_hover": "#333333",
        "grid": "#1a1a1a",
        "zeroline": "#222222",
        "annotation_bg": "rgba(11,11,11,0.7)",
        "annotation_text": "#666666",
        "marker_line": "#e5e5e5",
        "land": "#161616",
        "ocean": "#0e1215",
        "country_line": "#2a2a2a",
        "lake": "#0e1215",
        "plotly_template": "plotly_dark",
        "verde_badge_bg": "rgba(138,154,123,0.12)",
        "verde_badge_border": "rgba(138,154,123,0.3)",
        "footer_color": "#333333",
    },
}

# Initialize theme state
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# Theme toggle in the header area
_header_left, _header_spacer, _header_right = st.columns([6, 3, 1])
with _header_right:
    dark_mode = st.toggle(
        "Dark",
        value=st.session_state.dark_mode,
        key="theme_toggle",
        help="Switch between light and dark mode",
    )
    st.session_state.dark_mode = dark_mode

# Resolve active palette
T = THEMES["dark"] if st.session_state.dark_mode else THEMES["light"]

# Convenience aliases used throughout
VERDE = T["verde"]
AZUL = T["azul"]
BG = T["bg"]
SURFACE = T["surface"]
BORDER = T["border"]
TEXT = T["text"]
MUTED = T["muted"]
CRITICAL = T["critical"]
WARM = T["warm"]

PLOTLY_CONFIG = {"displayModeBar": False}

QUADRANT_COLORS = {
    "thriving": VERDE,
    "cultural_longevity": AZUL,
    "wealth_not_helping": WARM,
    "critical": CRITICAL,
}

QUADRANT_LABELS = {
    "thriving": "Thriving",
    "cultural_longevity": "Healthy, Not Wealthy",
    "wealth_not_helping": "Wealthy, Not Healthy",
    "critical": "Needs Attention",
}

QUADRANT_DESCRIPTIONS = {
    "thriving": "Strong healthcare access, nutritious food, and financial infrastructure. The model to study.",
    "cultural_longevity": "Good health outcomes despite limited economic resources. Rooted in diet, community ties, and walkable environments.",
    "wealth_not_helping": "Income is there, but food deserts, poor walkability, or preventive care gaps hold outcomes back.",
    "critical": "Limited access to both healthcare and financial services. Where targeted investment goes furthest.",
}

TIER_LABELS = {
    "proven": "Proven Blue Zone",
    "certified": "BZ Certified",
    "high_potential": "High Longevity",
    "emerging": "Emerging",
    "unscored": "Baseline",
}

# ---------------------------------------------------------------------------
# CSS (dynamically injected based on theme)
# ---------------------------------------------------------------------------

st.markdown(f"""
<style>
    #MainMenu, footer, header {{visibility: hidden;}}

    /* Dark mode: override Streamlit's base colors via CSS custom properties */
    {"" if not st.session_state.dark_mode else '''
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"],
    .main, .block-container, section[data-testid="stSidebar"] {
        background-color: #0b0b0b !important;
        color: #e5e5e5 !important;
    }
    [data-testid="stAppViewBlockContainer"] {
        background-color: #0b0b0b !important;
    }
    .stMarkdown, .stMarkdown p, .stMarkdown span, .stMarkdown li,
    .stText, label, .stSelectbox label, .stRadio label {
        color: #e5e5e5 !important;
    }
    [data-testid="stDataFrame"], [data-testid="stTable"] {
        color: #e5e5e5 !important;
    }
    .stSelectbox [data-baseweb="select"],
    .stSelectbox [data-baseweb="select"] * {
        background-color: #141414 !important;
        color: #e5e5e5 !important;
        border-color: #222 !important;
    }
    [data-baseweb="popover"], [data-baseweb="menu"],
    [data-baseweb="popover"] *, [data-baseweb="menu"] * {
        background-color: #141414 !important;
        color: #e5e5e5 !important;
    }
    [data-baseweb="popover"] li:hover, [data-baseweb="menu"] li:hover {
        background-color: #222 !important;
    }
    pre, code {
        background-color: #141414 !important;
        color: #e5e5e5 !important;
    }
    iframe[title="streamlit_dataframe.dataframe"] {
        background-color: #141414 !important;
    }
    '''}

    [data-testid="stMetricValue"] {{
        font-size: 2.4rem;
        font-weight: 300;
        letter-spacing: -0.03em;
        color: {T["text"]};
    }}
    [data-testid="stMetricLabel"] {{
        font-size: 0.68rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: {T["muted"]};
    }}
    [data-testid="stMetricDelta"] {{
        color: {T["muted"]} !important;
    }}
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0;
        border-bottom: 1px solid {T["border"]};
    }}
    .stTabs [data-baseweb="tab"] {{
        padding: 10px 24px;
        font-size: 0.78rem;
        letter-spacing: 0.05em;
        color: {T["muted"]};
    }}
    .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        color: {T["text"]};
    }}
    .va-mark {{
        font-size: 2rem;
        font-weight: 600;
        color: {T["text"]};
        letter-spacing: -0.02em;
        margin: 0 0 6px 0;
        line-height: 1;
    }}
    .va-mark span.verde {{ color: {T["verde"]}; }}
    .va-mark span.azul {{ color: {T["azul"]}; }}
    .va-hook {{
        font-size: 1.1rem;
        color: {T["text"]};
        margin: 0 0 6px 0;
        font-weight: 400;
        line-height: 1.5;
    }}
    .va-sub {{
        font-size: 0.82rem;
        color: {T["muted"]};
        margin: 0 0 36px 0;
        line-height: 1.6;
    }}
    .section-label {{
        font-size: 0.62rem;
        letter-spacing: 0.22em;
        text-transform: uppercase;
        color: {T["muted"]};
        margin: 36px 0 14px 0;
    }}
    .insight {{
        background: {T["surface"]};
        border: 1px solid {T["border"]};
        border-left: 3px solid {T["verde"]};
        border-radius: 10px;
        padding: 18px 22px;
        margin: 20px 0;
    }}
    .insight p {{
        font-size: 0.88rem;
        color: {T["body_text"]};
        line-height: 1.65;
        margin: 0;
    }}
    .insight strong {{ color: {T["text"]}; }}
    .quad-card {{
        background: {T["surface"]};
        border-radius: 10px;
        padding: 16px 18px;
        border-left: 3px solid;
        min-height: 110px;
    }}
    .quad-name {{
        font-size: 0.82rem;
        font-weight: 600;
        margin-bottom: 6px;
    }}
    .quad-desc {{
        font-size: 0.74rem;
        color: {T["desc_text"]};
        line-height: 1.55;
    }}
    .inv-card {{
        background: {T["surface"]};
        border: 1px solid {T["border"]};
        border-radius: 10px;
        padding: 18px 22px;
        margin-bottom: 10px;
    }}
    .inv-card:hover {{ border-color: {T["border_hover"]}; }}
    .inv-title {{
        font-size: 0.92rem;
        color: {T["text"]};
        font-weight: 500;
        margin-bottom: 5px;
    }}
    .inv-meta {{
        font-size: 0.7rem;
        color: {T["muted"]};
        letter-spacing: 0.04em;
        margin-bottom: 8px;
    }}
    .inv-desc {{
        font-size: 0.8rem;
        color: {T["desc_text"]};
        line-height: 1.55;
    }}
    .inv-impact {{
        display: inline-block;
        font-size: 0.7rem;
        color: {T["verde"]};
        background: {T["verde_badge_bg"]};
        border: 1px solid {T["verde_badge_border"]};
        padding: 2px 10px;
        border-radius: 12px;
        margin-left: 10px;
        font-weight: 600;
    }}
    .community-name {{
        font-size: 1.6rem;
        font-weight: 600;
        color: {T["text"]};
        margin: 8px 0 2px 0;
    }}
    .community-context {{
        font-size: 0.78rem;
        color: {T["muted"]};
        margin: 0 0 20px 0;
    }}
    .projection {{
        background: {T["surface"]};
        border: 1px solid {T["border"]};
        border-radius: 12px;
        padding: 20px 24px;
        margin: 16px 0;
    }}
    .projection-label {{
        font-size: 0.65rem;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        color: {T["muted"]};
        margin-bottom: 8px;
    }}
    .projection-row {{
        display: flex;
        align-items: baseline;
        gap: 12px;
    }}
    .projection-current {{
        font-size: 1.6rem;
        font-weight: 300;
        color: {T["muted"]};
    }}
    .projection-arrow {{ font-size: 1rem; color: {T["border_hover"]}; }}
    .projection-after {{
        font-size: 1.6rem;
        font-weight: 600;
        color: {T["verde"]};
    }}
    .projection-delta {{
        font-size: 0.78rem;
        color: {T["verde"]};
    }}
    [data-testid="stSidebar"] {{ border-right: 1px solid {T["border"]}; }}
</style>
""", unsafe_allow_html=True)


def plotly_layout(fig, height=400):
    fig.update_layout(
        template=T["plotly_template"],
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        font=dict(color=TEXT, size=12, family="system-ui, -apple-system, sans-serif"),
        margin=dict(l=40, r=20, t=30, b=40),
        height=height,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11, color=TEXT)),
    )
    fig.update_xaxes(gridcolor=T["grid"], zerolinecolor=T["zeroline"])
    fig.update_yaxes(gridcolor=T["grid"], zerolinecolor=T["zeroline"])
    return fig


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

with _header_left:
    st.markdown(
        '<p class="va-mark"><span class="verde">Verde</span><span class="azul">Azul</span></p>',
        unsafe_allow_html=True,
    )

st.markdown(
    '<p class="va-hook">How healthy can your community actually become?</p>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="va-sub">VerdeAzul scores communities on two things that determine how long people live: '
    'access to healthcare and nutritious food, and access to economic opportunity. '
    'Then it shows what to fix first.</p>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_overview, tab_explore, tab_community, tab_under = st.tabs([
    "Overview", "Explore", "Your Community", "Under the Hood"
])

# Get quadrant thresholds (used by multiple tabs)
H_THRESHOLD, W_THRESHOLD = analytics.get_quadrant_thresholds()


# ===== TAB 1: OVERVIEW =====
with tab_overview:
    stats = analytics.get_overview_stats()
    s = stats.iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Counties Scored", f"{int(s['total_communities']):,}")
    c2.metric("Average Health", f"{s['avg_health_score']}")
    c3.metric("Average Economic", f"{s['avg_wealth_score']}")
    c4.metric("Average Score", f"{s['avg_vida_index']}")

    map_df = analytics.get_community_map()

    fig_map = px.scatter_geo(
        map_df,
        lat="latitude",
        lon="longitude",
        color="quadrant",
        size="population",
        size_max=35,
        hover_name="name",
        hover_data={
            "state": True,
            "vida_index": ":.1f",
            "quadrant": False,
            "latitude": False,
            "longitude": False,
            "population": False,
        },
        color_discrete_map=QUADRANT_COLORS,
        category_orders={"quadrant": list(QUADRANT_LABELS.keys())},
        labels={"vida_index": "Score", "state": "State"},
    )
    fig_map.update_geos(
        scope="north america",
        showland=True, landcolor=T["land"],
        showocean=True, oceancolor=T["ocean"],
        showcountries=True, countrycolor=T["country_line"],
        showlakes=True, lakecolor=T["lake"],
        bgcolor=BG,
        projection_type="natural earth",
        center=dict(lat=32, lon=-100),
        lataxis=dict(range=[8, 52]),
        lonaxis=dict(range=[-130, -65]),
    )
    fig_map = plotly_layout(fig_map, height=480)
    fig_map.update_layout(geo=dict(bgcolor=BG), legend_title_text="")
    for trace in fig_map.data:
        if trace.name in QUADRANT_LABELS:
            trace.name = QUADRANT_LABELS[trace.name]
    st.plotly_chart(fig_map, use_container_width=True, config=PLOTLY_CONFIG)

    # Quadrant explainers
    st.markdown('<p class="section-label">What the colors mean</p>', unsafe_allow_html=True)
    qcols = st.columns(4)
    for i, (key, label) in enumerate(QUADRANT_LABELS.items()):
        color = QUADRANT_COLORS[key]
        desc = QUADRANT_DESCRIPTIONS[key]
        with qcols[i]:
            st.markdown(
                f'<div class="quad-card" style="border-left-color: {color};">'
                f'<div class="quad-name" style="color: {color};">{label}</div>'
                f'<div class="quad-desc">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # Insight
    thriving = int(s["thriving_count"])
    critical = int(s["critical_count"])
    st.markdown(
        f'<div class="insight"><p>'
        f'Of {int(s["total_communities"])} communities scored, '
        f'<strong>{thriving}</strong> are thriving across both health and economic dimensions, '
        f'while <strong>{critical}</strong> need attention in both. '
        f'The rest sit in between, where a single well-placed investment '
        f'in food access, preventive care, or financial services could shift the trajectory.'
        f'</p></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<p class="section-label">Highest-scoring communities</p>', unsafe_allow_html=True)
    rankings = analytics.get_rankings(limit=10)
    display_rankings = rankings[["rank", "name", "state", "vida_index", "health_score", "wealth_score", "blue_zone_tier"]].copy()
    display_rankings["blue_zone_tier"] = display_rankings["blue_zone_tier"].map(TIER_LABELS)
    st.dataframe(
        display_rankings.rename(columns={
            "rank": "#", "name": "County", "state": "State",
            "vida_index": "Score", "health_score": "Health",
            "wealth_score": "Economic", "blue_zone_tier": "Tier",
        }),
        hide_index=True, use_container_width=True,
    )


# ===== TAB 2: EXPLORE =====
with tab_explore:
    st.markdown(
        '<p class="section-label">Health Outcomes vs Economic Access</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "Each dot is a community. The bigger the dot, the larger the gap between its health and economic scores."
    )
    st.markdown("")

    gap_df = analytics.get_gap_analysis()

    fig_gap = px.scatter(
        gap_df,
        x="wealth_score",
        y="health_score",
        color="quadrant",
        size="gap_score",
        size_max=24,
        hover_name="name",
        hover_data={
            "state": True,
            "vida_index": ":.1f",
            "gap_score": ":.1f",
            "gap_direction": False,
            "blue_zone_tier": False,
            "wealth_score": ":.1f",
            "health_score": ":.1f",
        },
        color_discrete_map=QUADRANT_COLORS,
        category_orders={"quadrant": list(QUADRANT_LABELS.keys())},
        labels={
            "wealth_score": "Economic Access",
            "health_score": "Health Outcomes",
            "vida_index": "Score",
            "gap_score": "Gap",
            "state": "State",
        },
    )

    # Dynamic quadrant lines from actual medians
    fig_gap.add_hline(y=H_THRESHOLD, line_dash="dot", line_color=T["border_hover"], line_width=1)
    fig_gap.add_vline(x=W_THRESHOLD, line_dash="dot", line_color=T["border_hover"], line_width=1)

    # Quadrant labels positioned relative to data
    h_min, h_max = gap_df["health_score"].min() - 2, gap_df["health_score"].max() + 2
    w_min, w_max = gap_df["wealth_score"].min() - 2, gap_df["wealth_score"].max() + 2
    ann = dict(font=dict(size=10, color=T["annotation_text"]), showarrow=False, bgcolor=T["annotation_bg"])
    fig_gap.add_annotation(x=(w_min + W_THRESHOLD) / 2, y=h_max, text="Healthy, Not Wealthy", **ann)
    fig_gap.add_annotation(x=(w_max + W_THRESHOLD) / 2, y=h_max, text="Thriving", **ann)
    fig_gap.add_annotation(x=(w_max + W_THRESHOLD) / 2, y=h_min, text="Wealthy, Not Healthy", **ann)
    fig_gap.add_annotation(x=(w_min + W_THRESHOLD) / 2, y=h_min, text="Needs Attention", **ann)

    fig_gap = plotly_layout(fig_gap, height=540)
    fig_gap.update_layout(
        xaxis_title="Economic Access",
        yaxis_title="Health Outcomes",
        legend_title_text="",
    )
    for trace in fig_gap.data:
        if trace.name in QUADRANT_LABELS:
            trace.name = QUADRANT_LABELS[trace.name]
    st.plotly_chart(fig_gap, use_container_width=True, config=PLOTLY_CONFIG)

    # Dynamic insight from cultural_longevity quadrant
    cultural = gap_df[gap_df["quadrant"] == "cultural_longevity"]
    if not cultural.empty:
        ex = cultural.iloc[0]
        st.markdown(
            f'<div class="insight"><p>'
            f'<strong>{ex["name"]}, {ex["state"]}</strong> scores '
            f'{ex["health_score"]:.0f} on health but only {ex["wealth_score"]:.0f} on economic access. '
            f'Communities like this often rely on traditional diets, walkable neighborhoods, '
            f'and strong social networks rather than expensive healthcare systems. '
            f'Understanding what works here is the key to replicable models.'
            f'</p></div>',
            unsafe_allow_html=True,
        )

    # Wealthy-not-healthy insight
    wnp = gap_df[gap_df["quadrant"] == "wealth_not_helping"]
    if not wnp.empty:
        wx = wnp.iloc[0]
        st.markdown(
            f'<div class="insight" style="border-left-color: {T["warm"]};"><p>'
            f'<strong>{wx["name"]}, {wx["state"]}</strong> has economic access '
            f'({wx["wealth_score"]:.0f}) well ahead of its health outcomes ({wx["health_score"]:.0f}). '
            f'This pattern often points to car-dependent sprawl, fast food density, '
            f'or gaps in preventive care, things money alone won\'t fix.'
            f'</p></div>',
            unsafe_allow_html=True,
        )

    # Quadrant breakdown
    st.markdown('<p class="section-label">By category</p>', unsafe_allow_html=True)
    quad_df = analytics.get_quadrant_summary()
    quad_df["quadrant"] = quad_df["quadrant"].map(QUADRANT_LABELS)
    st.dataframe(
        quad_df.rename(columns={
            "quadrant": "Category", "count": "Communities",
            "avg_vida": "Avg Score", "avg_health": "Health",
            "avg_wealth": "Economic", "avg_gap": "Gap",
        }),
        hide_index=True, use_container_width=True,
    )

    # Border comparison
    st.markdown('<p class="section-label">Border vs non-border communities</p>', unsafe_allow_html=True)
    border = analytics.get_border_comparison()
    border_display = border[["category", "communities", "avg_health", "avg_wealth", "avg_vida", "avg_gap", "avg_income"]].copy()
    st.dataframe(
        border_display.rename(columns={
            "category": "Type", "communities": "N",
            "avg_health": "Health", "avg_wealth": "Economic",
            "avg_vida": "Score", "avg_gap": "Gap",
            "avg_income": "Income",
        }),
        hide_index=True, use_container_width=True,
    )

    if len(border) == 2:
        b_row = border[border["category"] == "Border"].iloc[0]
        nb_row = border[border["category"] == "Non-Border"].iloc[0]
        health_gap = nb_row["avg_health"] - b_row["avg_health"]
        income_gap = nb_row["avg_income"] - b_row["avg_income"]
        if health_gap > 0:
            st.markdown(
                f'<div class="insight"><p>'
                f'Border communities score <strong>{health_gap:.1f} points lower</strong> on health '
                f'and earn <strong>${income_gap:,.0f} less</strong> in median income '
                f'than non-border communities, despite strong cultural health practices, '
                f'multigenerational households, and traditional diets. The gap is driven by '
                f'economic access: insurance coverage, preventive care, and banking infrastructure.'
                f'</p></div>',
                unsafe_allow_html=True,
            )


# ===== TAB 3: YOUR COMMUNITY =====
with tab_community:
    map_df_for_select = analytics.get_community_map()
    community_options = dict(zip(
        map_df_for_select["name"] + ", " + map_df_for_select["state"],
        map_df_for_select["community_id"],
    ))

    selected_name = st.selectbox(
        "Choose a community",
        options=list(community_options.keys()),
        index=list(community_options.keys()).index("El Paso, TX") if "El Paso, TX" in community_options else 0,
    )
    selected_id = community_options[selected_name]

    detail = analytics.get_community_detail(selected_id)
    if not detail.empty:
        d = detail.iloc[0]

        quadrant_label = QUADRANT_LABELS.get(d['quadrant'], d['quadrant'])
        tier_label = TIER_LABELS.get(d['blue_zone_tier'], d['blue_zone_tier'])
        q_color = QUADRANT_COLORS.get(d["quadrant"], MUTED)

        st.markdown(
            f'<p class="community-name">{d["name"]}, {d["state"]}</p>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<p class="community-context">'
            f'<span style="color: {q_color};">{quadrant_label}</span>'
            f'&ensp;·&ensp;{tier_label}&ensp;·&ensp;{d["region_name"]}'
            f'&ensp;·&ensp;Pop. {d["population"]:,}'
            f'</p>',
            unsafe_allow_html=True,
        )

        # Get national averages for comparison
        natl = analytics.get_national_averages()
        n = natl.iloc[0] if not natl.empty else None

        m1, m2, m3, m4 = st.columns(4)
        vida_vs = f"vs {n['avg_vida']:.0f} avg" if n is not None else ""
        m1.metric("Overall Score", f"{d['vida_index']}", delta=vida_vs, delta_color="off")
        h_vs = f"vs {n['avg_insurance']:.0f} avg" if n is not None else ""
        m2.metric("Health Score", f"{d['health_score']}", delta=h_vs, delta_color="off")
        w_vs = f"vs {n['avg_poverty']:.0f}% avg" if n is not None else ""
        m3.metric("Poverty Rate", f"{d['poverty_rate']}%" if d['poverty_rate'] is not None else "N/A", delta=w_vs, delta_color="off")
        pctl = d['percentile_rank']
        m4.metric("Ranked", f"Top {100 - pctl:.0f}%" if pctl >= 50 else f"Bottom {pctl:.0f}%")

        # Bar charts with national average markers
        col_h, col_f = st.columns(2)

        with col_h:
            st.markdown('<p class="section-label">Health profile vs national average</p>', unsafe_allow_html=True)
            h_metrics = ["Insurance", "Mental Health", "Preventive Care"]
            h_vals = [d["insurance_coverage_pct"] or 0, d["mental_health_score"] or 0,
                      d["preventive_care_pct"] or 0]
            h_avgs = [n["avg_insurance"], n["avg_mental"], n["avg_preventive"]] if n is not None else [50]*3

            fig_h = go.Figure()
            fig_h.add_trace(go.Bar(
                y=h_metrics, x=h_vals, orientation="h",
                marker_color=VERDE, marker_line_width=0,
                name=d["name"],
            ))
            fig_h.add_trace(go.Scatter(
                y=h_metrics, x=h_avgs, mode="markers",
                marker=dict(symbol="line-ns", size=14, line=dict(width=2, color=T["marker_line"])),
                name="National Avg",
            ))
            fig_h.update_xaxes(range=[0, 100], title="")
            fig_h.update_yaxes(title="")
            fig_h = plotly_layout(fig_h, height=220)
            fig_h.update_layout(
                margin=dict(l=10, r=20, t=10, b=20), showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(size=10)),
            )
            st.plotly_chart(fig_h, use_container_width=True, config=PLOTLY_CONFIG)

        with col_f:
            st.markdown('<p class="section-label">Economic profile vs national average</p>', unsafe_allow_html=True)
            income = d["median_income"] or 50000
            poverty = d["poverty_rate"] or 13
            inc_n_val = min(max((income - 20000) / 130000 * 100, 0), 100)
            pov_n_val = max(100 - poverty * 2.2, 0)
            f_metrics = ["Income", "Low Poverty"]
            f_vals = [inc_n_val, pov_n_val]

            if n is not None:
                f_avgs = [
                    min(max((n["avg_income"] - 20000) / 130000 * 100, 0), 100),
                    max(100 - n["avg_poverty"] * 2.2, 0),
                ]
            else:
                f_avgs = [50]*2

            fig_f = go.Figure()
            fig_f.add_trace(go.Bar(
                y=f_metrics, x=f_vals, orientation="h",
                marker_color=AZUL, marker_line_width=0,
                name=d["name"],
            ))
            fig_f.add_trace(go.Scatter(
                y=f_metrics, x=f_avgs, mode="markers",
                marker=dict(symbol="line-ns", size=14, line=dict(width=2, color=T["marker_line"])),
                name="National Avg",
            ))
            fig_f.update_xaxes(range=[0, 100], title="")
            fig_f.update_yaxes(title="")
            fig_f = plotly_layout(fig_f, height=220)
            fig_f.update_layout(
                margin=dict(l=10, r=20, t=10, b=20), showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(size=10)),
            )
            st.plotly_chart(fig_f, use_container_width=True, config=PLOTLY_CONFIG)

        # Trend
        st.markdown('<p class="section-label">Quarterly trend</p>', unsafe_allow_html=True)
        trend = analytics.get_community_trend(selected_id)
        fig_t = go.Figure()
        fig_t.add_trace(go.Scatter(
            x=trend["period"], y=trend["vida_index"],
            mode="lines+markers", name="Overall",
            line=dict(color=VERDE, width=2.5), marker=dict(size=7),
        ))
        fig_t.add_trace(go.Scatter(
            x=trend["period"], y=trend["health_score"],
            mode="lines", name="Health",
            line=dict(color=VERDE, width=1, dash="dot"), opacity=0.5,
        ))
        fig_t.add_trace(go.Scatter(
            x=trend["period"], y=trend["wealth_score"],
            mode="lines", name="Economic",
            line=dict(color=AZUL, width=1, dash="dot"), opacity=0.5,
        ))
        fig_t = plotly_layout(fig_t, height=250)
        fig_t.update_layout(
            yaxis_title="",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_t, use_container_width=True, config=PLOTLY_CONFIG)

        # Peer communities
        st.markdown('<p class="section-label">Similar communities</p>', unsafe_allow_html=True)
        peers = analytics.get_peer_communities(selected_id)
        if not peers.empty:
            peers_display = peers[["name", "state", "vida_index", "health_score", "wealth_score", "quadrant"]].copy()
            peers_display["quadrant"] = peers_display["quadrant"].map(QUADRANT_LABELS)
            st.dataframe(
                peers_display.rename(columns={
                    "name": "Community", "state": "State",
                    "vida_index": "Score", "health_score": "Health",
                    "wealth_score": "Economic", "quadrant": "Category",
                }),
                hide_index=True, use_container_width=True,
            )

        # Interventions with projection
        interventions = analytics.get_interventions(selected_id)
        if not interventions.empty:
            total_impact = interventions["estimated_impact"].sum()
            current_vida = d["vida_index"]
            projected = min(current_vida + total_impact, 100)

            st.markdown(
                f'<div class="projection">'
                f'<div class="projection-label">If all recommended actions are implemented</div>'
                f'<div class="projection-row">'
                f'<span class="projection-current">{current_vida}</span>'
                f'<span class="projection-arrow">&#8594;</span>'
                f'<span class="projection-after">{projected:.1f}</span>'
                f'<span class="projection-delta">+{total_impact:.1f} points</span>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

            st.markdown('<p class="section-label">Recommended actions</p>', unsafe_allow_html=True)
            for _, row in interventions.iterrows():
                cost_label = {"low": "Low cost", "medium": "Moderate cost", "high": "Significant investment"}
                cat_label = row["category"].replace("_", " ").title()
                st.markdown(
                    f'<div class="inv-card">'
                    f'<div class="inv-title">{row["title"]}'
                    f'<span class="inv-impact">+{row["estimated_impact"]} pts</span></div>'
                    f'<div class="inv-meta">{cat_label} · {cost_label.get(row["cost_tier"], row["cost_tier"])}</div>'
                    f'<div class="inv-desc">{row["description"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                '<div class="insight"><p>'
                'This community is performing well across both dimensions. '
                'Focus on sustaining what works: food systems, walkable infrastructure, '
                'and the financial services in place.'
                '</p></div>',
                unsafe_allow_html=True,
            )


# ===== TAB 4: UNDER THE HOOD =====
with tab_under:
    st.markdown('<p class="section-label">How it works</p>', unsafe_allow_html=True)
    st.markdown(
        "VerdeAzul scores communities on two dimensions: **health outcomes** "
        "(chronic disease rates, insurance coverage, preventive care, walkability, "
        "access to nutritious food, air quality) and **economic access** "
        "(income, poverty, banking availability, medical debt, local business density). "
        "The gap between the two tells us whether a community needs better food and "
        "healthcare infrastructure, stronger financial services, or both."
    )
    st.markdown("")
    st.markdown(
        "The queries below power the dashboard. "
        "CTEs, window functions, percentile rankings, and gap analysis."
    )
    st.markdown("")

    from pathlib import Path
    queries_text = (Path(__file__).parent / "queries.sql").read_text()
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

    # Filter out any blocks that are just comments (no SELECT)
    query_blocks = [(t, s) for t, s in query_blocks if "SELECT" in s.upper()]

    selected_query = st.selectbox("Select a query", options=[t for t, _ in query_blocks])
    for title, sql in query_blocks:
        if title == selected_query:
            st.code(sql, language="sql")
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

    st.markdown("")
    st.markdown('<p class="section-label">Tier benchmarks</p>', unsafe_allow_html=True)
    tiers = analytics.get_tier_benchmarks()
    tiers["tier"] = tiers["tier"].map(TIER_LABELS)
    # Only show columns that have data
    tier_cols = ["tier", "communities", "avg_vida"]
    tier_rename = {"tier": "Tier", "communities": "N", "avg_vida": "Avg Score"}
    for col, label in [("avg_income", "Income"), ("avg_poverty", "Poverty %")]:
        if col in tiers.columns and tiers[col].notna().any():
            tier_cols.append(col)
            tier_rename[col] = label
    st.dataframe(
        tiers[tier_cols].rename(columns=tier_rename),
        hide_index=True, use_container_width=True,
    )


# Footer
st.markdown("")
st.markdown("")
st.markdown(
    f'<p style="text-align: center; color: {T["footer_color"]}; font-size: 0.6rem; letter-spacing: 0.2em;">'
    "VERDEAZUL"
    "</p>",
    unsafe_allow_html=True,
)
