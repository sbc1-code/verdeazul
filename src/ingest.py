"""
Ingest real public health and economic data for VerdeAzul.

Sources (all free, no API keys required except Census):
- CDC PLACES: county-level health measures (diabetes, obesity, insurance, etc.)
- EPA AQI: annual air quality by county
- FDIC: bank branch counts by county

Census ACS (median income, poverty) requires a free API key.
Set environment variable CENSUS_API_KEY or pass it as argument.

Usage:
    python -m src.ingest                    # fetch all, save to data/
    python -m src.ingest --census-key XXXXX  # include Census economic data
"""

import json
import csv
import io
import sys
import time
import zipfile
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

DATA_DIR = Path(__file__).parent.parent / "data"

# CDC PLACES measures we care about and their mapping to our schema
PLACES_MEASURES = {
    "DIABETES": "diabetes_rate",
    "CHD": "heart_disease_rate",
    "OBESITY": "obesity_rate",
    "ACCESS2": "lack_insurance_pct",  # inverted: 100 - this = insurance_coverage
    "MHLTH": "mental_distress_pct",   # inverted: 100 - this = mental_health_score
    "CHECKUP": "preventive_care_pct",
    "DEPRESSION": "depression_pct",
    "CSMOKING": "smoking_pct",
    "LPA": "physical_inactivity_pct",
    "BINGE": "binge_drinking_pct",
    "SLEEP": "short_sleep_pct",
}

# Border county FIPS codes (US-Mexico border)
BORDER_FIPS = {
    # Texas
    "48141",  # El Paso
    "48243",  # Jeff Davis
    "48377",  # Presidio
    "48043",  # Brewster
    "48371",  # Pecos
    "48443",  # Terrell
    "48465",  # Val Verde
    "48323",  # Maverick
    "48479",  # Webb
    "48427",  # Starr
    "48215",  # Hidalgo
    "48061",  # Cameron
    "48505",  # Zapata
    "48247",  # Jim Hogg
    "48311",  # McMullen
    # New Mexico
    "35013",  # Dona Ana
    "35023",  # Hidalgo
    "35029",  # Luna
    "35035",  # Otero
    # Arizona
    "04003",  # Cochise
    "04019",  # Pima
    "04023",  # Santa Cruz
    "04027",  # Yuma
    # California
    "06025",  # Imperial
    "06073",  # San Diego
}

# Known Blue Zone tier assignments by county name/state
BLUE_ZONE_TIERS = {
    ("San Bernardino", "CA"): "proven",  # Loma Linda is in San Bernardino County
    ("Freeborn", "MN"): "certified",     # Albert Lea
    ("Los Angeles", "CA"): "certified",   # Beach Cities
    ("Collier", "FL"): "certified",       # Naples
    ("Tarrant", "TX"): "certified",       # Fort Worth
    ("Linn", "IA"): "certified",          # Cedar Rapids
    ("Johnson", "IA"): "certified",       # Iowa City
    ("Monterey", "CA"): "certified",      # Monterey
    ("Napa", "CA"): "certified",          # St. Helena
    ("Walla Walla", "WA"): "certified",   # Walla Walla
    ("Hawaii", "HI"): "certified",        # Kailua-Kona
    ("Summit", "CO"): "high_potential",
    ("Pitkin", "CO"): "high_potential",
    ("Eagle", "CO"): "high_potential",
    ("Marin", "CA"): "high_potential",
    ("Santa Clara", "CA"): "high_potential",
    ("Fairfax", "VA"): "high_potential",
    ("Teton", "WY"): "high_potential",
    ("Blaine", "ID"): "high_potential",
    ("Los Alamos", "NM"): "high_potential",
    ("Benton", "OR"): "high_potential",
    ("Bergen", "NJ"): "high_potential",
}


def fetch_json(url, label=""):
    """Fetch JSON from URL with retries."""
    for attempt in range(3):
        try:
            req = Request(url, headers={"User-Agent": "VerdeAzul/1.0"})
            with urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            print(f"  Retry {attempt+1}/3 for {label}: {e}")
            time.sleep(2)
    print(f"  FAILED: {label}")
    return None


