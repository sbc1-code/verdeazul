-- VerdeAzul | SQL Analytics Showcase
-- 10 queries demonstrating CTEs, window functions, percentiles, gap analysis


-- 1. COMMUNITY RANKINGS: Top 15 by Vida Index with state-level ranking
-- Uses DENSE_RANK window function + multi-table join
SELECT
    c.name,
    c.state,
    c.blue_zone_tier,
    v.vida_index,
    v.health_score,
    v.wealth_score,
    v.quadrant,
    DENSE_RANK() OVER (PARTITION BY c.state ORDER BY v.vida_index DESC) AS state_rank,
    DENSE_RANK() OVER (ORDER BY v.vida_index DESC) AS overall_rank
FROM vida_scores v
JOIN communities c ON c.community_id = v.community_id
WHERE v.period = '2024-Q4'
ORDER BY v.vida_index DESC
LIMIT 15;


-- 2. GAP ANALYSIS: Communities where health and wealth diverge most
-- These are the most interesting intervention targets
SELECT
    c.name,
    c.state,
    v.health_score,
    v.wealth_score,
    v.gap_score,
    v.gap_direction,
    v.quadrant,
    CASE
        WHEN v.gap_direction = 'health_leading' THEN 'Invest in financial infrastructure'
        WHEN v.gap_direction = 'wealth_leading' THEN 'Invest in health access'
        ELSE 'Maintain balance'
    END AS primary_action
FROM vida_scores v
JOIN communities c ON c.community_id = v.community_id
WHERE v.period = '2024-Q4'
ORDER BY v.gap_score DESC
LIMIT 20;


-- 3. QUADRANT DISTRIBUTION: How many communities fall in each bucket
-- CTE + aggregation + percentage calculation
WITH quadrant_counts AS (
    SELECT
        v.quadrant,
        COUNT(*) AS community_count,
        ROUND(AVG(v.vida_index), 1) AS avg_vida,
        ROUND(AVG(v.gap_score), 1) AS avg_gap
    FROM vida_scores v
    WHERE v.period = '2024-Q4'
    GROUP BY v.quadrant
),
total AS (
    SELECT COUNT(*) AS n FROM vida_scores WHERE period = '2024-Q4'
)
SELECT
    qc.quadrant,
    qc.community_count,
    ROUND(CAST(qc.community_count AS REAL) / t.n * 100, 1) AS pct_of_total,
    qc.avg_vida,
    qc.avg_gap
FROM quadrant_counts qc
CROSS JOIN total t
ORDER BY qc.avg_vida DESC;


-- 4. PERIOD-OVER-PERIOD TREND: Quarter-by-quarter vida index change
-- Uses LAG window function to compute deltas
SELECT
    c.name,
    c.state,
    v.period,
    v.vida_index,
    LAG(v.vida_index) OVER (PARTITION BY c.community_id ORDER BY v.period) AS prev_vida,
    ROUND(
        v.vida_index - COALESCE(
            LAG(v.vida_index) OVER (PARTITION BY c.community_id ORDER BY v.period),
            v.vida_index
        ), 1
    ) AS delta
FROM vida_scores v
JOIN communities c ON c.community_id = v.community_id
ORDER BY c.name, v.period;


-- 5. BORDER VS NON-BORDER: Comparative analysis
-- Grouped aggregation with HAVING filter
SELECT
    CASE WHEN c.border_community = 1 THEN 'Border' ELSE 'Non-Border' END AS category,
    COUNT(DISTINCT c.community_id) AS communities,
    ROUND(AVG(v.health_score), 1) AS avg_health,
    ROUND(AVG(v.wealth_score), 1) AS avg_wealth,
    ROUND(AVG(v.vida_index), 1) AS avg_vida,
    ROUND(AVG(v.gap_score), 1) AS avg_gap,
    ROUND(AVG(h.life_expectancy), 1) AS avg_life_exp,
    ROUND(AVG(f.median_income)) AS avg_income
FROM vida_scores v
JOIN communities c ON c.community_id = v.community_id
JOIN health_metrics h ON h.community_id = c.community_id AND h.period = v.period
JOIN financial_metrics f ON f.community_id = c.community_id AND f.period = v.period
WHERE v.period = '2024-Q4'
GROUP BY c.border_community;


-- 6. INTERVENTION ROI RANKING: Highest impact per dollar across all communities
-- Multi-join CTE with conditional scoring
WITH intervention_value AS (
    SELECT
        i.intervention_id,
        c.name AS community_name,
        c.state,
        i.category,
        i.title,
        i.estimated_impact,
        i.cost_tier,
        CASE i.cost_tier
            WHEN 'low' THEN 1
            WHEN 'medium' THEN 2
            WHEN 'high' THEN 3
        END AS cost_rank,
        v.vida_index AS current_vida,
        v.quadrant
    FROM interventions i
    JOIN communities c ON c.community_id = i.community_id
    JOIN vida_scores v ON v.community_id = c.community_id AND v.period = i.period
)
SELECT
    community_name,
    state,
    category,
    title,
    estimated_impact,
    cost_tier,
    ROUND(estimated_impact / cost_rank, 2) AS impact_per_cost,
    current_vida,
    quadrant
