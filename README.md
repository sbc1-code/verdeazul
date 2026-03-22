# VerdeAzul

Every community has the building blocks. Most just don't know where to start.

Scores 62 communities across North America on healthcare access, nutritious food availability, and economic equity, then tells each one what to do about it.

## What it does

- **Vida Index** (0-100): composite health + economic access score weighted toward longevity factors
- **Gap Analysis**: health outcomes vs economic access scatter plot. Four quadrants reveal whether a community needs food and healthcare infrastructure, financial services, or both
- **Quadrant mapping**: Thriving, Healthy Not Wealthy (cultural longevity despite poverty), Wealthy Not Healthy (money isn't solving it), Needs Attention
- **Prescriptive interventions**: ranked, practical actions with projected score impact. Things a city council or community org can fund.

Covers proven Blue Zones, BZ Project certified communities, high-longevity counties, US-Mexico border corridor, and major metros as baselines.

## Tech stack

| Layer | Tool |
|-------|------|
| Data modeling | SQL (SQLite), star schema with dimensions, facts, computed scores |
| ETL pipeline | Python, NumPy, SQLAlchemy |
| Analytics | 10 SQL queries (CTEs, window functions, percentile rankings, median-based quadrants) |
| API | FastAPI REST endpoints |
| Dashboard | Streamlit + Plotly, dark-themed |
| Tests | pytest, 11 tests |

## Quick start

```bash
git clone https://github.com/sbc1-code/verdeazul.git
cd verdeazul
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run dashboard.py
```

The database auto-seeds on first run. No manual setup needed.

## Project structure

```
verdeazul/
  schema.sql          SQL schema: 6 tables, star schema design
  queries.sql         10 analytical queries (CTEs, window functions, gap analysis)
  src/
    database.py       SQLite connection, auto-seed on first access
    seed.py           ETL pipeline, 62 communities x 4 quarters, independent health/wealth baselines
    analytics.py      Python analytics layer, returns DataFrames
    api.py            FastAPI REST API (9 endpoints)
  dashboard.py        Streamlit dashboard (4 tabs, branded dark theme)
  tests/
    test_analytics.py 11 tests covering all query functions
```

## Dashboard tabs

1. **Overview**: key metrics, North America map (tightened to US/Mexico), quadrant explainers
2. **Explore**: health vs economic access scatter plot with dynamic median-based quadrant lines, border comparison, narrative insights
3. **Your Community**: select any community, bar chart profiles, quarterly trends, projected impact from interventions
4. **Under the Hood**: browse and run the 10 showcase SQL queries with live results, tier benchmarks

## API

```bash
uvicorn src.api:app --reload --port 8000
```

Endpoints: `/stats`, `/communities`, `/communities/{id}`, `/communities/{id}/trend`, `/communities/{id}/interventions`, `/rankings`, `/gap-analysis`, `/tiers`, `/border-comparison`

## Data model

Each community has **independent health and wealth baselines** so the data reflects reality: border communities with strong cultural health practices but limited economic access, wealthy suburbs with poor walkability, proven Blue Zones with high health but moderate income. Quadrant thresholds are computed from medians, not hardcoded, so all four quadrants are always populated.

Seed data uses distributions modeled on CDC PLACES, Census ACS, FDIC bank access, and EPA air quality patterns. Statistically representative for demonstration.

## The philosophy

Healthcare access and economic access are not separate problems. A community with good hospitals but no bank branches still fails its residents. A community with high incomes but no walkability still gets sick. VerdeAzul maps that intersection and tells you what to do about it.

---

Built by [Sebastian Becerra](https://sbc1-code.github.io/portfolio/)
