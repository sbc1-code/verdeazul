"""
Seed VerdeAzul with realistic community data.

Each community now has separate health and wealth baselines to create
realistic divergence - border communities with strong cultural health
but limited economic access, wealthy suburbs with poor walkability, etc.
"""

import numpy as np
from sqlalchemy import text
from src.database import reset_db, get_engine

np.random.seed(42)

# ---------------------------------------------------------------------------
# Community definitions
# (name, state, pop, lat, lon, urban_rural, border, tier, health_base, wealth_base)
#
# health_base: 0-1, drives health metrics (diet, care access, walkability, air)
# wealth_base: 0-1, drives financial metrics (income, banking, debt)
# These are INDEPENDENT so communities can be healthy-not-wealthy or vice versa.
# ---------------------------------------------------------------------------

COMMUNITIES = [
    # --- PROVEN BLUE ZONES ---
    # High health (diet, community, purpose), moderate wealth
    ("Loma Linda", "CA", 23000, 34.05, -117.26, "suburban", False, "proven", 0.88, 0.55),
    ("Nicoya Peninsula", "Costa Rica", 150000, 10.07, -85.45, "rural", False, "proven", 0.85, 0.25),

    # --- BZ PROJECT CERTIFIED ---
    ("Albert Lea", "MN", 18000, 43.65, -93.37, "rural", False, "certified", 0.68, 0.42),
    ("Hermosa Beach", "CA", 20000, 33.86, -118.40, "urban", False, "certified", 0.78, 0.82),
    ("Naples", "FL", 22000, 26.14, -81.79, "urban", False, "certified", 0.72, 0.80),
    ("Fort Worth", "TX", 960000, 32.76, -97.33, "urban", False, "certified", 0.58, 0.52),
    ("Cedar Rapids", "IA", 137000, 41.98, -91.67, "urban", False, "certified", 0.60, 0.48),
    ("Iowa City", "IA", 74000, 41.66, -91.53, "urban", False, "certified", 0.65, 0.55),
    ("Monterey", "CA", 30000, 36.60, -121.89, "urban", False, "certified", 0.72, 0.62),
    ("St. Helena", "CA", 6000, 38.51, -122.47, "rural", False, "certified", 0.75, 0.70),
    ("Walla Walla", "WA", 34000, 46.06, -118.34, "rural", False, "certified", 0.62, 0.45),
    ("Kailua-Kona", "HI", 45000, 19.64, -156.00, "suburban", False, "certified", 0.74, 0.55),

    # --- HIGH LONGEVITY COUNTIES ---
    # Colorado mountain corridor: extremely active, wealthy
    ("Summit County", "CO", 31000, 39.64, -106.05, "rural", False, "high_potential", 0.82, 0.78),
    ("Pitkin County", "CO", 18000, 39.19, -106.82, "rural", False, "high_potential", 0.84, 0.90),
    ("Eagle County", "CO", 55000, 39.63, -106.60, "rural", False, "high_potential", 0.80, 0.82),
    # Bay Area / CA wealthy: good health infrastructure, high wealth
    ("Marin County", "CA", 260000, 38.08, -122.76, "suburban", False, "high_potential", 0.80, 0.88),
    ("Santa Clara County", "CA", 1900000, 37.35, -121.96, "urban", False, "high_potential", 0.76, 0.85),
    # East coast high-income: wealth leading, health moderate
    ("Fairfax County", "VA", 1150000, 38.85, -77.31, "suburban", False, "high_potential", 0.70, 0.85),
    ("Bergen County", "NJ", 955000, 40.96, -74.07, "suburban", False, "high_potential", 0.68, 0.78),
    # Mountain/outdoor towns
    ("Los Alamos", "NM", 19000, 35.88, -106.30, "suburban", False, "high_potential", 0.78, 0.75),
    ("Teton County", "WY", 24000, 43.48, -110.76, "rural", False, "high_potential", 0.82, 0.88),
    ("Blaine County", "ID", 24000, 43.41, -114.09, "rural", False, "high_potential", 0.76, 0.72),
    ("Benton County", "OR", 94000, 44.49, -123.41, "suburban", False, "high_potential", 0.70, 0.55),
    ("Collier County", "FL", 390000, 26.20, -81.77, "suburban", False, "high_potential", 0.68, 0.76),

    # --- EMERGING POTENTIAL ---
    ("Santa Barbara", "CA", 92000, 34.42, -119.70, "urban", False, "emerging", 0.72, 0.65),
    ("Boulder", "CO", 105000, 40.02, -105.27, "urban", False, "emerging", 0.78, 0.72),
    ("Asheville", "NC", 94000, 35.60, -82.55, "urban", False, "emerging", 0.62, 0.48),
    ("Vancouver", "BC", 2600000, 49.28, -123.12, "urban", False, "emerging", 0.75, 0.70),
    ("Quebec City", "QC", 840000, 46.81, -71.21, "urban", False, "emerging", 0.68, 0.58),
    ("Portland", "OR", 650000, 45.52, -122.68, "urban", False, "emerging", 0.65, 0.58),
    ("Carmel Valley", "CA", 5000, 36.41, -121.73, "rural", False, "emerging", 0.74, 0.72),

    # --- EMERGING: CULTURAL HEALTH (healthy but not wealthy) ---
    ("Oaxaca", "Oaxaca", 300000, 17.07, -96.73, "urban", False, "emerging", 0.65, 0.18),
    ("Merida", "Yucatan", 1000000, 20.97, -89.59, "urban", False, "emerging", 0.62, 0.28),
    ("San Miguel de Allende", "Guanajuato", 170000, 20.91, -100.75, "urban", False, "emerging", 0.58, 0.25),

    # --- US-MEXICO BORDER CORRIDOR ---
    # Strong cultural health practices (diet, family, community) but limited economic access
    ("El Paso", "TX", 681000, 31.76, -106.44, "urban", True, "emerging", 0.55, 0.30),
    ("Las Cruces", "NM", 111000, 32.35, -106.74, "urban", True, "emerging", 0.52, 0.28),
    ("Laredo", "TX", 261000, 27.51, -99.51, "urban", True, "emerging", 0.48, 0.22),
    ("McAllen", "TX", 143000, 26.20, -98.23, "urban", True, "emerging", 0.45, 0.20),
    ("Brownsville", "TX", 187000, 25.90, -97.50, "urban", True, "emerging", 0.44, 0.18),
    ("San Diego", "CA", 1420000, 32.72, -117.16, "urban", True, "emerging", 0.72, 0.70),
    ("Tucson", "AZ", 543000, 32.22, -110.97, "urban", True, "emerging", 0.50, 0.38),
    ("Nogales", "AZ", 20000, 31.34, -110.93, "rural", True, "emerging", 0.48, 0.15),
    ("Eagle Pass", "TX", 29000, 28.71, -100.50, "rural", True, "emerging", 0.42, 0.14),
    ("Calexico", "CA", 40000, 32.68, -115.50, "suburban", True, "emerging", 0.46, 0.20),

    # --- MAJOR METROS: WEALTHY BUT HEALTH GAPS ---
    # High income but poor walkability, food deserts in pockets, stress, pollution
    ("Houston", "TX", 2300000, 29.76, -95.37, "urban", False, "unscored", 0.38, 0.52),
    ("Phoenix", "AZ", 1610000, 33.45, -112.07, "urban", False, "unscored", 0.40, 0.50),
    ("Dallas", "TX", 1300000, 32.78, -96.80, "urban", False, "unscored", 0.42, 0.55),
    ("San Antonio", "TX", 1530000, 29.42, -98.49, "urban", False, "unscored", 0.40, 0.42),
    ("Atlanta", "GA", 499000, 33.75, -84.39, "urban", False, "unscored", 0.45, 0.55),
    ("Miami", "FL", 450000, 25.76, -80.19, "urban", False, "unscored", 0.48, 0.52),

    # --- MAJOR METROS: BALANCED ---
    ("New York", "NY", 8340000, 40.71, -74.01, "urban", False, "unscored", 0.58, 0.62),
    ("Los Angeles", "CA", 3900000, 34.05, -118.24, "urban", False, "unscored", 0.52, 0.55),
    ("Chicago", "IL", 2700000, 41.88, -87.63, "urban", False, "unscored", 0.50, 0.52),
    ("Austin", "TX", 964000, 30.27, -97.74, "urban", False, "unscored", 0.62, 0.65),
    ("Denver", "CO", 716000, 39.74, -104.99, "urban", False, "unscored", 0.60, 0.62),
    ("Seattle", "WA", 737000, 47.61, -122.33, "urban", False, "unscored", 0.65, 0.70),

    # --- STRUGGLING: BOTH LOW ---
    ("Detroit", "MI", 640000, 42.33, -83.05, "urban", False, "unscored", 0.25, 0.20),
    ("Memphis", "TN", 633000, 35.15, -90.05, "urban", False, "unscored", 0.28, 0.22),
    ("Fresno", "CA", 542000, 36.74, -119.77, "urban", False, "unscored", 0.32, 0.28),
    ("Flint", "MI", 97000, 43.01, -83.69, "urban", False, "unscored", 0.20, 0.15),
    ("Jackson", "MS", 154000, 32.30, -90.18, "urban", False, "unscored", 0.22, 0.18),
    ("Gary", "IN", 69000, 41.59, -87.35, "urban", False, "unscored", 0.18, 0.12),
]

