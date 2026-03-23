"""Tests for VerdeAzul analytics layer."""

import pytest
from src.database import reset_db, DB_PATH
from src.seed import seed
from src import analytics


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """Seed the database once for all tests."""
    seed()
    yield
    if DB_PATH.exists():
        DB_PATH.unlink()


def test_overview_stats():
    df = analytics.get_overview_stats()
    assert len(df) == 1
    row = df.iloc[0]
    assert row["total_communities"] > 50
    assert 0 < row["avg_vida_index"] < 100
    # life expectancy may be None when using real data (not in CDC PLACES)
    if row["avg_life_expectancy"] is not None:
        assert row["avg_life_expectancy"] > 65


def test_community_map_has_all_communities():
    df = analytics.get_community_map()
    assert len(df) > 50
    assert "latitude" in df.columns
    assert "longitude" in df.columns
    assert "vida_index" in df.columns


def test_community_detail():
    # Get first community ID
    map_df = analytics.get_community_map()
    cid = int(map_df.iloc[0]["community_id"])
    detail = analytics.get_community_detail(cid)
    assert len(detail) == 1
    d = detail.iloc[0]
    assert d["vida_index"] > 0
    assert d["health_score"] > 0
    assert d["wealth_score"] > 0


def test_community_trend():
    map_df = analytics.get_community_map()
    cid = int(map_df.iloc[0]["community_id"])
    trend = analytics.get_community_trend(cid)
    assert len(trend) == 4  # 4 quarters
    assert list(trend.columns) == ["period", "health_score", "wealth_score", "vida_index", "gap_score", "quadrant"]


def test_gap_analysis():
    df = analytics.get_gap_analysis()
    assert len(df) > 50
    assert set(df["quadrant"].unique()).issubset(
        {"thriving", "cultural_longevity", "wealth_not_helping", "critical"}
    )


def test_interventions_exist():
    map_df = analytics.get_community_map()
    # Check a community that likely has interventions (low-scoring)
    low_vida = map_df.nsmallest(1, "vida_index")
    cid = int(low_vida.iloc[0]["community_id"])
    interventions = analytics.get_interventions(cid)
    assert len(interventions) > 0
    assert "estimated_impact" in interventions.columns
    assert "cost_tier" in interventions.columns


def test_rankings():
    df = analytics.get_rankings(limit=10)
    assert len(df) == 10
    # Should be sorted descending
    assert df.iloc[0]["vida_index"] >= df.iloc[-1]["vida_index"]


def test_tier_benchmarks():
    df = analytics.get_tier_benchmarks()
    assert len(df) > 0
    assert "tier" in df.columns
    assert "avg_vida" in df.columns


def test_border_comparison():
    df = analytics.get_border_comparison()
    assert len(df) == 2
    categories = set(df["category"])
    assert categories == {"Border", "Non-Border"}


def test_quadrant_summary():
    df = analytics.get_quadrant_summary()
    assert len(df) > 0
    total = df["count"].sum()
    map_df = analytics.get_community_map()
    assert total == len(map_df)


def test_vida_scores_bounded():
    """All scores should be between 0 and 100."""
    df = analytics.get_community_map()
    assert (df["vida_index"] >= 0).all() and (df["vida_index"] <= 100).all()
    assert (df["health_score"] >= 0).all() and (df["health_score"] <= 100).all()
    assert (df["wealth_score"] >= 0).all() and (df["wealth_score"] <= 100).all()