def fetch_cdc_places():
    """Fetch CDC PLACES county-level data for key health measures."""
    print("Fetching CDC PLACES county data...")
    all_data = {}

    for measure_id, field_name in PLACES_MEASURES.items():
        url = (
            f"https://data.cdc.gov/resource/swc5-untb.json"
            f"?measureid={measure_id}&datavaluetypeid=CrdPrv&$limit=50000"
            f"&$select=locationid,locationname,stateabbr,data_value,totalpopulation,geolocation"
        )
        data = fetch_json(url, f"PLACES {measure_id}")
        if not data:
            continue

        count = 0
        for row in data:
            fips = row.get("locationid", "")
            if not fips or not row.get("data_value"):
                continue

            if fips not in all_data:
                geo = row.get("geolocation", {})
                coords = geo.get("coordinates", [None, None]) if isinstance(geo, dict) else [None, None]
                all_data[fips] = {
                    "fips": fips,
                    "name": row.get("locationname", ""),
                    "state": row.get("stateabbr", ""),
                    "population": int(row.get("totalpopulation", 0) or 0),
                    "longitude": coords[0] if coords else None,
                    "latitude": coords[1] if coords else None,
                }
            all_data[fips][field_name] = float(row["data_value"])
            count += 1

        print(f"  {measure_id}: {count} counties")

    print(f"  Total counties with data: {len(all_data)}")
    return all_data


def fetch_epa_aqi(year=2023):
    """Download EPA annual AQI by county."""
    print(f"Fetching EPA AQI data ({year})...")
    url = f"https://aqs.epa.gov/aqsweb/airdata/annual_aqi_by_county_{year}.zip"

    try:
        req = Request(url, headers={"User-Agent": "VerdeAzul/1.0"})
        with urlopen(req, timeout=60) as resp:
            zip_data = resp.read()

        with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
            csv_name = zf.namelist()[0]
            with zf.open(csv_name) as f:
                reader = csv.DictReader(io.TextIOWrapper(f))
                aqi_data = {}
                for row in reader:
                    state_fips = row.get("State", "").zfill(2)
                    county_fips = row.get("County", "").zfill(3)
                    fips = state_fips + county_fips
                    median_aqi = row.get("Median AQI", "")
                    if median_aqi:
                        aqi_data[fips] = float(median_aqi)

        print(f"  AQI data for {len(aqi_data)} counties")
        return aqi_data
    except Exception as e:
        print(f"  FAILED to fetch EPA AQI: {e}")
        return {}


def fetch_fdic_branches():
    """Fetch FDIC bank branch counts by county FIPS."""
    print("Fetching FDIC bank branch data...")
    # FDIC API allows getting all branches but it's huge.
    # We'll query state by state for the counts.
    # Actually, we can get branch counts by querying with grouping.
    # The API doesn't support GROUP BY, so we'll fetch all and count in Python.

    branch_counts = {}
    states = [
        "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
        "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
        "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
        "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
        "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC",
    ]

    for state in states:
        url = (
            f"https://banks.data.fdic.gov/api/locations"
            f"?filters=STALP:{state}&fields=STCNTYBR&limit=10000&fmt=json"
        )
        data = fetch_json(url, f"FDIC {state}")
        if not data or "data" not in data:
            continue

        for item in data["data"]:
            fips = str(item.get("data", {}).get("STCNTYBR", "")).zfill(5)
            if fips and fips != "00000":
                branch_counts[fips] = branch_counts.get(fips, 0) + 1

        # Check if there are more pages
        total = data.get("meta", {}).get("total", 0)
        if total > 10000:
            offset = 10000
            while offset < total:
                page_url = f"{url}&offset={offset}"
                page_data = fetch_json(page_url, f"FDIC {state} page {offset}")
                if page_data and "data" in page_data:
                    for item in page_data["data"]:
                        fips = str(item.get("data", {}).get("STCNTYBR", "")).zfill(5)
                        if fips and fips != "00000":
                            branch_counts[fips] = branch_counts.get(fips, 0) + 1
                offset += 10000

        time.sleep(0.3)  # rate limiting

    print(f"  Bank branch data for {len(branch_counts)} counties")
    return branch_counts


