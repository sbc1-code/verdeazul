-- VerdeAzul | Community Longevity Potential Index
-- Star schema: dimensions + facts + computed scores + prescriptive interventions

-- ---------------------------------------------------------------------------
-- DIMENSION TABLES
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS regions (
    region_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    type            TEXT NOT NULL CHECK (type IN ('state', 'border_zone', 'metro', 'rural', 'province')),
    country         TEXT NOT NULL DEFAULT 'US'
);

CREATE TABLE IF NOT EXISTS communities (
    community_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    state           TEXT NOT NULL,
    county          TEXT,
    region_id       INTEGER REFERENCES regions(region_id),
    population      INTEGER,
    latitude        REAL,
    longitude       REAL,
    urban_rural     TEXT CHECK (urban_rural IN ('urban', 'suburban', 'rural')),
    border_community BOOLEAN DEFAULT 0,
    blue_zone_tier  TEXT CHECK (blue_zone_tier IN ('proven', 'certified', 'high_potential', 'emerging', 'unscored')),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_communities_state ON communities(state);
CREATE INDEX IF NOT EXISTS idx_communities_tier ON communities(blue_zone_tier);

-- ---------------------------------------------------------------------------
-- FACT TABLES
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS health_metrics (
    metric_id               INTEGER PRIMARY KEY AUTOINCREMENT,
    community_id            INTEGER NOT NULL REFERENCES communities(community_id),
    period                  TEXT NOT NULL,  -- '2024-Q1', '2024-Q2', etc.
    diabetes_rate           REAL,   -- % of adults
    heart_disease_rate      REAL,   -- % of adults
    obesity_rate            REAL,   -- % of adults
    insurance_coverage_pct  REAL,   -- % with any coverage
    mental_health_score     REAL,   -- 0-100 (higher = better)
    preventive_care_pct     REAL,   -- % getting annual checkups
    life_expectancy         REAL,   -- years
    air_quality_index       REAL,   -- EPA AQI (lower = better)
    walkability_score       REAL,   -- 0-100
    food_access_score       REAL,   -- 0-100 (farmers markets, grocery density)
    health_score            REAL,   -- computed composite 0-100
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_health_community ON health_metrics(community_id, period);

CREATE TABLE IF NOT EXISTS financial_metrics (
    metric_id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    community_id                INTEGER NOT NULL REFERENCES communities(community_id),
    period                      TEXT NOT NULL,
    median_income               INTEGER,
    poverty_rate                REAL,   -- %
    unbanked_rate               REAL,   -- %
    bank_branches_per_10k       REAL,
    health_expenditure_per_cap  REAL,   -- annual $
    medical_debt_rate           REAL,   -- % of adults with medical debt
    cost_of_living_index        REAL,   -- 100 = national avg
    small_biz_density           REAL,   -- per 1,000 residents
    wealth_score                REAL,   -- computed composite 0-100
    created_at                  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_financial_community ON financial_metrics(community_id, period);

-- ---------------------------------------------------------------------------
-- COMPUTED SCORES
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS vida_scores (
    score_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    community_id        INTEGER NOT NULL REFERENCES communities(community_id),
    period              TEXT NOT NULL,
    health_score        REAL,
    wealth_score        REAL,
    vida_index          REAL,       -- weighted composite 0-100
    gap_score           REAL,       -- abs(health - wealth), higher = more imbalanced
    gap_direction       TEXT CHECK (gap_direction IN ('health_leading', 'wealth_leading', 'balanced')),
    quadrant            TEXT,
    percentile_rank     REAL,       -- 0-100 among all communities
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(community_id, period)
);

CREATE INDEX IF NOT EXISTS idx_vida_scores_period ON vida_scores(period);
CREATE INDEX IF NOT EXISTS idx_vida_scores_quadrant ON vida_scores(quadrant);

-- ---------------------------------------------------------------------------
-- PRESCRIPTIVE LAYER: what a community can actually DO
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS interventions (
    intervention_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    community_id        INTEGER NOT NULL REFERENCES communities(community_id),
    period              TEXT NOT NULL,
    category            TEXT NOT NULL,
    title               TEXT NOT NULL,
    description         TEXT,
    estimated_impact    REAL,       -- projected vida_index point increase
    cost_tier           TEXT CHECK (cost_tier IN ('low', 'medium', 'high')),
    priority_rank       INTEGER,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_interventions_community ON interventions(community_id);
