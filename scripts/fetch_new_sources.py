"""
Fetch EPA Walkability Index and Urban Institute Medical Debt data,
aggregate to county level, and merge into data/real_counties.json.

Usage:
    python scripts/fetch_new_sources.py
"""

import json
import csv
import io
import sys
import os
import zipfile
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from collections import defaultdict

DATA_DIR = Path(__file__).parent.parent / "data"
REAL_DATA_PATH = DATA_DIR / "real_counties.json"


def _read_walkability_gdb(zip_path, all_names):
    """Read walkability data from a geodatabase inside a ZIP file using pyogrio."""
    try:
        import pyogrio
    except ImportError:
        print("  SKIP: pyogrio not installed. Cannot read GDB.")
        print("  Install with: pip install pyogrio")
        return {}

    import tempfile, shutil

    # Extract the ZIP to a temp directory
    extract_dir = tempfile.mkdtemp(prefix="walkability_")
    print(f"  Extracting ZIP to {extract_dir}...")

    try:
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(extract_dir)

        # Find the .gdb directory
        gdb_path = None
        for root, dirs, files in os.walk(extract_dir):
            for d in dirs:
                if d.lower().endswith(".gdb"):
                    gdb_path = os.path.join(root, d)
                    break
            if gdb_path:
                break

        if not gdb_path:
            print("  SKIP: Could not find .gdb directory after extraction")
            return {}

        print(f"  Found GDB: {gdb_path}")

        # List layers
        layers = pyogrio.list_layers(gdb_path)
        print(f"  Layers: {layers}")

        # Find the right layer
        target_layer = None
        for layer_info in layers:
            layer_name = layer_info[0] if isinstance(layer_info, (list, tuple)) else str(layer_info)
            if "walk" in layer_name.lower() or "sld" in layer_name.lower():
                target_layer = layer_name
                break
        if not target_layer:
            target_layer = layers[0][0] if isinstance(layers[0], (list, tuple)) else str(layers[0])

        print(f"  Reading layer: {target_layer} (no geometry, attributes only)...")

        # Read without geometry for speed
        # First check available columns
        info = pyogrio.read_info(gdb_path, layer=target_layer)
        fields = info.get("fields", []) if isinstance(info, dict) else []
        # pyogrio.read_info returns a dict with 'columns' key
        if not fields:
            # Try reading just a few rows to get column names
            df_sample = pyogrio.read_dataframe(
                gdb_path, layer=target_layer, read_geometry=False, max_features=5
            )
            fields = list(df_sample.columns)

        print(f"  Fields: {list(fields)[:15]}...")

        # Find GEOID and NatWalkInd columns
        geoid_field = None
        walk_field = None
        for f in fields:
            fl = f.lower()
            if "geoid" in fl and geoid_field is None:
                geoid_field = f
            if "natwalkind" in fl:
                walk_field = f

        if not geoid_field or not walk_field:
            print(f"  SKIP: Could not find GEOID and NatWalkInd fields")
            print(f"  Available fields: {list(fields)}")
            return {}

        print(f"  Using: GEOID={geoid_field}, Walk={walk_field}")

        # Read only the columns we need (much faster, no geometry)
        df = pyogrio.read_dataframe(
            gdb_path, layer=target_layer,
            read_geometry=False,
            columns=[geoid_field, walk_field],
        )

        print(f"  Read {len(df):,} block groups")

        # Aggregate to county level
        df["county_fips"] = df[geoid_field].astype(str).str[:5]
        df[walk_field] = df[walk_field].astype(float)
        # Filter out zero/null values
        df = df[df[walk_field] > 0]

        county_avg = df.groupby("county_fips")[walk_field].mean()

        # Normalize from 1-20 scale to 0-100
        result = {}
        for fips, avg_walk in county_avg.items():
            normalized = round(min(max(avg_walk * 5, 0), 100), 1)
            result[fips] = normalized

        print(f"  Walkability scores for {len(result)} counties")
        return result

    except Exception as e:
        print(f"  Error reading GDB: {e}")
        import traceback
        traceback.print_exc()
        return {}
    finally:
        # Cleanup
        try:
            shutil.rmtree(extract_dir)
        except Exception:
            pass


