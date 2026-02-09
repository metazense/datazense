"""
Load Synthea CSV data into the PostgreSQL healthcare database.

Handles column renaming (Synthea uses UPPERCASE → our snake_case)
and respects foreign key load order.
"""

import csv
import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(__file__).parent.parent / "data" / "healthcare"

# Connection settings
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5433")),
    "database": "healthcare",
    "user": os.getenv("POSTGRES_USER", "taxi_user"),
    "password": os.getenv("POSTGRES_PASSWORD", "taxi_password"),
}

# Synthea CSV column → database column mapping
# Synthea uses UPPERCASE column names; we map to our snake_case schema.
COLUMN_MAPS = {
    "organizations": {
        "Id": "id",
        "NAME": "name",
        "ADDRESS": "address",
        "CITY": "city",
        "STATE": "state",
        "ZIP": "zip",
        "PHONE": "phone",
        "REVENUE": "revenue",
        "UTILIZATION": "utilization",
    },
    "payers": {
        "Id": "id",
        "NAME": "name",
        "AMOUNT_COVERED": "amount_covered",
        "AMOUNT_UNCOVERED": "amount_uncovered",
        "REVENUE": "revenue",
        "COVERED_ENCOUNTERS": "covered_encounters",
        "UNCOVERED_ENCOUNTERS": "uncovered_encounters",
        "COVERED_MEDICATIONS": "covered_medications",
        "UNCOVERED_MEDICATIONS": "uncovered_medications",
        "COVERED_PROCEDURES": "covered_procedures",
        "UNCOVERED_PROCEDURES": "uncovered_procedures",
        "COVERED_IMMUNIZATIONS": "covered_immunizations",
        "UNCOVERED_IMMUNIZATIONS": "uncovered_immunizations",
        "UNIQUE_CUSTOMERS": "unique_customers",
        "QOLS_AVG": "qols_avg",
        "MEMBER_MONTHS": "member_months",
    },
    "patients": {
        "Id": "id",
        "BIRTHDATE": "birth_date",
        "DEATHDATE": "death_date",
        "SSN": "ssn",
        "DRIVERS": "drivers",
        "PASSPORT": "passport",
        "PREFIX": "prefix",
        "FIRST": "first_name",
        "LAST": "last_name",
        "SUFFIX": "suffix",
        "MAIDEN": "maiden",
        "MARITAL": "marital",
        "RACE": "race",
        "ETHNICITY": "ethnicity",
        "GENDER": "gender",
        "BIRTHPLACE": "birthplace",
        "ADDRESS": "address",
        "CITY": "city",
        "STATE": "state",
        "COUNTY": "county",
        "FIPS": "fips",
        "ZIP": "zip",
        "LAT": "lat",
        "LON": "lon",
        "HEALTHCARE_EXPENSES": "healthcare_expenses",
        "HEALTHCARE_COVERAGE": "healthcare_coverage",
        "INCOME": "income",
    },
    "providers": {
        "Id": "id",
        "ORGANIZATION": "organization_id",
        "NAME": "name",
        "GENDER": "gender",
        "SPECIALITY": "speciality",
        "ADDRESS": "address",
        "CITY": "city",
        "STATE": "state",
        "ZIP": "zip",
        "LAT": "lat",
        "LON": "lon",
        "ENCOUNTERS": "encounters",
        "PROCEDURES": "procedures",
    },
    "encounters": {
        "Id": "id",
        "START": "start_time",
        "STOP": "stop_time",
        "PATIENT": "patient_id",
        "ORGANIZATION": "organization_id",
        "PROVIDER": "provider_id",
        "PAYER": "payer_id",
        "ENCOUNTERCLASS": "encounter_class",
        "CODE": "code",
        "DESCRIPTION": "description",
        "BASE_ENCOUNTER_COST": "base_encounter_cost",
        "TOTAL_CLAIM_COST": "total_claim_cost",
        "PAYER_COVERAGE": "payer_coverage",
        "REASONCODE": "reason_code",
        "REASONDESCRIPTION": "reason_description",
    },
    "conditions": {
        "START": "start_date",
        "STOP": "stop_date",
        "PATIENT": "patient_id",
        "ENCOUNTER": "encounter_id",
        "CODE": "code",
        "DESCRIPTION": "description",
    },
    "medications": {
        "START": "start_date",
        "STOP": "stop_date",
        "PATIENT": "patient_id",
        "PAYER": "payer_id",
        "ENCOUNTER": "encounter_id",
        "CODE": "code",
        "DESCRIPTION": "description",
        "BASE_COST": "base_cost",
        "PAYER_COVERAGE": "payer_coverage",
        "DISPENSES": "dispenses",
        "TOTALCOST": "total_cost",
        "REASONCODE": "reason_code",
        "REASONDESCRIPTION": "reason_description",
    },
    "procedures": {
        "START": "start_time",
        "STOP": "stop_time",
        "PATIENT": "patient_id",
        "ENCOUNTER": "encounter_id",
        "CODE": "code",
        "DESCRIPTION": "description",
        "BASE_COST": "base_cost",
        "REASONCODE": "reason_code",
        "REASONDESCRIPTION": "reason_description",
    },
}