REGIONS = [
    ("US-Mexico Border Corridor", "border_zone", "US"),
    ("Rocky Mountain West", "metro", "US"),
    ("Pacific Coast", "metro", "US"),
    ("Sun Belt", "metro", "US"),
    ("Midwest", "metro", "US"),
    ("Northeast", "metro", "US"),
    ("Southeast", "metro", "US"),
    ("Hawaii-Pacific", "metro", "US"),
    ("British Columbia", "province", "Canada"),
    ("Quebec", "province", "Canada"),
    ("Ontario", "province", "Canada"),
    ("Central Mexico", "metro", "Mexico"),
    ("Southern Mexico", "metro", "Mexico"),
]

REGION_MAP = {
    "TX": "Sun Belt", "AZ": "Sun Belt", "FL": "Sun Belt", "GA": "Southeast",
    "CA": "Pacific Coast", "OR": "Pacific Coast", "WA": "Pacific Coast",
    "CO": "Rocky Mountain West", "WY": "Rocky Mountain West", "ID": "Rocky Mountain West",
    "NM": "Rocky Mountain West", "MN": "Midwest", "IA": "Midwest", "IL": "Midwest",
    "MI": "Midwest", "IN": "Midwest", "NY": "Northeast", "NJ": "Northeast",
    "VA": "Northeast", "HI": "Hawaii-Pacific", "NC": "Southeast", "TN": "Southeast",
    "MS": "Southeast", "BC": "British Columbia", "QC": "Quebec", "ON": "Ontario",
    "Oaxaca": "Southern Mexico", "Yucatan": "Central Mexico",
    "Guanajuato": "Central Mexico", "Costa Rica": "Sun Belt",
}

