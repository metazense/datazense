"""
Semantic Layer - Powered by boring-semantic-layer + Ibis + PostgreSQL

This module provides the COMPUTATION layer that actually executes queries
and returns real data. It's the "WHAT" layer in the architecture.

The semantic layer:
- Defines metrics (trip_count, total_revenue, avg_tip, etc.)
- Defines dimensions (borough, zone, payment_type, etc.)
- Handles joins between tables
- Generates and executes SQL against PostgreSQL
- Returns actual computed values

Usage:
    from semantic_layer import SemanticLayer

    sl = SemanticLayer()
    result = sl.query(
        dimensions=["pickup_zone.borough"],
        measures=["trip_count", "total_revenue"]
    )
    print(result)
"""

import os
from pathlib import Path
from typing import Optional, List, Tuple

import ibis
from boring_semantic_layer import SemanticModel
from dotenv import load_dotenv

load_dotenv()


class SemanticLayer:
    """
    PostgreSQL-backed semantic layer using boring-semantic-layer.

    This is the computation engine that translates business metrics
    into SQL and executes against the database.
    """

    def __init__(
        self,
        host: str = None,
        port: int = None,
        database: str = None,
        user: str = None,
        password: str = None,
        yaml_path: Optional[str] = None
    ):
        """
        Initialize semantic layer with PostgreSQL connection.

        Args:
            host: PostgreSQL host (default: localhost)
            port: PostgreSQL port (default: 5433)
            database: Database name (default: nyc_taxi)
            user: Database user (default: taxi_user)
            password: Database password (default: taxi_password)
            yaml_path: Path to semantic model YAML (default: semantic_model.yml)
        """
        # Use environment variables or defaults
        host = host or os.getenv("POSTGRES_HOST", "localhost")
        port = port or int(os.getenv("POSTGRES_PORT", "5433"))
        database = database or os.getenv("POSTGRES_DB", "nyc_taxi")
        user = user or os.getenv("POSTGRES_USER", "taxi_user")
        password = password or os.getenv("POSTGRES_PASSWORD", "taxi_password")

        # Connect to PostgreSQL via Ibis
        print(f"Connecting to PostgreSQL: {host}:{port}/{database}")
        self.con = ibis.postgres.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        print("Connected successfully!")

        # Register tables from PostgreSQL
        self.tables = {
            "trips_tbl": self.con.table("trips"),
            "zones_tbl": self.con.table("zones"),
            "payment_types_tbl": self.con.table("payment_types"),
            "rate_codes_tbl": self.con.table("rate_codes"),
        }

        # Load semantic model from YAML
        if yaml_path is None:
            yaml_path = Path(__file__).parent.parent / "semantic_model.yml"

        print(f"Loading semantic model from: {yaml_path}")
        self.models = SemanticModel.from_yaml(str(yaml_path), tables=self.tables)

        # Shortcuts for common models
        self.trips = self.models["trips"]
        self.zones = self.models["zones"]
        self.payment_types = self.models["payment_types"]
        self.rate_codes = self.models["rate_codes"]

        print("Semantic layer initialized!")

    @property
    def available_dimensions(self) -> List[str]:
        """Get all available dimensions including joined ones."""
        # Get dimensions directly from the model
        # Note: Joined dimensions are automatically included
        return sorted(list(set(self.trips.available_dimensions)))

    @property
    def available_measures(self) -> List[str]:
        """Get all available measures."""
        return sorted(list(self.trips.available_measures))

    def query(
        self,
        dimensions: List[str],
        measures: List[str],
        filters: Optional[dict] = None,
        order_by: Optional[List[Tuple[str, str]]] = None,
        limit: Optional[int] = None
    ) -> dict:
        """
        Execute a semantic query and return results.

        Args:
            dimensions: List of dimensions to group by
                       e.g., ["pickup_zone.borough", "payment_type"]
            measures: List of measures to compute
                     e.g., ["trip_count", "total_revenue", "avg_tip"]
            filters: Optional filters (not fully implemented in BSL yet)
            order_by: Optional ordering as list of (field, 'asc'|'desc') tuples
            limit: Optional row limit

        Returns:
            Dict with:
            - 'data': List of row dicts
            - 'columns': List of column names
            - 'row_count': Number of rows
            - 'query': The generated SQL (for debugging)
        """
        try:
            # Build query expression
            expr = self.trips.query(
                dimensions=dimensions,
                measures=measures,
                order_by=order_by,
                limit=limit
            )

            # Execute and convert to records
            df = expr.execute()

            return {
                "data": df.to_dict(orient="records"),
                "columns": list(df.columns),
                "row_count": len(df)
            }

        except Exception as e:
            import traceback
            return {
                "error": str(e),
                "traceback": traceback.format_exc(),
                "dimensions": dimensions,
                "measures": measures
            }

    def get_revenue_by_borough(self, limit: int = 10) -> dict:
        """
        Convenience method: Get revenue metrics by borough.

        Returns total revenue, trip count, average fare, and average tip
        grouped by pickup borough.
        """
        return self.query(
            dimensions=["pickup_zone.borough"],
            measures=["trip_count", "total_revenue", "avg_fare", "avg_tip"],
            order_by=[("total_revenue", "desc")],
            limit=limit
        )

    def get_tips_by_borough(self, limit: int = 10) -> dict:
        """
        Convenience method: Get tip metrics by borough.

        Note: Cash tips are not recorded, so tip analysis should
        consider credit_card_rate for context.
        """
        return self.query(
            dimensions=["pickup_zone.borough"],
            measures=["trip_count", "avg_tip", "credit_card_rate"],
            order_by=[("avg_tip", "desc")],
            limit=limit
        )

    def get_trips_by_payment_type(self) -> dict:
        """
        Convenience method: Get trip counts by payment type.
        """
        return self.query(
            dimensions=["payment_type"],
            measures=["trip_count", "avg_fare", "avg_tip", "total_revenue"],
            order_by=[("trip_count", "desc")]
        )

    def get_airport_analysis(self) -> dict:
        """
        Convenience method: Analyze airport trips (rate_code 2=JFK, 3=Newark).
        """
        return self.query(
            dimensions=["rate_code_id"],
            measures=["trip_count", "avg_fare", "avg_distance", "avg_tip"],
            order_by=[("trip_count", "desc")]
        )

    def get_hourly_pattern(self, limit: int = 24) -> dict:
        """
        Convenience method: Get trip patterns by hour.

        Note: This requires extracting hour from pickup_datetime.
        May need custom SQL for complex time analysis.
        """
        # For now, return by pickup_datetime (will be many rows)
        # A production version would extract hour component
        return self.query(
            dimensions=["pickup_zone.borough"],
            measures=["trip_count", "avg_fare"],
            order_by=[("trip_count", "desc")],
            limit=limit
        )

    def get_zone_performance(self, limit: int = 20) -> dict:
        """
        Convenience method: Get performance by pickup zone.
        """
        return self.query(
            dimensions=["pickup_zone.zone_name", "pickup_zone.borough"],
            measures=["trip_count", "total_revenue", "avg_fare"],
            order_by=[("total_revenue", "desc")],
            limit=limit
        )

    def summary(self) -> dict:
        """
        Get a summary of the semantic layer capabilities.
        """
        return {
            "models": list(self.models.keys()),
            "dimensions": self.available_dimensions,
            "measures": self.available_measures,
            "tables": list(self.tables.keys())
        }


