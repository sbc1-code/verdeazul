"""
Seed VerdeAzul database from real public data or synthetic fallback.

If data/real_counties.json exists (from src.ingest), uses real CDC PLACES,
Census ACS, EPA AQI, and FDIC data. Otherwise generates synthetic data.
"""

import json
import numpy as np
from pathlib import Path
from sqlalchemy import text
from src.database import reset_db, _raw_engine

np.random.seed(42)

DATA_DIR = Path(__file__).parent.parent / "data"
REAL_DATA_PATH = DATA_DIR / "real_counties.json"

PERIODS = ["2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4"]

REGIONS = [
    ("US-Mexico Border Corridor", "border_zone", "US"),
    ("Rocky Mountain West", "metro", "US"),
    ("Pacific Coast", "metro", "US"),
    ("Sun Belt", "metro", "US"),
    ("Midwest", "metro", "US"),
    ("Northeast", "metro", "US"),
    ("Southeast", "metro", "US"),
    ("Hawaii-Pacific", "metro", "US"),
]

STATE_REGIONS = {
    "TX": "Sun Belt", "AZ": "Sun Belt", "FL": "Sun Belt", "GA": "Southeast",
    "AL": "Southeast", "LA": "Sun Belt", "SC": "Southeast", "NC": "Southeast",
    "TN": "Southeast", "MS": "Southeast", "AR": "Southeast", "KY": "Southeast",
    "CA": "Pacific Coast", "OR": "Pacific Coast", "WA": "Pacific Coast",
    "CO": "Rocky Mountain West", "WY": "Rocky Mountain West", "ID": "Rocky Mountain West",
    "NM": "Rocky Mountain West", "MT": "Rocky Mountain West", "UT": "Rocky Mountain West",
    "NV": "Rocky Mountain West",
    "MN": "Midwest", "IA": "Midwest", "IL": "Midwest", "MI": "Midwest",
    "IN": "Midwest", "OH": "Midwest", "WI": "Midwest", "MO": "Midwest",
    "KS": "Midwest", "NE": "Midwest", "ND": "Midwest", "SD": "Midwest",
    "NY": "Northeast", "NJ": "Northeast", "PA": "Northeast", "CT": "Northeast",
    "MA": "Northeast", "MD": "Northeast", "VA": "Northeast", "DE": "Northeast",
    "DC": "Northeast", "NH": "Northeast", "VT": "Northeast", "ME": "Northeast",
    "RI": "Northeast", "WV": "Southeast",
    "HI": "Hawaii-Pacific", "AK": "Pacific Coast",
    "OK": "Sun Belt",
}

INTERVENTION_TEMPLATES = {
    "walkability": [
        ("Add protected bike lanes on main corridors", "Reduces car dependency, increases daily movement by avg 22 min/week per resident", 3.5, "medium"),
        ("Implement complete streets policy", "Requires all road projects to include pedestrian and cyclist infrastructure", 4.2, "low"),
    ],
    "food_access": [
        ("Fund weekly farmers market with SNAP/EBT matching", "Doubles purchasing power for low-income residents, increases fresh produce intake 30%+", 4.0, "low"),
        ("Healthy corner store initiative", "Partner with local stores to stock fresh produce, subsidize healthy options", 2.5, "low"),
    ],
    "financial_inclusion": [
        ("Partner with credit union for community branch", "Reduces unbanked rate, provides low-fee banking, financial literacy classes", 3.0, "medium"),
        ("Medical debt forgiveness fund", "Buys and forgives medical debt at pennies on the dollar, reduces financial stress", 4.5, "medium"),
    ],
    "preventive_care": [
        ("Mobile health clinic circuit", "Brings preventive screenings to underserved neighborhoods on rotating schedule", 5.0, "high"),
        ("Community health worker program", "Train local residents as health navigators, proven to reduce ER visits 40%", 4.8, "medium"),
    ],
    "mental_health": [
        ("Free community movement classes in parks", "Parks dept offers tai chi, yoga, walking groups in public spaces", 2.0, "low"),
        ("Nature prescription program", "Doctors prescribe park time, partnered with local trails and green spaces", 1.8, "low"),
    ],
    "air_quality": [
        ("Urban tree canopy program", "Plant 1,000+ trees in low-canopy neighborhoods, reduces heat island and filters air", 2.0, "medium"),
        ("Electric bus fleet transition", "Replace diesel transit buses, reduces respiratory illness in transit corridors", 2.2, "high"),
    ],
    "economic_development": [
        ("Healthcare job training pipeline", "Train residents for healthcare careers, addresses both employment and care access", 4.0, "high"),
        ("Cooperative business incubator", "Supports worker-owned co-ops, builds community wealth that stays local", 3.0, "medium"),
    ],
    "smoking_cessation": [
        ("Free smoking cessation program with nicotine replacement", "County-funded quit line + free patches/gum, proven 25% quit rate", 3.5, "medium"),
        ("Tobacco-free parks and public spaces policy", "Reduces secondhand exposure and normalizes non-smoking", 2.0, "low"),
    ],
}


