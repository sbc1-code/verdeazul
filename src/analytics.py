"""Analytics layer for VerdeAzul. Runs SQL queries, returns DataFrames."""

import pandas as pd
from sqlalchemy import text
from src.database import get_engine


def _query(sql, params=None):
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})


def get_overview_stats(period="2024-Q4"):
    """Key stats for the overview dashboard."""
    return _query("""
        SELECT
            COUNT(DISTINCT c.community_id) AS total_communities,
            ROUND(AVG(v.vida_index), 1) AS avg_vida_index,
            ROUND(AVG(v.health_score), 1) AS avg_health_score,
            ROUND(AVG(v.wealth_score), 1) AS avg_wealth_score,
            ROUND(AVG(v.gap_score), 1) AS avg_gap,
            SUM(CASE WHEN v.quadrant = 'critical' THEN 1 ELSE 0 END) AS critical_count,
            SUM(CASE WHEN v.quadrant = 'thriving' THEN 1 ELSE 0 END) AS thriving_count,
            ROUND(AVG(h.life_expectancy), 1) AS avg_life_expectancy
        FROM vida_scores v
        JOIN communities c ON c.community_id = v.community_id
        JOIN health_metrics h ON h.community_id = c.community_id AND h.period = v.period
        WHERE v.period = :period
    """, {"period": period})


def get_community_map(period="2024-Q4"):
    """All communities with coords and scores for map plotting."""
    return _query("""
        SELECT
            c.community_id, c.name, c.state, c.population,
            c.latitude, c.longitude, c.urban_rural,
            c.border_community, c.blue_zone_tier,
            v.vida_index, v.health_score, v.wealth_score,
            v.gap_score, v.gap_direction, v.quadrant, v.percentile_rank,
            h.life_expectancy, h.walkability_score, h.food_access_score,
            f.median_income, f.poverty_rate
        FROM communities c
        JOIN vida_scores v ON v.community_id = c.community_id AND v.period = :period
        JOIN health_metrics h ON h.community_id = c.community_id AND h.period = :period
        JOIN financial_metrics f ON f.community_id = c.community_id AND f.period = :period
        ORDER BY v.vida_index DESC
    """, {"period": period})


def get_community_detail(community_id):
    """Full detail for a single community, latest period."""
    return _query("""
        SELECT
            c.*, r.name AS region_name,
            h.diabetes_rate, h.heart_disease_rate, h.obesity_rate,
            h.insurance_coverage_pct, h.mental_health_score,
            h.preventive_care_pct, h.life_expectancy,
            h.air_quality_index, h.walkability_score, h.food_access_score,
            h.health_score,
            f.median_income, f.poverty_rate, f.unbanked_rate,
            f.bank_branches_per_10k, f.health_expenditure_per_cap,
            f.medical_debt_rate, f.cost_of_living_index,
            f.small_biz_density, f.wealth_score,
            v.vida_index, v.gap_score, v.gap_direction,
            v.quadrant, v.percentile_rank
        FROM communities c
        JOIN regions r ON r.region_id = c.region_id
        JOIN health_metrics h ON h.community_id = c.community_id AND h.period = '2024-Q4'
        JOIN financial_metrics f ON f.community_id = c.community_id AND f.period = '2024-Q4'
        JOIN vida_scores v ON v.community_id = c.community_id AND v.period = '2024-Q4'
        WHERE c.community_id = :cid
    """, {"cid": community_id})


def get_community_trend(community_id):
    """Vida scores across all periods for trend charting."""
    return _query("""
        SELECT period, health_score, wealth_score, vida_index, gap_score, quadrant
        FROM vida_scores
        WHERE community_id = :cid
        ORDER BY period
    """, {"cid": community_id})


def get_gap_analysis(period="2024-Q4"):
    """Health vs Wealth scatter data with quadrant assignments."""
    return _query("""
        SELECT
            c.community_id, c.name, c.state, c.population,
            c.border_community, c.blue_zone_tier,
            v.health_score, v.wealth_score, v.vida_index,
            v.gap_score, v.gap_direction, v.quadrant
        FROM vida_scores v
        JOIN communities c ON c.community_id = v.community_id
        WHERE v.period = :period
        ORDER BY v.gap_score DESC
    """, {"period": period})


