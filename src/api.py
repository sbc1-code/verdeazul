"""VerdeAzul REST API. FastAPI endpoints for community longevity data."""

from fastapi import FastAPI, HTTPException, Query
from src import analytics

app = FastAPI(
    title="VerdeAzul API",
    description="Community health and financial equity index. Verde = greens + money well spent. Azul = Blue Zone potential + health.",
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "name": "VerdeAzul",
        "version": "1.0.0",
        "description": "Community longevity potential index",
        "endpoints": [
            "/stats", "/communities", "/communities/{id}",
            "/communities/{id}/trend", "/communities/{id}/interventions",
            "/rankings", "/gap-analysis", "/tiers", "/border-comparison",
        ],
    }


@app.get("/stats")
def stats(period: str = "2024-Q4"):
    df = analytics.get_overview_stats(period)
    return df.to_dict(orient="records")[0]


@app.get("/communities")
def communities(period: str = "2024-Q4"):
    df = analytics.get_community_map(period)
    return df.to_dict(orient="records")


@app.get("/communities/{community_id}")
def community_detail(community_id: int):
    df = analytics.get_community_detail(community_id)
    if df.empty:
        raise HTTPException(status_code=404, detail="Community not found")
    return df.to_dict(orient="records")[0]


@app.get("/communities/{community_id}/trend")
def community_trend(community_id: int):
    df = analytics.get_community_trend(community_id)
    if df.empty:
        raise HTTPException(status_code=404, detail="Community not found")
    return df.to_dict(orient="records")


@app.get("/communities/{community_id}/interventions")
def community_interventions(community_id: int):
    df = analytics.get_interventions(community_id)
    return df.to_dict(orient="records")


@app.get("/rankings")
def rankings(period: str = "2024-Q4", limit: int = Query(20, le=100)):
    df = analytics.get_rankings(period, limit)
    return df.to_dict(orient="records")


@app.get("/gap-analysis")
def gap_analysis(period: str = "2024-Q4"):
    df = analytics.get_gap_analysis(period)
    return df.to_dict(orient="records")


@app.get("/tiers")
def tier_benchmarks(period: str = "2024-Q4"):
    df = analytics.get_tier_benchmarks(period)
    return df.to_dict(orient="records")


@app.get("/border-comparison")
def border_comparison(period: str = "2024-Q4"):
    df = analytics.get_border_comparison(period)
    return df.to_dict(orient="records")