def _clamp(val, lo, hi):
    return max(lo, min(hi, val))


def compute_health_score(c):
    """Compute health score (0-100) from real metrics."""
    diabetes = c.get("diabetes_rate") or 10
    heart = c.get("heart_disease_rate") or 6
    obesity = c.get("obesity_rate") or 32
    insurance = c.get("insurance_coverage_pct") or 85
    mental = c.get("mental_health_score") or 80
    preventive = c.get("preventive_care_pct") or 70
    aqi = c.get("air_quality_index") or 45
    walkability = c.get("walkability_score")

    # Base weights sum to 1.0 when walkability is present
    if walkability is not None:
        score = _clamp(
            (100 - diabetes * 3.5) * 0.11 +
            (100 - heart * 5) * 0.11 +
            (100 - obesity * 1.5) * 0.09 +
            insurance * 0.16 +
            mental * 0.13 +
            preventive * 0.13 +
            _clamp(100 - aqi * 0.6, 0, 100) * 0.07 +
            _clamp(100 - (c.get("smoking_pct") or 15) * 2.5, 0, 100) * 0.10 +
            walkability * 0.10,
            0, 100
        )
    else:
        score = _clamp(
            (100 - diabetes * 3.5) * 0.12 +
            (100 - heart * 5) * 0.12 +
            (100 - obesity * 1.5) * 0.10 +
            insurance * 0.18 +
            mental * 0.15 +
            preventive * 0.15 +
            _clamp(100 - aqi * 0.6, 0, 100) * 0.08 +
            _clamp(100 - (c.get("smoking_pct") or 15) * 2.5, 0, 100) * 0.10,
            0, 100
        )
    return round(score, 1)


def compute_wealth_score(c):
    """Compute wealth score (0-100) from real metrics."""
    income = c.get("median_income") or 65000
    poverty = c.get("poverty_rate") or 13
    branches = c.get("bank_branches_per_10k") or 3
    med_debt = c.get("medical_debt_rate")

    # When medical debt data is present, include it in scoring
    if med_debt is not None:
        score = _clamp(
            _clamp((income - 20000) / 130000 * 100, 0, 100) * 0.30 +
            _clamp(100 - poverty * 2.0, 0, 100) * 0.30 +
            _clamp(branches / 6 * 100, 0, 100) * 0.12 +
            _clamp(100 - med_debt * 4.0, 0, 100) * 0.15 +
            _clamp((income - 20000) / 130000 * 80 + (100 - poverty), 0, 100) * 0.13,
            0, 100
        )
    else:
        score = _clamp(
            _clamp((income - 20000) / 130000 * 100, 0, 100) * 0.35 +
            _clamp(100 - poverty * 2.0, 0, 100) * 0.35 +
            _clamp(branches / 6 * 100, 0, 100) * 0.15 +
            _clamp((income - 20000) / 130000 * 80 + (100 - poverty), 0, 100) * 0.15,
            0, 100
        )
    return round(score, 1)


def pick_interventions(c, health_score, wealth_score):
    """Select interventions based on actual metric gaps."""
    gaps = []

    if (c.get("preventive_care_pct") or 100) < 70:
        gaps.append("preventive_care")
    if (c.get("mental_health_score") or 100) < 80:
        gaps.append("mental_health")
    if (c.get("smoking_pct") or 0) > 18:
        gaps.append("smoking_cessation")
    if (c.get("air_quality_index") or 0) > 50:
        gaps.append("air_quality")
    if (c.get("poverty_rate") or 0) > 18:
        gaps.append("economic_development")
    if (c.get("bank_branches_per_10k") or 10) < 2.5:
        gaps.append("financial_inclusion")
    if (c.get("obesity_rate") or 0) > 35:
        gaps.append("food_access")
    if (c.get("walkability_score") or 100) < 40:
        gaps.append("walkability")
    if (c.get("medical_debt_rate") or 0) > 20:
        gaps.append("financial_inclusion")
    if not gaps:
        gaps = ["preventive_care"]

    interventions = []
    for cat in gaps[:4]:
        templates = INTERVENTION_TEMPLATES.get(cat, [])
        for title, desc, impact, cost in templates[:2]:
            interventions.append({
                "category": cat,
                "title": title,
                "description": desc,
                "estimated_impact": round(impact + np.random.normal(0, 0.3), 1),
                "cost_tier": cost,
            })

    interventions.sort(key=lambda x: x["estimated_impact"], reverse=True)
    for i, inv in enumerate(interventions):
        inv["priority_rank"] = i + 1
    return interventions


