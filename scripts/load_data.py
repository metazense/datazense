"""
Load NYC Taxi data into PostgreSQL.

This script loads:
1. Taxi zone lookup data
2. Yellow taxi trip data (January 2024)
"""

import pandas as pd
from sqlalchemy import create_engine, text
from pathlib import Path
import sys

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Database connection (port 5433 to avoid conflict with local PostgreSQL)
DB_URL = "postgresql://taxi_user:taxi_password@127.0.0.1:5433/nyc_taxi"


def load_zones(engine):
    """Load taxi zone lookup data."""
    print("Loading taxi zones...")

    zones_file = DATA_DIR / "taxi_zone_lookup.csv"
    if not zones_file.exists():
        print(f"  ERROR: {zones_file} not found. Run download_data.py first.")
        return False

    df = pd.read_csv(zones_file)

    # Rename columns to match schema
    df = df.rename(columns={
        'LocationID': 'location_id',
        'Borough': 'borough',
        'Zone': 'zone_name',
        'service_zone': 'service_zone'
    })

    # Clear existing data and load (table already created by init script)
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE zones CASCADE"))
        conn.commit()

    # Load into existing table
    df.to_sql('zones', engine, if_exists='append', index=False)

    print(f"  Loaded {len(df)} zones")
    return True


def load_trips(engine, batch_size: int = 50000):
    """Load trip data in batches."""
    print("Loading trip data...")

    trips_file = DATA_DIR / "yellow_tripdata_2024-01.parquet"
    if not trips_file.exists():
        print(f"  ERROR: {trips_file} not found. Run download_data.py first.")
        return False

    # Read parquet file
    print("  Reading parquet file...")
    df = pd.read_parquet(trips_file)
    print(f"  Total records: {len(df):,}")

    # Rename columns to match our schema
    column_mapping = {
        'VendorID': 'vendor_id',
        'tpep_pickup_datetime': 'pickup_datetime',
        'tpep_dropoff_datetime': 'dropoff_datetime',
        'passenger_count': 'passenger_count',
        'trip_distance': 'trip_distance',
        'PULocationID': 'pickup_location_id',
        'DOLocationID': 'dropoff_location_id',
        'RatecodeID': 'rate_code_id',
        'store_and_fwd_flag': 'store_and_fwd_flag',
        'payment_type': 'payment_type',
        'fare_amount': 'fare_amount',
        'extra': 'extra',
        'mta_tax': 'mta_tax',
        'tip_amount': 'tip_amount',
        'tolls_amount': 'tolls_amount',
        'improvement_surcharge': 'improvement_surcharge',
        'total_amount': 'total_amount',
        'congestion_surcharge': 'congestion_surcharge',
        'Airport_fee': 'airport_fee'
    }

    df = df.rename(columns=column_mapping)

    # Select only columns we need
    columns = [
        'vendor_id', 'pickup_datetime', 'dropoff_datetime', 'passenger_count',
        'trip_distance', 'pickup_location_id', 'dropoff_location_id', 'rate_code_id',
        'store_and_fwd_flag', 'payment_type', 'fare_amount', 'extra', 'mta_tax',
        'tip_amount', 'tolls_amount', 'improvement_surcharge', 'total_amount',
        'congestion_surcharge', 'airport_fee'
    ]

    df = df[[col for col in columns if col in df.columns]]

    # Clean data - handle invalid foreign keys
    print("  Cleaning data...")

    # Filter out invalid location IDs (zones are 1-265)
    df = df[df['pickup_location_id'].between(1, 265, inclusive='both')]
    df = df[df['dropoff_location_id'].between(1, 265, inclusive='both')]

    # Filter out invalid payment types (1-6)
    df = df[df['payment_type'].between(1, 6, inclusive='both')]

    # Filter out invalid rate codes (1-6)
    if 'rate_code_id' in df.columns:
        df = df[df['rate_code_id'].between(1, 6, inclusive='both') | df['rate_code_id'].isna()]

    # Filter out unreasonable values
    df = df[df['fare_amount'] >= 0]
    df = df[df['total_amount'] >= 0]
    df = df[df['trip_distance'] >= 0]

    print(f"  Records after cleaning: {len(df):,}")

    # Clear existing data
    print("  Clearing existing trip data...")
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE trips RESTART IDENTITY"))
        conn.commit()

    # Load in batches
    total_batches = (len(df) + batch_size - 1) // batch_size
    print(f"  Loading in {total_batches} batches...")

    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size]
        batch_num = i // batch_size + 1

        batch.to_sql(
            'trips',
            engine,
            if_exists='append',
            index=False,
            method='multi'
        )

        print(f"    Batch {batch_num}/{total_batches} loaded ({len(batch):,} records)")

    print(f"  Total trips loaded: {len(df):,}")
    return True


def verify_data(engine):
    """Verify data was loaded correctly."""
    print("\nVerifying data...")

    with engine.connect() as conn:
        # Check zones
        result = conn.execute(text("SELECT COUNT(*) FROM zones"))
        zone_count = result.scalar()
        print(f"  Zones: {zone_count}")

        # Check trips
        result = conn.execute(text("SELECT COUNT(*) FROM trips"))
        trip_count = result.scalar()
        print(f"  Trips: {trip_count:,}")

        # Sample query - revenue by borough
        print("\n  Sample: Revenue by Borough (Top 5)")
        query = """
            SELECT
                z.borough,
                COUNT(*) as trip_count,
                ROUND(SUM(t.fare_amount + t.tip_amount)::numeric, 2) as total_revenue
            FROM trips t
            JOIN zones z ON t.pickup_location_id = z.location_id
            GROUP BY z.borough
            ORDER BY total_revenue DESC
            LIMIT 5
        """
        result = conn.execute(text(query))
        for row in result:
            print(f"    {row[0]}: {row[1]:,} trips, ${row[2]:,.2f} revenue")

    return True


def main():
    print("=" * 60)
    print("NYC Taxi Data Loader")
    print("=" * 60)

    # Create database connection
    print(f"\nConnecting to: {DB_URL}")
    try:
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("  Connected successfully!")
    except Exception as e:
        print(f"  ERROR: Could not connect to database: {e}")
        print("\n  Make sure PostgreSQL is running:")
        print("    docker-compose up -d")
        sys.exit(1)

    print()

    # Load data
    if not load_zones(engine):
        sys.exit(1)

    if not load_trips(engine):
        sys.exit(1)

    # Verify
    verify_data(engine)

    print("\n" + "=" * 60)
    print("Data loading complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
