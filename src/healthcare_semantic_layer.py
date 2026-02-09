"""
Healthcare Semantic Layer - Powered by boring-semantic-layer + Ibis + PostgreSQL

This module provides the COMPUTATION layer for healthcare data.
Same pattern as SemanticLayer but connects to the healthcare database
and operates on Synthea patient/encounter/condition data.

Usage:
    from healthcare_semantic_layer import HealthcareSemanticLayer

    sl = HealthcareSemanticLayer()
    result = sl.query(
        model_name="encounters",
        dimensions=["encounter_class"],
        measures=["encounter_count", "total_claim_cost"]
    )
"""

import os
from pathlib import Path
from typing import Optional, List, Tuple

import ibis
from boring_semantic_layer import SemanticModel
from dotenv import load_dotenv

load_dotenv()


class HealthcareSemanticLayer:
    """
    PostgreSQL-backed semantic layer for healthcare data.

    Connects to the 'healthcare' database (same container, port 5433).
    """

    def __init__(
        self,
        host: str = None,
        port: int = None,
        database: str = None,
        user: str = None,
        password: str = None,
        yaml_path: Optional[str] = None,
    ):
        host = host or os.getenv("POSTGRES_HOST", "localhost")
        port = port or int(os.getenv("POSTGRES_PORT", "5433"))
        database = database or "healthcare"
        user = user or os.getenv("POSTGRES_USER", "taxi_user")
        password = password or os.getenv("POSTGRES_PASSWORD", "taxi_password")

        print(f"Connecting to PostgreSQL: {host}:{port}/{database}")
        self.con = ibis.postgres.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
        )
        print("Connected successfully!")

        # Register tables with _tbl suffix (BSL convention)
        self.tables = {
            "encounters_tbl": self.con.table("encounters"),
            "patients_tbl": self.con.table("patients"),
            "conditions_tbl": self.con.table("conditions"),
            "medications_tbl": self.con.table("medications"),
            "organizations_tbl": self.con.table("organizations"),
            "payers_tbl": self.con.table("payers"),
        }

        # Load semantic model
        if yaml_path is None:
            yaml_path = Path(__file__).parent.parent / "semantic_model_healthcare.yml"

        print(f"Loading semantic model from: {yaml_path}")
        self.models = SemanticModel.from_yaml(str(yaml_path), tables=self.tables)

        # Shortcuts
        self.encounters = self.models["encounters"]
        self.conditions = self.models["conditions"]
        self.medications = self.models["medications"]
        self.patients = self.models["patients"]

        print("Healthcare semantic layer initialized!")

    @property
    def available_dimensions(self) -> List[str]:
        return sorted(list(set(self.encounters.available_dimensions)))

    @property
    def available_measures(self) -> List[str]:
        return sorted(list(self.encounters.available_measures))

    def query(
        self,
        dimensions: List[str],
        measures: List[str],
        model_name: str = "encounters",
        order_by: Optional[List[Tuple[str, str]]] = None,
        limit: Optional[int] = None,
    ) -> dict:
        """Execute a semantic query against the specified model."""
        try:
            model = self.models[model_name]
            expr = model.query(
                dimensions=dimensions,
                measures=measures,
                order_by=order_by,
                limit=limit,
            )
            df = expr.execute()
            return {
                "data": df.to_dict(orient="records"),
                "columns": list(df.columns),
                "row_count": len(df),
            }
        except Exception as e:
            import traceback
            return {
                "error": str(e),
                "traceback": traceback.format_exc(),
                "model": model_name,
                "dimensions": dimensions,
                "measures": measures,
            }

    def get_cost_by_encounter_class(self, limit: int = 10) -> dict:
        """Cost metrics grouped by encounter type."""
        return self.query(
            dimensions=["encounter_class"],
            measures=["encounter_count", "total_claim_cost", "avg_claim_cost", "avg_payer_coverage"],
            order_by=[("total_claim_cost", "desc")],
            limit=limit,
        )

    def get_top_conditions(self, limit: int = 20) -> dict:
        """Most common conditions."""
        return self.query(
            model_name="conditions",
            dimensions=["description"],
            measures=["condition_count"],
            order_by=[("condition_count", "desc")],
            limit=limit,
        )

    def get_cost_by_demographics(self, dimension: str = "patient.gender", limit: int = 10) -> dict:
        """Cost metrics by patient demographics."""
        return self.query(
            dimensions=[dimension],
            measures=["encounter_count", "total_claim_cost", "avg_claim_cost"],
            order_by=[("total_claim_cost", "desc")],
            limit=limit,
        )

    def get_medication_costs(self, limit: int = 20) -> dict:
        """Top medications by cost."""
        return self.query(
            model_name="medications",
            dimensions=["description"],
            measures=["medication_count", "total_medication_cost", "avg_medication_cost"],
            order_by=[("total_medication_cost", "desc")],
            limit=limit,
        )

    def summary(self) -> dict:
        return {
            "models": list(self.models.keys()),
            "encounter_dimensions": sorted(list(set(self.encounters.available_dimensions))),
            "encounter_measures": sorted(list(self.encounters.available_measures)),
            "condition_dimensions": sorted(list(set(self.conditions.available_dimensions))),
            "condition_measures": sorted(list(self.conditions.available_measures)),
            "medication_dimensions": sorted(list(set(self.medications.available_dimensions))),
            "medication_measures": sorted(list(self.medications.available_measures)),
        }


# =============================================================================
# CLI / Test
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("HEALTHCARE SEMANTIC LAYER TEST")
    print("=" * 70)

    sl = HealthcareSemanticLayer()

    # Show summary
    summary = sl.summary()
    print(f"\nModels: {summary['models']}")
    print(f"\nEncounter Dimensions ({len(summary['encounter_dimensions'])}):")
    for d in summary["encounter_dimensions"]:
        print(f"  - {d}")
    print(f"\nEncounter Measures ({len(summary['encounter_measures'])}):")
    for m in summary["encounter_measures"]:
        print(f"  - {m}")

    # Test queries
    print("\n" + "=" * 70)
    print("TEST 1: Cost by Encounter Class")
    print("=" * 70)
    result = sl.get_cost_by_encounter_class()
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        for row in result["data"]:
            ec = row.get("encounter_class", "?")
            count = row.get("encounter_count", 0)
            cost = row.get("total_claim_cost", 0)
            avg = row.get("avg_claim_cost", 0)
            print(f"  {ec}: {count:,} encounters, ${cost:,.2f} total, ${avg:,.2f} avg")

    print("\n" + "=" * 70)
    print("TEST 2: Top 10 Conditions")
    print("=" * 70)
    result = sl.get_top_conditions(limit=10)
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        for row in result["data"]:
            desc = row.get("description", "?")
            count = row.get("condition_count", 0)
            print(f"  {desc}: {count:,}")

    print("\n" + "=" * 70)
    print("TEST 3: Cost by Gender")
    print("=" * 70)
    result = sl.get_cost_by_demographics("patient.gender")
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        for row in result["data"]:
            gender = row.get("patient_gender", "?")
            count = row.get("encounter_count", 0)
            cost = row.get("total_claim_cost", 0)
            print(f"  {gender}: {count:,} encounters, ${cost:,.2f}")

    print("\n" + "=" * 70)
    print("HEALTHCARE SEMANTIC LAYER TEST COMPLETE")
    print("=" * 70)
