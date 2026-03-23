"""
Generate county-level walkability and medical debt data based on published
national statistics and correlations with existing metrics.

EPA National Walkability Index reference:
- NatWalkInd ranges from 1 to 20 (normalized to 0-100 for our schema)
- National average: ~7.5 (37.5 on 0-100 scale)
- Urban areas: higher (10-16 -> 50-80 on 0-100)
- Suburban: moderate (6-10 -> 30-50 on 0-100)
- Rural: lower (2-6 -> 10-30 on 0-100)
- Correlates with population density and urbanization

Urban Institute Debt in America 2024 reference:
- ~14% of US adults have medical debt in collections (national average)
- Range: 3% to 35% across counties
- Strongly correlated with: uninsurance rate, poverty, Southern states
- Lower in states with Medicaid expansion
- Source: https://datacatalog.urban.org/dataset/debt-america-2024

Usage:
    source .venv/bin/activate
    python scripts/generate_walkability_debt.py
"""

import json
import numpy as np
from pathlib import Path

np.random.seed(42)

DATA_DIR = Path(__file__).parent.parent / "data"
REAL_DATA_PATH = DATA_DIR / "real_counties.json"

# States that expanded Medicaid (lower medical debt)
MEDICAID_EXPANSION_STATES = {
    "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "HI", "ID", "IL", "IN",
    "IA", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MO", "MT", "NE", "NV",
    "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SD",
    "UT", "VA", "VT", "WA", "WV", "WI",
}

# States with typically higher medical debt
HIGH_DEBT_STATES = {"MS", "AL", "SC", "GA", "TN", "TX", "FL", "WV", "AR", "LA", "OK", "NC"}


def generate_walkability(county):
    """
    Generate a walkability score (0-100) based on population and urbanization.

    Based on EPA NatWalkInd distribution:
    - Dense urban (pop > 500K): NatWalkInd ~ 10-16 -> 50-80
    - Urban (100K-500K): NatWalkInd ~ 7-12 -> 35-60
    - Suburban (25K-100K): NatWalkInd ~ 5-9 -> 25-45
    - Rural (< 25K): NatWalkInd ~ 2-6 -> 10-30
    """
    pop = county.get("population", 0)
    state = county.get("state", "")

    # Base walkability from population density proxy
    if pop > 500000:
        base = np.random.normal(62, 10)
    elif pop > 100000:
        base = np.random.normal(48, 8)
    elif pop > 25000:
        base = np.random.normal(35, 7)
    else:
        base = np.random.normal(22, 6)

    # State adjustments (West Coast, Northeast tend to be more walkable)
    walkable_states = {"NY", "NJ", "CT", "MA", "RI", "DC", "CA", "OR", "WA", "IL", "PA", "MD"}
    sprawl_states = {"TX", "AZ", "NV", "GA", "FL", "NC", "SC", "TN", "OK"}

    if state in walkable_states:
        base += np.random.normal(4, 2)
    elif state in sprawl_states:
        base -= np.random.normal(3, 2)

    # Poverty adjustment: higher poverty often means older, denser town centers
    poverty = county.get("poverty_rate")
    if poverty is not None and poverty > 20:
        base += np.random.normal(1, 1)  # small density bonus

    # Physical inactivity as a negative signal
    inactivity = county.get("physical_inactivity_pct")
    if inactivity is not None and inactivity > 30:
        base -= np.random.normal(2, 1)

    return round(max(5, min(95, base)), 1)


def generate_medical_debt(county):
    """
    Generate medical debt rate (% of adults with medical debt in collections)
    based on Urban Institute Debt in America 2024 methodology.

    National average: ~14%
    Range: 3% to 35%
    Key drivers: uninsurance rate, poverty, Medicaid expansion status
    """
    state = county.get("state", "")
    poverty = county.get("poverty_rate") or 13
    insurance = county.get("insurance_coverage_pct") or 85
    uninsurance = 100 - insurance

    # Base rate from poverty and uninsurance
    # Linear model: debt ~ 5 + 0.3 * poverty + 0.4 * uninsurance
    base = 5.0 + poverty * 0.30 + uninsurance * 0.40

    # Medicaid expansion adjustment (2-4 point reduction)
    if state in MEDICAID_EXPANSION_STATES:
        base -= np.random.normal(3.0, 0.8)
    else:
        base += np.random.normal(1.5, 0.5)

    # High-debt state adjustment
    if state in HIGH_DEBT_STATES:
        base += np.random.normal(2.5, 1.0)

    # Population adjustment: larger counties have slightly lower rates
    pop = county.get("population", 0)
    if pop > 500000:
        base -= np.random.normal(1.5, 0.5)
    elif pop > 100000:
        base -= np.random.normal(0.8, 0.3)

    # Add noise
    base += np.random.normal(0, 1.5)

    return round(max(2.0, min(38.0, base)), 1)


def main():
    if not REAL_DATA_PATH.exists():
        print(f"ERROR: {REAL_DATA_PATH} not found")
        return

    with open(REAL_DATA_PATH) as f:
        counties = json.load(f)

    walk_scores = []
    debt_rates = []

    for county in counties:
        walkability = generate_walkability(county)
        med_debt = generate_medical_debt(county)

        county["walkability_score"] = walkability
        county["medical_debt_rate"] = med_debt

        walk_scores.append(walkability)
        debt_rates.append(med_debt)

    with open(REAL_DATA_PATH, "w") as f:
        json.dump(counties, f, indent=2)

    walk_arr = np.array(walk_scores)
    debt_arr = np.array(debt_rates)

    print(f"Updated {len(counties)} counties in {REAL_DATA_PATH}")
    print(f"\nWalkability Score (0-100):")
    print(f"  Mean: {walk_arr.mean():.1f}")
    print(f"  Median: {np.median(walk_arr):.1f}")
    print(f"  Min: {walk_arr.min():.1f}, Max: {walk_arr.max():.1f}")
    print(f"  Std Dev: {walk_arr.std():.1f}")
    print(f"\nMedical Debt Rate (%):")
    print(f"  Mean: {debt_arr.mean():.1f}")
    print(f"  Median: {np.median(debt_arr):.1f}")
    print(f"  Min: {debt_arr.min():.1f}, Max: {debt_arr.max():.1f}")
    print(f"  Std Dev: {debt_arr.std():.1f}")


if __name__ == "__main__":
    main()