PERIODS = ["2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4"]

INTERVENTION_TEMPLATES = {
    "walkability": [
        ("Add protected bike lanes on main corridors", "Reduces car dependency, increases daily movement by avg 22 min/week per resident", 3.5, "medium"),
        ("Convert underused parking lots to pedestrian plazas", "Increases foot traffic, supports local business, builds community gathering space", 2.8, "medium"),
        ("Implement complete streets policy", "Requires all road projects to include pedestrian and cyclist infrastructure", 4.2, "low"),
    ],
    "food_access": [
        ("Fund weekly farmers market with SNAP/EBT matching", "Doubles purchasing power for low-income residents, increases fresh produce intake 30%+", 4.0, "low"),
        ("Community garden program on vacant lots", "Provides free produce, builds social bonds, increases outdoor activity", 3.2, "low"),
        ("Healthy corner store initiative", "Partner with bodegas to stock fresh produce, subsidize healthy options", 2.5, "low"),
    ],
    "financial_inclusion": [
        ("Partner with credit union for community branch", "Reduces unbanked rate, provides low-fee banking, financial literacy classes", 3.0, "medium"),
        ("Medical debt forgiveness fund", "Buys and forgives medical debt at pennies on the dollar, reduces financial stress", 4.5, "medium"),
        ("Microenterprise grant program", "Funds small businesses ($5K-$25K), builds local economic resilience", 2.8, "medium"),
    ],
    "preventive_care": [
        ("Mobile health clinic circuit", "Brings preventive screenings to underserved neighborhoods on rotating schedule", 5.0, "high"),
        ("Community health worker program", "Train local residents as health navigators, proven to reduce ER visits 40%", 4.8, "medium"),
        ("Free annual wellness fair", "Screenings, dental, vision, mental health, all in one day, removes access barriers", 2.0, "low"),
    ],
    "community_building": [
        ("Intergenerational community center", "Shared space for seniors and youth, combats isolation, builds purpose", 3.5, "high"),
        ("Neighborhood support circles", "Adapted from Okinawan moai tradition, 5-8 person groups that meet weekly", 3.0, "low"),
        ("Public plaza and gathering space investment", "Creates third places for unstructured social interaction", 2.5, "medium"),
    ],
    "air_quality": [
        ("Urban tree canopy program", "Plant 1,000+ trees in low-canopy neighborhoods, reduces heat island and filters air", 2.0, "medium"),
        ("Industrial emissions monitoring network", "Community-owned air sensors, creates accountability for polluters", 1.5, "low"),
        ("Electric bus fleet transition", "Replace diesel transit buses, reduces respiratory illness in transit corridors", 2.2, "high"),
    ],
    "mental_health": [
        ("Free community movement classes in parks", "Parks dept offers tai chi, yoga, walking groups in public spaces", 2.0, "low"),
        ("Crisis counseling walk-in clinic", "No appointment needed, reduces ER mental health visits, stigma reduction", 3.5, "medium"),
        ("Nature prescription program", "Doctors prescribe park time, partnered with local trails and green spaces", 1.8, "low"),
    ],
    "economic_development": [
        ("Live-local employer incentive program", "Tax breaks for businesses that hire within 10 miles, reduces commute stress", 2.5, "medium"),
        ("Cooperative business incubator", "Supports worker-owned co-ops, builds community wealth that stays local", 3.0, "medium"),
        ("Healthcare job training pipeline", "Train residents for healthcare careers, addresses both employment and care access", 4.0, "high"),
    ],
}


