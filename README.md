# VerdeAzul

Community longevity potential index.

Verde = greens on your plate + green in your wallet. Azul = Blue Zone health.

Any community can move the needle. You don't need a mountain or an island. You need data on where you're falling short, and a ranked list of what to fix first.

## What it does

Scores 61 North American communities on health outcomes and financial access, then identifies:

- **Vida Index** (0-100): composite health + wealth score weighted toward longevity factors
- **Gap Analysis**: where health and wealth diverge, revealing whether a community needs health infrastructure or financial inclusion
- **Quadrant mapping**: Thriving, Cultural Longevity (healthy but poor), Wealth Not Helping (rich but sick), Critical Priority
- **Prescriptive interventions**: ranked, practical actions a city council can fund, with projected Vida Index impact

Covers proven Blue Zones, BZ Project certified communities, high-longevity counties, emerging potential areas, US-Mexico border corridor communities, and major metros as baselines.

## Tech stack

| Layer | Tool |
|-------|------|
| Data modeling | SQL (SQLite), star schema with dimensions + facts + computed scores |
| ETL pipeline | Python, NumPy, SQLAlchemy |
| Analytics | 10 showcase SQL queries (CTEs, window functions, percentile rankings) |
| API | FastAPI REST endpoints |
| Dashboard | Streamlit + Plotly, dark-themed |
| Tests | pytest, 11 tests covering all analytics functions |

## Quick start

```bash
git clone https://github.com/sbc1-code/verdeazul.git
cd verdeazul
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m src.seed
streamlit run dashboard.py
```

## Project structure

```
verdeazul/
  schema.sql          SQL schema: 6 tables, star schema design
  queries.sql         10 analytical queries (CTEs, window functions, gap analysis)
  src/
    database.py       SQLite connection + initialization
    seed.py           ETL pipeline, generates 61 communities x 4 quarters
    analytics.py      Python analytics layer, returns DataFrames
    api.py            FastAPI REST API (9 endpoints)
  dashboard.py        Streamlit dashboard (4 tabs, branded dark theme)
  tests/
    test_analytics.py 11 tests covering all query functions
```

## Dashboard tabs

1. **Pulse Overview**: key metrics, North America map, rankings, tier benchmarks, border comparison
2. **Gap Analysis**: health vs wealth scatter plot with quadrant mapping, gap rankings
3. **Community Profile**: deep dive with radar charts, trend lines, and ranked interventions
4. **SQL Lab**: browse and run the 10 showcase queries with live results

## API

```bash
uvicorn src.api:app --reload --port 8000
```

Endpoints: `/stats`, `/communities`, `/communities/{id}`, `/communities/{id}/trend`, `/communities/{id}/interventions`, `/rankings`, `/gap-analysis`, `/tiers`, `/border-comparison`

## Data sources (seed methodology)

Seed data uses distributions modeled on CDC PLACES, Census ACS, FDIC bank access, and EPA air quality data. Each community has a prosperity baseline that drives correlated health and financial metrics with realistic noise. Not raw public data, but statistically representative for demonstration.

## The philosophy

Health and wealth are not separate problems. A community with good hospitals but no bank branches still fails its residents. A community with high incomes but no walkability still gets sick. VerdeAzul maps that intersection and tells you what to do about it.

---

Built by [Sebastian Becerra](https://sbc1-code.github.io/portfolio/)