def seed_from_real_data(engine, counties_data):
    """Seed database from real ingested data."""
    with engine.connect() as conn:
        # Insert regions
        region_ids = {}
        for name, rtype, country in REGIONS:
            conn.execute(text(
                "INSERT INTO regions (name, type, country) VALUES (:n, :t, :c)"
            ), {"n": name, "t": rtype, "c": country})
            result = conn.execute(text("SELECT last_insert_rowid()"))
            region_ids[name] = result.scalar()

        for c in counties_data:
            # Determine region
            state = c.get("state", "")
            is_border = c.get("border_community", False)
            region_name = "US-Mexico Border Corridor" if is_border else STATE_REGIONS.get(state, "Sun Belt")
            rid = region_ids.get(region_name, 1)

            # Determine urban/rural by population
            pop = c.get("population", 0)
            urban_rural = "urban" if pop > 100000 else "suburban" if pop > 25000 else "rural"

            conn.execute(text("""
                INSERT INTO communities
                    (name, state, county, region_id, population, latitude, longitude,
                     urban_rural, border_community, blue_zone_tier)
                VALUES (:name, :state, :county, :rid, :pop, :lat, :lon, :ur, :border, :tier)
            """), {
                "name": c["name"], "state": state, "county": c.get("fips"),
                "rid": rid, "pop": pop,
                "lat": c.get("latitude"), "lon": c.get("longitude"),
                "ur": urban_rural,
                "border": 1 if is_border else 0,
                "tier": c.get("blue_zone_tier", "unscored"),
            })
            cid = conn.execute(text("SELECT last_insert_rowid()")).scalar()

            # Compute scores
            health_score = compute_health_score(c)
            wealth_score = compute_wealth_score(c)
            vida_index = round(health_score * 0.55 + wealth_score * 0.45, 1)
            gap = round(abs(health_score - wealth_score), 1)
            direction = "balanced" if gap < 8 else ("health_leading" if health_score > wealth_score else "wealth_leading")

            # Insert metrics for each period (slight variation per quarter)
            for pi, period in enumerate(PERIODS):
                noise_h = np.random.normal(0, 0.5)
                noise_w = np.random.normal(0, 0.3)
                hs = round(_clamp(health_score + noise_h + pi * 0.1, 0, 100), 1)
                ws = round(_clamp(wealth_score + noise_w + pi * 0.05, 0, 100), 1)
                vi = round(hs * 0.55 + ws * 0.45, 1)
                g = round(abs(hs - ws), 1)
                gd = "balanced" if g < 8 else ("health_leading" if hs > ws else "wealth_leading")

                conn.execute(text("""
                    INSERT INTO health_metrics
                        (community_id, period, diabetes_rate, heart_disease_rate,
                         obesity_rate, insurance_coverage_pct, mental_health_score,
                         preventive_care_pct, life_expectancy, air_quality_index,
                         walkability_score, food_access_score, health_score)
                    VALUES (:cid, :period, :diabetes_rate, :heart_disease_rate,
                            :obesity_rate, :insurance_coverage_pct, :mental_health_score,
                            :preventive_care_pct, :life_expectancy, :air_quality_index,
                            :walkability_score, :food_access_score, :health_score)
                """), {
                    "cid": cid, "period": period,
                    "diabetes_rate": c.get("diabetes_rate"),
                    "heart_disease_rate": c.get("heart_disease_rate"),
                    "obesity_rate": c.get("obesity_rate"),
                    "insurance_coverage_pct": c.get("insurance_coverage_pct"),
                    "mental_health_score": c.get("mental_health_score"),
                    "preventive_care_pct": c.get("preventive_care_pct"),
                    "life_expectancy": None,  # not in PLACES, could add from IHME later
                    "air_quality_index": c.get("air_quality_index"),
                    "walkability_score": c.get("walkability_score"),
                    "food_access_score": None,
                    "health_score": hs,
                })

                conn.execute(text("""
                    INSERT INTO financial_metrics
                        (community_id, period, median_income, poverty_rate,
                         unbanked_rate, bank_branches_per_10k,
                         health_expenditure_per_cap, medical_debt_rate,
                         cost_of_living_index, small_biz_density, wealth_score)
                    VALUES (:cid, :period, :median_income, :poverty_rate,
                            :unbanked_rate, :bank_branches_per_10k,
                            :health_expenditure_per_cap, :medical_debt_rate,
                            :cost_of_living_index, :small_biz_density, :wealth_score)
                """), {
                    "cid": cid, "period": period,
                    "median_income": c.get("median_income"),
                    "poverty_rate": c.get("poverty_rate"),
                    "unbanked_rate": None,
                    "bank_branches_per_10k": c.get("bank_branches_per_10k"),
                    "health_expenditure_per_cap": None,
                    "medical_debt_rate": c.get("medical_debt_rate"),
                    "cost_of_living_index": None,
                    "small_biz_density": None,
                    "wealth_score": ws,
                })

                conn.execute(text("""
                    INSERT INTO vida_scores
                        (community_id, period, health_score, wealth_score,
                         vida_index, gap_score, gap_direction, quadrant, percentile_rank)
                    VALUES (:cid, :period, :hs, :ws, :vida_index, :gap_score,
                            :gap_direction, :quadrant, 0)
                """), {
                    "cid": cid, "period": period,
                    "hs": hs, "ws": ws, "vida_index": vi,
                    "gap_score": g, "gap_direction": gd,
                    "quadrant": "unassigned",
                })

            # Interventions for latest period
            interventions = pick_interventions(c, health_score, wealth_score)
            for inv in interventions:
                conn.execute(text("""
                    INSERT INTO interventions
                        (community_id, period, category, title, description,
                         estimated_impact, cost_tier, priority_rank)
                    VALUES (:cid, :period, :cat, :title, :desc, :impact, :cost, :rank)
                """), {
                    "cid": cid, "period": "2024-Q4", "cat": inv["category"],
                    "title": inv["title"], "desc": inv["description"],
                    "impact": inv["estimated_impact"], "cost": inv["cost_tier"],
                    "rank": inv["priority_rank"],
                })

        # Assign quadrants using median thresholds
        import pandas as pd
        scores = pd.read_sql(text(
            "SELECT health_score, wealth_score FROM vida_scores WHERE period = '2024-Q4'"
        ), conn)
        h_med = float(scores["health_score"].median())
        w_med = float(scores["wealth_score"].median())

        conn.execute(text("""
            UPDATE vida_scores SET quadrant = CASE
                WHEN health_score >= :h AND wealth_score >= :w THEN 'thriving'
                WHEN health_score >= :h AND wealth_score < :w THEN 'cultural_longevity'
                WHEN health_score < :h AND wealth_score >= :w THEN 'wealth_not_helping'
                ELSE 'critical'
            END
        """), {"h": h_med, "w": w_med})

        # Percentile ranks
        conn.execute(text("""
            UPDATE vida_scores
            SET percentile_rank = (
                SELECT ROUND(
                    CAST(COUNT(*) AS REAL) /
                    (SELECT COUNT(*) FROM vida_scores WHERE period = '2024-Q4') * 100, 1
                )
                FROM vida_scores v2
                WHERE v2.period = '2024-Q4'
                  AND v2.vida_index <= vida_scores.vida_index
            )
            WHERE period = '2024-Q4'
        """))

        conn.commit()

    return len(counties_data)