def fetch_epa_walkability():
    """
    Download the EPA National Walkability Index ZIP.
    The ZIP contains a CSV with census block group level data.
    We aggregate NatWalkInd to county level (simple average) using the
    first 5 digits of the GEOID (block group FIPS -> county FIPS).

    Returns dict: {county_fips: walkability_score_0_to_100}
    """
    print("Fetching EPA National Walkability Index...")
    url = "https://edg.epa.gov/EPADataCommons/public/OA/WalkabilityIndex.zip"
    cache_path = "/tmp/walkability_index.zip"

    try:
        # Use cached download if available
        if os.path.exists(cache_path) and os.path.getsize(cache_path) > 1000000:
            print(f"  Using cached download: {cache_path} ({os.path.getsize(cache_path) / 1024 / 1024:.0f} MB)")
            with open(cache_path, "rb") as f:
                data = f.read()
        else:
            req = Request(url, headers={"User-Agent": "VerdeAzul/1.0"})
            print(f"  Downloading from {url}")
            print("  (This file is ~425MB, may take several minutes...)")

            resp = urlopen(req, timeout=300)
            content_type = resp.headers.get("Content-Type", "")
            first_bytes = resp.read(4)

            if first_bytes[:2] != b"PK":
                print(f"  SKIP: Response is not a ZIP file (Content-Type: {content_type})")
                resp.close()
                return {}

            # Read the rest
            print("  Downloading ZIP contents...")
            data = first_bytes + resp.read()
            resp.close()
            print(f"  Downloaded {len(data) / 1024 / 1024:.0f} MB")

            # Cache for future runs
            with open(cache_path, "wb") as f:
                f.write(data)
            print(f"  Cached to {cache_path}")

        # Extract CSV from ZIP
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            all_names = zf.namelist()
            print(f"  ZIP contains {len(all_names)} files:")
            for nm in all_names[:20]:
                print(f"    {nm}")
            if len(all_names) > 20:
                print(f"    ... and {len(all_names) - 20} more")

            # Look for CSV, DBF, or GDB files
            csv_names = [n for n in all_names if n.lower().endswith(".csv")]
            dbf_names = [n for n in all_names if n.lower().endswith(".dbf")]
            gdb_names = [n for n in all_names if ".gdb" in n.lower()]

            if not csv_names:
                print(f"  No CSV files found. DBF files: {len(dbf_names)}, GDB paths: {len(gdb_names)}")
                if gdb_names:
                    print("  This ZIP contains a geodatabase (GDB). Need to extract and read with geopandas.")
                    # Save the ZIP for geopandas processing
                    import tempfile
                    tmp_path = "/tmp/walkability_index.zip"
                    with open(tmp_path, "wb") as tmpf:
                        tmpf.write(data)
                    print(f"  Saved ZIP to {tmp_path} for geodatabase extraction")
                    return _read_walkability_gdb(tmp_path, all_names)
                print("  SKIP: No usable data files in ZIP")
                return {}

            csv_name = csv_names[0]
            print(f"  Extracting {csv_name}...")

            with zf.open(csv_name) as f:
                reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"))

                # Find the right columns
                county_walkability = defaultdict(list)
                row_count = 0
                geoid_col = None
                walk_col = None

                for row in reader:
                    if row_count == 0:
                        # Detect column names (may vary)
                        cols = list(row.keys())
                        for c in cols:
                            if "geoid" in c.lower() or c == "GEOID10" or c == "GEOID20":
                                geoid_col = c
                            if "natwalkind" in c.lower():
                                walk_col = c
                        if not geoid_col or not walk_col:
                            print(f"  SKIP: Could not find GEOID/NatWalkInd columns. Columns: {cols[:10]}")
                            return {}
                        print(f"  Using columns: GEOID={geoid_col}, Walk={walk_col}")

                    geoid = str(row.get(geoid_col, ""))
                    walk_val = row.get(walk_col, "")

                    if len(geoid) >= 5 and walk_val:
                        try:
                            county_fips = geoid[:5]
                            walk_score = float(walk_val)
                            county_walkability[county_fips].append(walk_score)
                        except (ValueError, TypeError):
                            pass

                    row_count += 1
                    if row_count % 100000 == 0:
                        print(f"  Processed {row_count:,} block groups...")

                print(f"  Total block groups processed: {row_count:,}")

        # Aggregate: simple average per county, then normalize to 0-100
        result = {}
        for fips, scores in county_walkability.items():
            avg_walk = sum(scores) / len(scores)
            # NatWalkInd is 1-20; normalize to 0-100
            normalized = round(min(max(avg_walk * 5, 0), 100), 1)
            result[fips] = normalized

        print(f"  Walkability scores for {len(result)} counties")
        return result

    except Exception as e:
        print(f"  FAILED to fetch EPA Walkability: {e}")
        return {}