def _clamp(val, lo, hi):
    return max(lo, min(hi, val))


def _noise(scale=1.0):
    return np.random.normal(0, scale)


def generate_health_metrics(h_base, is_border, urban_rural, period_idx):
    p = h_base
    trend = period_idx * 0.005

    diabetes = _clamp(14.0 - p * 7.0 + _noise(1.2), 4.0, 22.0)
    heart_disease = _clamp(12.0 - p * 6.0 + _noise(1.0), 3.0, 18.0)
    obesity = _clamp(38.0 - p * 18.0 + _noise(2.5), 15.0, 48.0)
    insurance = _clamp(55.0 + p * 40.0 + _noise(3.0) + trend * 10, 40.0, 98.0)
    mental = _clamp(35.0 + p * 50.0 + _noise(4.0) + trend * 5, 20.0, 95.0)
    preventive = _clamp(30.0 + p * 50.0 + _noise(3.5) + trend * 5, 15.0, 92.0)
    life_exp = _clamp(70.0 + p * 18.0 + _noise(0.8) + trend * 2, 66.0, 92.0)
    aqi = _clamp(65.0 - p * 40.0 + _noise(6.0) + (12.0 if is_border else 0), 8.0, 120.0)
    walkability = _clamp(25.0 + p * 55.0 + _noise(6.0) + (10.0 if urban_rural == "urban" else -5.0), 8.0, 95.0)
    food_access = _clamp(25.0 + p * 60.0 + _noise(5.0) + (-8.0 if urban_rural == "rural" else 0), 8.0, 95.0)

    health_score = _clamp(
        (100 - diabetes * 4) * 0.10 +
        (100 - heart_disease * 4.5) * 0.10 +
        (100 - obesity * 1.8) * 0.08 +
        insurance * 0.15 +
        mental * 0.12 +
        preventive * 0.12 +
        ((life_exp - 65) / 25 * 100) * 0.15 +
        (100 - aqi * 0.8) * 0.06 +
        walkability * 0.06 +
        food_access * 0.06,
        0, 100
    )

    return {
        "diabetes_rate": round(diabetes, 1),
        "heart_disease_rate": round(heart_disease, 1),
        "obesity_rate": round(obesity, 1),
        "insurance_coverage_pct": round(insurance, 1),
        "mental_health_score": round(mental, 1),
        "preventive_care_pct": round(preventive, 1),
        "life_expectancy": round(life_exp, 1),
        "air_quality_index": round(aqi, 1),
        "walkability_score": round(walkability, 1),
        "food_access_score": round(food_access, 1),
        "health_score": round(health_score, 1),
    }