def seed():
    """Main entry point. Uses real data if available, synthetic fallback."""
    engine = reset_db()

    if REAL_DATA_PATH.exists():
        with open(REAL_DATA_PATH) as f:
            counties = json.load(f)
        n = seed_from_real_data(engine, counties)
        source = "real (CDC PLACES + Census ACS + EPA AQI + FDIC + Walkability + Medical Debt)"
    else:
        # Fallback: synthetic data would go here
        # For now, raise an error directing user to run ingest
        print("No real data found. Run: python -m src.ingest")
        print("Or download data/real_counties.json from the repo.")
        n = 0
        source = "none"

    # Print summary
    from src.database import _raw_engine
    eng = _raw_engine()
    with eng.connect() as c:
        import pandas as pd
        try:
            dist = pd.read_sql(text(
                "SELECT quadrant, COUNT(*) as n FROM vida_scores WHERE period='2024-Q4' GROUP BY quadrant"
            ), c)
            print(f"VerdeAzul database seeded successfully ({source}).")
            print(f"  Communities: {n}")
            print(f"  Quadrant distribution (Q4):")
            for _, row in dist.iterrows():
                print(f"    {row['quadrant']}: {row['n']}")
        except Exception:
            print(f"Seeded {n} communities ({source}).")


if __name__ == "__main__":
    seed()