def get_interventions(community_id):
    """Ranked interventions for a specific community."""
    return _query("""
        SELECT
            i.category, i.title, i.description,
            i.estimated_impact, i.cost_tier, i.priority_rank,
            v.vida_index AS current_vida,
            ROUND(v.vida_index + i.estimated_impact, 1) AS projected_vida
        FROM interventions i
        JOIN vida_scores v ON v.community_id = i.community_id AND v.period = i.period
        WHERE i.community_id = :cid
        ORDER BY i.priority_rank
    """, {"cid": community_id})


def get_rankings(period="2024-Q4", limit=20):
    """Top communities by vida index with state-level rank."""
    return _query("""
        SELECT
            c.name, c.state, c.blue_zone_tier,
            v.vida_index, v.health_score, v.wealth_score,
            v.quadrant, v.percentile_rank,
            h.life_expectancy,
            DENSE_RANK() OVER (ORDER BY v.vida_index DESC) AS rank
        FROM vida_scores v
        JOIN communities c ON c.community_id = v.community_id
        JOIN health_metrics h ON h.community_id = c.community_id AND h.period = v.period
        WHERE v.period = :period
        ORDER BY v.vida_index DESC
        LIMIT :lim
    """, {"period": period, "lim": limit})


def get_tier_benchmarks(period="2024-Q4"):
    """Average metrics grouped by Blue Zone tier."""
    return _query("""
        SELECT
            c.blue_zone_tier AS tier,
            COUNT(DISTINCT c.community_id) AS communities,
            ROUND(AVG(v.vida_index), 1) AS avg_vida,
            ROUND(AVG(h.life_expectancy), 1) AS avg_life_exp,
            ROUND(AVG(h.walkability_score), 1) AS avg_walkability,
            ROUND(AVG(h.food_access_score), 1) AS avg_food_access,
            ROUND(AVG(f.median_income)) AS avg_income,
            ROUND(AVG(f.poverty_rate), 1) AS avg_poverty,
            ROUND(AVG(f.medical_debt_rate), 1) AS avg_medical_debt
        FROM communities c
        JOIN vida_scores v ON v.community_id = c.community_id AND v.period = :period
        JOIN health_metrics h ON h.community_id = c.community_id AND h.period = :period
        JOIN financial_metrics f ON f.community_id = c.community_id AND f.period = :period
        GROUP BY c.blue_zone_tier
        ORDER BY avg_vida DESC
    """, {"period": period})


def get_border_comparison(period="2024-Q4"):
    """Border vs non-border community comparison."""
    return _query("""
        SELECT
            CASE WHEN c.border_community = 1 THEN 'Border' ELSE 'Non-Border' END AS category,
            COUNT(DISTINCT c.community_id) AS communities,
            ROUND(AVG(v.health_score), 1) AS avg_health,
            ROUND(AVG(v.wealth_score), 1) AS avg_wealth,
            ROUND(AVG(v.vida_index), 1) AS avg_vida,
            ROUND(AVG(v.gap_score), 1) AS avg_gap,
            ROUND(AVG(h.life_expectancy), 1) AS avg_life_exp,
            ROUND(AVG(f.median_income)) AS avg_income,
            ROUND(AVG(f.unbanked_rate), 1) AS avg_unbanked
        FROM vida_scores v
        JOIN communities c ON c.community_id = v.community_id
        JOIN health_metrics h ON h.community_id = c.community_id AND h.period = v.period
        JOIN financial_metrics f ON f.community_id = c.community_id AND f.period = v.period
        WHERE v.period = :period
        GROUP BY c.border_community
    """, {"period": period})


def get_quadrant_summary(period="2024-Q4"):
    """Community counts and averages by quadrant."""
    return _query("""
        SELECT
            v.quadrant,
            COUNT(*) AS count,
            ROUND(AVG(v.vida_index), 1) AS avg_vida,
            ROUND(AVG(v.health_score), 1) AS avg_health,
            ROUND(AVG(v.wealth_score), 1) AS avg_wealth,
            ROUND(AVG(v.gap_score), 1) AS avg_gap
        FROM vida_scores v
        WHERE v.period = :period
        GROUP BY v.quadrant
        ORDER BY avg_vida DESC
    """, {"period": period})


def get_quadrant_thresholds(period="2024-Q4"):
    """Get the median health/wealth scores used as quadrant dividers."""
    df = _query("""
        SELECT health_score, wealth_score FROM vida_scores WHERE period = :period
    """, {"period": period})
    return float(df["health_score"].median()), float(df["wealth_score"].median())