FROM intervention_value
ORDER BY impact_per_cost DESC
LIMIT 15;


-- 7. INCOME vs LIFE EXPECTANCY CORRELATION: the money-health link
-- Subquery + bucketed analysis
SELECT
    income_bucket,
    COUNT(*) AS communities,
    ROUND(AVG(life_expectancy), 1) AS avg_life_exp,
    ROUND(AVG(health_score), 1) AS avg_health,
    ROUND(AVG(vida_index), 1) AS avg_vida
FROM (
    SELECT
        c.community_id,
        h.life_expectancy,
        v.health_score,
        v.vida_index,
        CASE
            WHEN f.median_income < 35000 THEN '< $35K'
            WHEN f.median_income < 55000 THEN '$35K-$55K'
            WHEN f.median_income < 80000 THEN '$55K-$80K'
            WHEN f.median_income < 110000 THEN '$80K-$110K'
            ELSE '$110K+'
        END AS income_bucket
    FROM communities c
    JOIN health_metrics h ON h.community_id = c.community_id AND h.period = '2024-Q4'
    JOIN financial_metrics f ON f.community_id = c.community_id AND f.period = '2024-Q4'
    JOIN vida_scores v ON v.community_id = c.community_id AND v.period = '2024-Q4'
) bucketed
GROUP BY income_bucket
ORDER BY AVG(vida_index) DESC;


-- 8. RUNNING AVERAGE: Smoothed vida index trend per community
-- Window function with frame specification
SELECT
    c.name,
    v.period,
    v.vida_index,
    ROUND(
        AVG(v.vida_index) OVER (
            PARTITION BY c.community_id
            ORDER BY v.period
            ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING
        ), 1
    ) AS rolling_avg_3q
FROM vida_scores v
JOIN communities c ON c.community_id = v.community_id
ORDER BY c.name, v.period;


-- 9. CRITICAL INTERVENTION OPPORTUNITIES: communities that need the most help
-- Multi-level CTE with prioritization logic
WITH critical AS (
    SELECT
        c.community_id,
        c.name,
        c.state,
        c.border_community,
        v.vida_index,
        v.quadrant,
        v.gap_score,
        h.life_expectancy,
        f.poverty_rate,
        f.unbanked_rate
    FROM communities c
    JOIN vida_scores v ON v.community_id = c.community_id AND v.period = '2024-Q4'
    JOIN health_metrics h ON h.community_id = c.community_id AND h.period = '2024-Q4'
    JOIN financial_metrics f ON f.community_id = c.community_id AND f.period = '2024-Q4'
    WHERE v.quadrant IN ('critical', 'wealth_not_helping')
),
with_interventions AS (
    SELECT
        cr.*,
        COUNT(i.intervention_id) AS intervention_count,
        ROUND(SUM(i.estimated_impact), 1) AS total_potential_impact
    FROM critical cr
    LEFT JOIN interventions i ON i.community_id = cr.community_id
    GROUP BY cr.community_id
)
SELECT
    name,
    state,
    vida_index,
    quadrant,
    life_expectancy,
    poverty_rate,
    unbanked_rate,
    intervention_count,
    total_potential_impact,
    ROUND(vida_index + total_potential_impact, 1) AS projected_vida_after
FROM with_interventions
ORDER BY total_potential_impact DESC;


-- 10. BLUE ZONE TIER BENCHMARKING: how do tiers compare on every dimension
-- Comprehensive multi-metric aggregation
SELECT
    c.blue_zone_tier AS tier,
    COUNT(DISTINCT c.community_id) AS n,
    ROUND(AVG(v.vida_index), 1) AS avg_vida,
    ROUND(AVG(h.life_expectancy), 1) AS avg_life_exp,
    ROUND(AVG(h.diabetes_rate), 1) AS avg_diabetes,
    ROUND(AVG(h.obesity_rate), 1) AS avg_obesity,
    ROUND(AVG(h.insurance_coverage_pct), 1) AS avg_insurance,
    ROUND(AVG(h.walkability_score), 1) AS avg_walkability,
    ROUND(AVG(h.food_access_score), 1) AS avg_food_access,
    ROUND(AVG(f.median_income)) AS avg_income,
    ROUND(AVG(f.poverty_rate), 1) AS avg_poverty,
    ROUND(AVG(f.unbanked_rate), 1) AS avg_unbanked,
    ROUND(AVG(f.medical_debt_rate), 1) AS avg_medical_debt
FROM communities c
JOIN vida_scores v ON v.community_id = c.community_id AND v.period = '2024-Q4'
JOIN health_metrics h ON h.community_id = c.community_id AND h.period = '2024-Q4'
JOIN financial_metrics f ON f.community_id = c.community_id AND f.period = '2024-Q4'
GROUP BY c.blue_zone_tier
ORDER BY avg_vida DESC;