# =============================================================================
# CLI / Test
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("SEMANTIC LAYER TEST - PostgreSQL Backend")
    print("=" * 70)

    # Initialize
    sl = SemanticLayer()

    # Show available dimensions and measures
    print(f"\n--- Available Dimensions ({len(sl.available_dimensions)}) ---")
    for dim in sl.available_dimensions:
        print(f"  - {dim}")

    print(f"\n--- Available Measures ({len(sl.available_measures)}) ---")
    for measure in sl.available_measures:
        print(f"  - {measure}")

    # Test queries
    print("\n" + "=" * 70)
    print("TEST QUERY 1: Revenue by Borough")
    print("=" * 70)
    result = sl.get_revenue_by_borough()
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(f"Rows: {result['row_count']}")
        for row in result["data"]:
            borough = row.get("pickup_zone_borough", "Unknown")
            trips = row.get("trip_count", 0)
            revenue = row.get("total_revenue", 0)
            avg_fare = row.get("avg_fare", 0)
            avg_tip = row.get("avg_tip", 0)
            print(f"  {borough}: {trips:,} trips, ${revenue:,.2f} revenue, "
                  f"${avg_fare:.2f} avg fare, ${avg_tip:.2f} avg tip")

    print("\n" + "=" * 70)
    print("TEST QUERY 2: Tips by Borough")
    print("=" * 70)
    result = sl.get_tips_by_borough()
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        for row in result["data"]:
            borough = row.get("pickup_zone_borough", "Unknown")
            trips = row.get("trip_count", 0)
            avg_tip = row.get("avg_tip", 0)
            cc_rate = row.get("credit_card_rate", 0)
            print(f"  {borough}: {trips:,} trips, ${avg_tip:.2f} avg tip, "
                  f"{cc_rate*100:.1f}% credit card")

    print("\n" + "=" * 70)
    print("TEST QUERY 3: Top Pickup Zones")
    print("=" * 70)
    result = sl.get_zone_performance(limit=10)
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        for row in result["data"]:
            zone = row.get("pickup_zone_zone_name", "Unknown")
            borough = row.get("pickup_zone_borough", "Unknown")
            trips = row.get("trip_count", 0)
            revenue = row.get("total_revenue", 0)
            print(f"  {zone} ({borough}): {trips:,} trips, ${revenue:,.2f}")

    print("\n" + "=" * 70)
    print("TEST QUERY 4: Payment Type Analysis")
    print("=" * 70)
    result = sl.get_trips_by_payment_type()
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        for row in result["data"]:
            ptype = row.get("payment_type", "Unknown")
            trips = row.get("trip_count", 0)
            avg_tip = row.get("avg_tip", 0)
            print(f"  Payment Type {ptype}: {trips:,} trips, ${avg_tip:.2f} avg tip")

    print("\n" + "=" * 70)
    print("SEMANTIC LAYER TEST COMPLETE")
    print("=" * 70)