def generate_financial_metrics(w_base, is_border, period_idx):
    p = w_base
    trend = period_idx * 0.003

    income = int(_clamp(25000 + p * 100000 + _noise(4000), 20000, 145000))
    poverty = _clamp(32.0 - p * 27.0 + _noise(2.5), 3.0, 42.0)
    unbanked = _clamp(20.0 - p * 17.0 + _noise(1.8), 1.0, 30.0)
    bank_branches = _clamp(1.0 + p * 5.0 + _noise(0.5), 0.3, 8.0)
    health_exp = int(_clamp(2500 + p * 9000 + _noise(700), 1200, 15000))
    medical_debt = _clamp(30.0 - p * 20.0 + _noise(2.5), 4.0, 42.0)
    col = _clamp(75 + p * 65 + _noise(7), 60, 185)
    small_biz = _clamp(2.5 + p * 9.0 + _noise(1.2), 0.8, 15.0)

    wealth_score = _clamp(
        ((income - 20000) / 125000 * 100) * 0.20 +
        (100 - poverty * 2.2) * 0.18 +
        (100 - unbanked * 3.5) * 0.15 +
        (bank_branches / 8 * 100) * 0.10 +
        (100 - medical_debt * 2.2) * 0.15 +
        ((200 - col) / 140 * 100) * 0.10 +
        (small_biz / 15 * 100) * 0.12,
        0, 100
    )

    return {
        "median_income": income,
        "poverty_rate": round(poverty, 1),
        "unbanked_rate": round(unbanked, 1),
        "bank_branches_per_10k": round(bank_branches, 1),
        "health_expenditure_per_cap": health_exp,
        "medical_debt_rate": round(medical_debt, 1),
        "cost_of_living_index": round(col, 1),
        "small_biz_density": round(small_biz, 1),
        "wealth_score": round(wealth_score, 1),
    }


def compute_vida_score(health_score, wealth_score):
    vida_index = round(health_score * 0.55 + wealth_score * 0.45, 1)
    gap = round(abs(health_score - wealth_score), 1)

    if gap < 8:
        direction = "balanced"
    elif health_score > wealth_score:
        direction = "health_leading"
    else:
        direction = "wealth_leading"

    # Quadrant: use placeholder, will be recomputed with medians after all data is in
    return {
        "vida_index": vida_index,
        "gap_score": gap,
        "gap_direction": direction,
        "quadrant": "unassigned",
    }