def fetch_census_acs(api_key=None):
    """Fetch Census ACS 5-year data: median income, poverty."""
    if not api_key:
        print("Skipping Census ACS (no API key). Set CENSUS_API_KEY env var.")
        return {}

    print("Fetching Census ACS data...")
    # B19013_001E = median household income
    # B17001_001E = poverty universe total
    # B17001_002E = below poverty
    url = (
        f"https://api.census.gov/data/2023/acs/acs5"
        f"?get=NAME,B19013_001E,B17001_001E,B17001_002E"
        f"&for=county:*&key={api_key}"
    )

    try:
        req = Request(url, headers={"User-Agent": "VerdeAzul/1.0"})
        with urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode())

        census_data = {}
        headers = data[0]
        for row in data[1:]:
            state_fips = row[headers.index("state")]
            county_fips = row[headers.index("county")]
            fips = state_fips + county_fips

            income = row[headers.index("B19013_001E")]
            pov_total = row[headers.index("B17001_001E")]
            pov_below = row[headers.index("B17001_002E")]

            entry = {}
            if income and income not in ("-666666666", "-999999999", "null"):
                entry["median_income"] = int(income)
            if pov_total and pov_below and pov_total not in ("0", "null"):
                try:
                    entry["poverty_rate"] = round(int(pov_below) / int(pov_total) * 100, 1)
                except (ValueError, ZeroDivisionError):
                    pass

            if entry:
                census_data[fips] = entry

        print(f"  Census data for {len(census_data)} counties")
        return census_data
    except Exception as e:
        print(f"  FAILED to fetch Census data: {e}")
        return {}


def merge_and_save(places, aqi, branches, census):
    """Merge all data sources and save processed file."""
    print("Merging data sources...")

    counties = []
    for fips, health in places.items():
        if not health.get("name") or not health.get("state"):
            continue
        if health.get("latitude") is None:
            continue

        pop = health.get("population", 0)
        if pop < 1000:
            continue  # skip very small counties

        # Determine border status
        is_border = fips in BORDER_FIPS

        # Determine Blue Zone tier
        tier_key = (health["name"], health["state"])
        tier = BLUE_ZONE_TIERS.get(tier_key, "unscored")

        # Build health metrics
        insurance = 100 - health.get("lack_insurance_pct", 15)
        mental = 100 - health.get("mental_distress_pct", 15)
        preventive = health.get("preventive_care_pct", 50)

        # AQI
        county_aqi = aqi.get(fips, 45)  # national median ~45

        # Bank branches
        branch_count = branches.get(fips, 3)
        branches_per_10k = round(branch_count / (pop / 10000), 1) if pop > 0 else 0

        # Census economic data
        econ = census.get(fips, {})
        median_income = econ.get("median_income")
        poverty_rate = econ.get("poverty_rate")

        county = {
            "fips": fips,
            "name": health["name"],
            "state": health["state"],
            "population": pop,
            "latitude": health["latitude"],
            "longitude": health["longitude"],
            "border_community": is_border,
            "blue_zone_tier": tier,
            # Health
            "diabetes_rate": health.get("diabetes_rate"),
            "heart_disease_rate": health.get("heart_disease_rate"),
            "obesity_rate": health.get("obesity_rate"),
            "insurance_coverage_pct": round(insurance, 1),
            "mental_health_score": round(mental, 1),
            "preventive_care_pct": round(preventive, 1),
            "air_quality_index": county_aqi,
            "depression_pct": health.get("depression_pct"),
            "smoking_pct": health.get("smoking_pct"),
            "physical_inactivity_pct": health.get("physical_inactivity_pct"),
            # Economic
            "median_income": median_income,
            "poverty_rate": poverty_rate,
            "bank_branches_per_10k": branches_per_10k,
        }
        counties.append(county)

    # Sort by population descending
    counties.sort(key=lambda x: x["population"], reverse=True)

    output_path = DATA_DIR / "real_counties.json"
    DATA_DIR.mkdir(exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(counties, f, indent=2)

    print(f"Saved {len(counties)} counties to {output_path}")
    return counties


def ingest(census_key=None):
    """Run full ingestion pipeline."""
    import os
    key = census_key or os.environ.get("CENSUS_API_KEY")

    places = fetch_cdc_places()
    aqi = fetch_epa_aqi()
    branches = fetch_fdic_branches()
    census = fetch_census_acs(key)

    counties = merge_and_save(places, aqi, branches, census)
    print(f"\nIngestion complete. {len(counties)} counties ready.")
    print("Run `python -m src.seed` to rebuild the database with real data.")


if __name__ == "__main__":
    key = None
    if "--census-key" in sys.argv:
        idx = sys.argv.index("--census-key")
        if idx + 1 < len(sys.argv):
            key = sys.argv[idx + 1]
    ingest(key)