def fetch_urban_medical_debt():
    """
    Fetch Urban Institute Debt in America county-level medical debt data.

    Tries multiple known download patterns since Urban Institute uses
    Cloudflare protection. Falls back to their GitHub data if available.

    Returns dict: {county_fips: medical_debt_rate_pct}
    """
    print("Fetching Urban Institute Medical Debt data...")

    # Try several known download URL patterns
    urls_to_try = [
        # Direct S3 patterns used by Urban Institute
        "https://urban-data-catalog.s3.amazonaws.com/drupal-root-live/2024/08/13/county_dia2024.csv",
        "https://urban-data-catalog.s3.amazonaws.com/drupal-root-live/2024/07/16/county_dia2024.csv",
        "https://urban-data-catalog.s3.amazonaws.com/drupal-root-live/2024/08/county_dia2024.csv",
        "https://urban-data-catalog.s3.amazonaws.com/drupal-root-live/2024/county_dia2024.csv",
        # Past dataset patterns
        "https://urban-data-catalog.s3.amazonaws.com/drupal-root-live/2023/04/27/county_dia2023.csv",
        "https://urban-data-catalog.s3.amazonaws.com/drupal-root-live/2023/08/22/county_dia2023.csv",
    ]

    for url in urls_to_try:
        try:
            print(f"  Trying: {url}")
            req = Request(url, headers={"User-Agent": "VerdeAzul/1.0"})
            resp = urlopen(req, timeout=30)
            content = resp.read().decode("utf-8-sig")
            resp.close()

            if content.startswith("<?xml") or content.startswith("<!DOCTYPE"):
                continue

            # Parse CSV
            reader = csv.DictReader(io.StringIO(content))
            result = {}
            cols = None
            for row in reader:
                if cols is None:
                    cols = list(row.keys())
                    print(f"  Columns found: {cols[:8]}...")

                # Find FIPS and medical debt columns
                fips = None
                med_debt = None
                for key in row:
                    kl = key.lower()
                    if "fips" in kl or "geoid" in kl or kl == "county_fips":
                        fips = str(row[key]).zfill(5)
                    if "medical" in kl and "debt" in kl and ("share" in kl or "rate" in kl or "pct" in kl):
                        try:
                            med_debt = float(row[key])
                        except (ValueError, TypeError):
                            pass
                    # Also try generic "med_debt" or "meddebt" patterns
                    if med_debt is None and ("meddebt" in kl or "med_debt" in kl):
                        try:
                            med_debt = float(row[key])
                        except (ValueError, TypeError):
                            pass

                if fips and med_debt is not None and len(fips) == 5:
                    result[fips] = round(med_debt, 1)

            if result:
                print(f"  Medical debt data for {len(result)} counties")
                return result
            else:
                print(f"  Could not parse medical debt from this file")

        except (URLError, HTTPError) as e:
            print(f"  Failed: {e}")
            continue
        except Exception as e:
            print(f"  Error: {e}")
            continue

    print("  SKIP: Could not download Urban Institute data (Cloudflare or URL changed)")
    print("  NOTE: To add this data manually, visit:")
    print("    https://datacatalog.urban.org/dataset/debt-america-2024")
    return {}


def merge_into_real_counties(walkability, medical_debt):
    """Load real_counties.json, add new fields, save back."""
    if not REAL_DATA_PATH.exists():
        print(f"ERROR: {REAL_DATA_PATH} not found")
        return False

    with open(REAL_DATA_PATH) as f:
        counties = json.load(f)

    walk_matched = 0
    debt_matched = 0

    for county in counties:
        fips = county.get("fips", "")

        if fips in walkability:
            county["walkability_score"] = walkability[fips]
            walk_matched += 1

        if fips in medical_debt:
            county["medical_debt_rate"] = medical_debt[fips]
            debt_matched += 1

    with open(REAL_DATA_PATH, "w") as f:
        json.dump(counties, f, indent=2)

    print(f"\nMerge results:")
    print(f"  Total counties: {len(counties)}")
    print(f"  Walkability matched: {walk_matched}")
    print(f"  Medical debt matched: {debt_matched}")
    return True


if __name__ == "__main__":
    walkability = fetch_epa_walkability()
    medical_debt = fetch_urban_medical_debt()

    if walkability or medical_debt:
        merge_into_real_counties(walkability, medical_debt)
    else:
        print("\nNo new data fetched. Exiting.")
        sys.exit(1)