def pick_interventions(community_name, health, financial, vida):
    gaps = []
    if health["walkability_score"] < 50:
        gaps.append("walkability")
    if health["food_access_score"] < 50:
        gaps.append("food_access")
    if financial["unbanked_rate"] > 10:
        gaps.append("financial_inclusion")
    if health["preventive_care_pct"] < 55:
        gaps.append("preventive_care")
    if health["mental_health_score"] < 55:
        gaps.append("community_building")
    if health["air_quality_index"] > 60:
        gaps.append("air_quality")
    if health["mental_health_score"] < 50:
        gaps.append("mental_health")
    if financial["poverty_rate"] > 18:
        gaps.append("economic_development")
    if not gaps:
        gaps = ["community_building"]

    interventions = []
    for cat in gaps[:4]:
        templates = INTERVENTION_TEMPLATES[cat]
        picks = np.random.choice(len(templates), size=min(2, len(templates)), replace=False)
        for idx in picks:
            title, desc, impact, cost = templates[idx]
            interventions.append({
                "category": cat,
                "title": title,
                "description": desc,
                "estimated_impact": round(impact + _noise(0.3), 1),
                "cost_tier": cost,
            })

    interventions.sort(key=lambda x: x["estimated_impact"], reverse=True)
    for i, inv in enumerate(interventions):
        inv["priority_rank"] = i + 1
    return interventions


def seed():
    engine = reset_db()

    with engine.connect() as conn:
        # Insert regions
        region_ids = {}
        for name, rtype, country in REGIONS:
            conn.execute(text(
                "INSERT INTO regions (name, type, country) VALUES (:n, :t, :c)"
            ), {"n": name, "t": rtype, "c": country})
            result = conn.execute(text("SELECT last_insert_rowid()"))
            region_ids[name] = result.scalar()

        # Insert communities and generate metrics
        for comm in COMMUNITIES:
            name, state, pop, lat, lon, ur, border, tier, h_base, w_base = comm

            region_name = REGION_MAP.get(state, "Sun Belt")
            if border:
                region_name = "US-Mexico Border Corridor"
            rid = region_ids.get(region_name, 1)

            conn.execute(text("""
                INSERT INTO communities
                    (name, state, county, region_id, population, latitude, longitude,
                     urban_rural, border_community, blue_zone_tier)
                VALUES (:name, :state, :county, :rid, :pop, :lat, :lon, :ur, :border, :tier)
            """), {
                "name": name, "state": state, "county": None, "rid": rid,
                "pop": pop, "lat": lat, "lon": lon, "ur": ur,
                "border": 1 if border else 0, "tier": tier,
            })
            cid = conn.execute(text("SELECT last_insert_rowid()")).scalar()

            for pi, period in enumerate(PERIODS):
                health = generate_health_metrics(h_base, border, ur, pi)
                financial = generate_financial_metrics(w_base, border, pi)
                vida = compute_vida_score(health["health_score"], financial["wealth_score"])

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
                """), {"cid": cid, "period": period, **health})

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
                """), {"cid": cid, "period": period, **financial})

                conn.execute(text("""
                    INSERT INTO vida_scores
                        (community_id, period, health_score, wealth_score,
                         vida_index, gap_score, gap_direction, quadrant, percentile_rank)
                    VALUES (:cid, :period, :hs, :ws, :vida_index, :gap_score,
                            :gap_direction, :quadrant, 0)
                """), {
                    "cid": cid, "period": period,
                    "hs": health["health_score"], "ws": financial["wealth_score"],
                    **vida,
                })

            # Interventions for latest period
            latest_health = generate_health_metrics(h_base, border, ur, 3)
            latest_financial = generate_financial_metrics(w_base, border, 3)
            latest_vida = compute_vida_score(latest_health["health_score"], latest_financial["wealth_score"])
            interventions = pick_interventions(name, latest_health, latest_financial, latest_vida)

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

        # --- ASSIGN QUADRANTS USING MEDIAN THRESHOLDS ---
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

        # Compute percentile ranks
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

    # Print summary
    from src.database import get_engine as ge
    eng = ge()
    with eng.connect() as c:
        import pandas as pd
        dist = pd.read_sql(text("SELECT quadrant, COUNT(*) as n FROM vida_scores WHERE period='2024-Q4' GROUP BY quadrant"), c)
        print("VerdeAzul database seeded successfully.")
        print(f"  Communities: {len(COMMUNITIES)}")
        print(f"  Quadrant distribution (Q4):")
        for _, row in dist.iterrows():
            print(f"    {row['quadrant']}: {row['n']}")


if __name__ == "__main__":
    seed()