# Load order respects foreign key constraints
LOAD_ORDER = [
    "organizations",
    "payers",
    "patients",
    "providers",
    "encounters",
    "conditions",
    "medications",
    "procedures",
]


def load_table(conn, table_name: str, csv_path: Path) -> int:
    """Load a CSV file into a table with column mapping."""
    column_map = COLUMN_MAPS[table_name]

    # Read CSV header
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        csv_headers = next(reader)

    # Find columns that exist in both CSV and our mapping
    mapped_cols = []
    csv_indices = []
    for i, header in enumerate(csv_headers):
        if header in column_map:
            mapped_cols.append(column_map[header])
            csv_indices.append(i)

    if not mapped_cols:
        print(f"  WARNING: No matching columns for {table_name}")
        print(f"  CSV headers: {csv_headers[:10]}")
        return 0

    # Build INSERT statement
    placeholders = ", ".join(["%s"] * len(mapped_cols))
    col_names = ", ".join(mapped_cols)
    insert_sql = f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"

    # Load data
    cur = conn.cursor()
    row_count = 0
    batch = []
    batch_size = 1000

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # skip header

        for row in reader:
            values = []
            for idx in csv_indices:
                val = row[idx] if idx < len(row) else ""
                # Convert empty strings to None
                if val == "" or val == "None":
                    val = None
                values.append(val)

            batch.append(tuple(values))
            row_count += 1

            if len(batch) >= batch_size:
                cur.executemany(insert_sql, batch)
                conn.commit()
                batch = []

    # Insert remaining
    if batch:
        cur.executemany(insert_sql, batch)
        conn.commit()

    cur.close()
    return row_count


def main():
    print("=" * 70)
    print("HEALTHCARE DATA LOADER")
    print("=" * 70)

    # Check data directory
    if not DATA_DIR.exists():
        print(f"\nData directory not found: {DATA_DIR}")
        print("Run download_healthcare_data.py first.")
        sys.exit(1)

    # Check which files are available
    available = {f.stem: f for f in DATA_DIR.glob("*.csv")}
    print(f"\nFound {len(available)} CSV files in {DATA_DIR}")

    # Connect to database
    print(f"\nConnecting to PostgreSQL: {DB_CONFIG['host']}:{DB_CONFIG['port']}/healthcare")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        print("Connected!")
    except Exception as e:
        print(f"Connection failed: {e}")
        print("\nMake sure:")
        print("  1. Docker containers are running: docker compose up -d")
        print("  2. Healthcare database exists (created by 02-healthcare-schema.sql)")
        sys.exit(1)

    # Load tables in FK order
    total_rows = 0
    for table_name in LOAD_ORDER:
        csv_path = available.get(table_name)
        if csv_path is None:
            print(f"\n  SKIP: {table_name}.csv not found")
            continue

        print(f"\nLoading {table_name}...")

        # Check if table already has data
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM {table_name}")
        existing = cur.fetchone()[0]
        cur.close()

        if existing > 0:
            print(f"  Table already has {existing:,} rows. Skipping.")
            total_rows += existing
            continue

        try:
            rows = load_table(conn, table_name, csv_path)
            print(f"  Loaded {rows:,} rows")
            total_rows += rows
        except Exception as e:
            print(f"  ERROR loading {table_name}: {e}")
            conn.rollback()
            continue

    conn.close()

    # Summary
    print(f"\n" + "=" * 70)
    print("LOAD COMPLETE")
    print("=" * 70)
    print(f"\nTotal rows loaded: {total_rows:,}")
    print(f"\nVerify with:")
    print(f"  psql -h localhost -p 5433 -U taxi_user -d healthcare")
    print(f"  SELECT COUNT(*) FROM encounters;")
    print(f"  SELECT COUNT(*) FROM patients;")
    print(f"  SELECT encounter_class, COUNT(*) FROM encounters GROUP BY encounter_class;")


if __name__ == "__main__":
    main()
