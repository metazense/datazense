"""
Unified Intelligence Layer - Combines Technical, Semantic, and Ontology layers.

This module demonstrates how the 3 layers work together:
1. Technical Layer (OpenMetadata) - What data EXISTS (tables, columns, types)
2. Semantic Layer (boring-semantic-layer) - What data MEANS and HOW to compute it
3. Ontology Layer (OWL/RDF) - How concepts RELATE and business RULES

Architecture:
    User Question
         ↓
    ┌─────────────────────────────────────────────────────┐
    │            Unified Intelligence Layer               │
    │  ┌─────────────┬──────────────┬──────────────────┐  │
    │  │  Technical  │   Semantic   │     Ontology     │  │
    │  │ (OpenMeta)  │   (Ibis/PG)  │    (OWL/RDF)     │  │
    │  │             │              │                  │  │
    │  │ - Tables    │ - Metrics    │ - Concepts       │  │
    │  │ - Columns   │ - Dimensions │ - Relationships  │  │
    │  │ - Types     │ - Queries    │ - Rules          │  │
    │  └─────────────┴──────────────┴──────────────────┘  │
    │                        ↓                            │
    │              PostgreSQL (2.76M trips)               │
    └─────────────────────────────────────────────────────┘
         ↓
    Computed Answer with Context
"""

import requests
import base64
from typing import Optional, Dict, List, Any

from ontology_layer import OntologyLayer


class TechnicalLayer:
    """
    Interface to OpenMetadata for technical metadata.

    This layer answers: "What data exists?"
    - Table structures
    - Column definitions
    - Data types
    - Lineage information
    """

    def __init__(self, base_url: str = "http://localhost:8585/api/v1"):
        self.base_url = base_url
        self.headers = None
        self._authenticated = False
        self._try_authenticate()

    def _try_authenticate(self):
        """Try to authenticate with OpenMetadata."""
        try:
            password_b64 = base64.b64encode("admin".encode()).decode()
            payload = {"email": "admin@open-metadata.org", "password": password_b64}
            response = requests.post(
                f"{self.base_url}/users/login",
                json=payload,
                timeout=5
            )
            if response.status_code == 200:
                token = response.json().get("accessToken")
                self.headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}"
                }
                self._authenticated = True
        except Exception:
            self._authenticated = False

    @property
    def is_available(self) -> bool:
        return self._authenticated

    def get_table(self, table_fqn: str) -> dict:
        """Get table metadata including columns."""
        if not self._authenticated:
            return {}
        url = f"{self.base_url}/tables/name/{table_fqn}"
        response = requests.get(url, headers=self.headers, params={"fields": "columns"})
        if response.status_code == 200:
            return response.json()
        return {}

    def get_column_info(self, table_fqn: str, column_name: str) -> dict:
        """Get specific column metadata."""
        table = self.get_table(table_fqn)
        for col in table.get("columns", []):
            if col.get("name") == column_name:
                return col
        return {}

    def get_all_tables(self) -> list[dict]:
        """Get all tables in the NYC Taxi database."""
        if not self._authenticated:
            return []
        url = f"{self.base_url}/tables"
        response = requests.get(url, headers=self.headers, params={"limit": 100})
        if response.status_code == 200:
            return response.json().get("data", [])
        return []

    def get_glossary_terms(self) -> list[dict]:
        """Get all glossary terms from OpenMetadata."""
        if not self._authenticated:
            return []
        try:
            # Get glossary
            glossary_url = f"{self.base_url}/glossaries/name/NYCTaxiBusinessGlossary"
            response = requests.get(glossary_url, headers=self.headers)
            if response.status_code != 200:
                return []
            glossary_id = response.json().get("id")

            # Get terms
            url = f"{self.base_url}/glossaryTerms"
            response = requests.get(url, headers=self.headers, params={"glossary": glossary_id, "limit": 100})
            if response.status_code == 200:
                return response.json().get("data", [])
        except Exception:
            pass
        return []


class ComputationLayer:
    """
    Computation layer using boring-semantic-layer + PostgreSQL.

    This layer answers: "What does the data MEAN and how do we COMPUTE it?"
    - Metric definitions (how to calculate)
    - Dimension definitions (how to group)
    - Query execution (actual computation)
    """

    def __init__(self):
        self._semantic_layer = None
        self._available = False
        self._try_init()

    def _try_init(self):
        """Try to initialize the semantic layer."""
        try:
            from semantic_layer import SemanticLayer
            self._semantic_layer = SemanticLayer()
            self._available = True
        except Exception as e:
            print(f"Warning: Could not initialize computation layer: {e}")
            self._available = False

    @property
    def is_available(self) -> bool:
        return self._available

    @property
    def available_dimensions(self) -> List[str]:
        if not self._available:
            return []
        return self._semantic_layer.available_dimensions

    @property
    def available_measures(self) -> List[str]:
        if not self._available:
            return []
        return self._semantic_layer.available_measures

    def query(
        self,
        dimensions: List[str],
        measures: List[str],
        order_by: Optional[List[tuple]] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute a semantic query."""
        if not self._available:
            return {"error": "Computation layer not available"}
        return self._semantic_layer.query(
            dimensions=dimensions,
            measures=measures,
            order_by=order_by,
            limit=limit
        )

    def get_revenue_by_borough(self, limit: int = 10) -> Dict:
        if not self._available:
            return {"error": "Not available"}
        return self._semantic_layer.get_revenue_by_borough(limit)

    def get_tips_by_borough(self, limit: int = 10) -> Dict:
        if not self._available:
            return {"error": "Not available"}
        return self._semantic_layer.get_tips_by_borough(limit)

    def get_zone_performance(self, limit: int = 20) -> Dict:
        if not self._available:
            return {"error": "Not available"}
        return self._semantic_layer.get_zone_performance(limit)


class UnifiedIntelligenceLayer:
    """
    Combines all 3 layers to provide intelligent data access.

    This is the "Mini Fabric IQ" - combining:
    - Technical metadata (what exists)
    - Semantic computation (how to calculate)
    - Ontology reasoning (what it means)
    """

    def __init__(self):
        print("Initializing Unified Intelligence Layer...")

        # Layer 1: Technical (OpenMetadata)
        print("  - Technical Layer (OpenMetadata)...", end=" ")
        self.technical = TechnicalLayer()
        print("OK" if self.technical.is_available else "Not Available")

        # Layer 2: Computation (boring-semantic-layer + PostgreSQL)
        print("  - Computation Layer (Semantic)...", end=" ")
        self.computation = ComputationLayer()
        print("OK" if self.computation.is_available else "Not Available")

        # Layer 3: Ontology (OWL/RDF)
        print("  - Ontology Layer (OWL/RDF)...", end=" ")
        self.ontology = OntologyLayer()
        print("OK")

        print("Unified Intelligence Layer ready!")

    def understand_concept(self, concept: str) -> Dict[str, Any]:
        """
        Understand a business concept using all 3 layers.

        Returns combined knowledge:
        - Technical: What columns/tables exist
        - Semantic: How to calculate it
        - Ontology: Business context and rules
        """
        result = {
            "concept": concept,
            "technical": {},
            "semantic": {},
            "ontology": {}
        }

        # 1. Ontology - Business context
        context = self.ontology.get_concept_context(concept)
        if context:
            result["ontology"] = context

        # Also check trip types, zone types, time contexts
        for trip_type in self.ontology.get_trip_types():
            if concept.lower() in trip_type.get("label", "").lower():
                result["ontology"]["trip_type"] = trip_type
                break

        for zone_type in self.ontology.get_zone_types():
            if concept.lower() in zone_type.get("label", "").lower():
                result["ontology"]["zone_type"] = zone_type
                break

        # 2. Semantic - Computation info
        if self.computation.is_available:
            # Check if it's a measure
            if concept.lower().replace(" ", "_") in [m.lower() for m in self.computation.available_measures]:
                result["semantic"]["type"] = "measure"
                result["semantic"]["name"] = concept
                result["semantic"]["available"] = True

            # Check if it's a dimension
            for dim in self.computation.available_dimensions:
                if concept.lower() in dim.lower():
                    result["semantic"]["type"] = "dimension"
                    result["semantic"]["name"] = dim
                    result["semantic"]["available"] = True
                    break

        # 3. Technical - OpenMetadata info
        if self.technical.is_available:
            # Try to find matching glossary term
            terms = self.technical.get_glossary_terms()
            for term in terms:
                if concept.lower() in term.get("displayName", "").lower():
                    result["technical"]["glossary_term"] = {
                        "name": term.get("displayName"),
                        "description": term.get("description"),
                        "fqn": term.get("fullyQualifiedName")
                    }
                    break

        return result

    def answer_question(self, question: str) -> Dict[str, Any]:
        """
        Answer a business question using all 3 layers.

        1. Parse question to identify concepts
        2. Get computation context from ontology
        3. Execute query via semantic layer
        4. Enrich with business context
        """
        result = {
            "question": question,
            "identified_concepts": [],
            "computation": None,
            "context": [],
            "answer": None
        }

        question_lower = question.lower()

        # Identify what type of question
        is_revenue_question = any(w in question_lower for w in ["revenue", "money", "earn", "fare"])
        is_tip_question = any(w in question_lower for w in ["tip", "tips", "tipping"])
        is_zone_question = any(w in question_lower for w in ["zone", "area", "neighborhood"])
        is_borough_question = any(w in question_lower for w in ["borough", "manhattan", "brooklyn", "queens"])
        is_why_question = "why" in question_lower

        # Get relevant analysis context from ontology
        if is_tip_question:
            ctx = self.ontology.get_context_for_analysis("tips")
            result["context"] = ctx.get("business_insights", [])
            result["identified_concepts"].append("Tips Analysis")
        elif is_revenue_question:
            ctx = self.ontology.get_context_for_analysis("revenue")
            result["context"] = ctx.get("business_insights", [])
            result["identified_concepts"].append("Revenue Analysis")

        # Execute appropriate query
        if self.computation.is_available:
            if is_revenue_question and is_borough_question:
                data = self.computation.get_revenue_by_borough()
                result["computation"] = data
                result["identified_concepts"].append("Revenue by Borough")

                if not data.get("error"):
                    # Build answer
                    rows = data.get("data", [])
                    answer_parts = ["Revenue by Borough:"]
                    for row in rows[:5]:
                        borough = row.get("pickup_zone_borough", "Unknown")
                        revenue = row.get("total_revenue", 0)
                        trips = row.get("trip_count", 0)
                        answer_parts.append(f"  - {borough}: ${revenue:,.2f} ({trips:,} trips)")
                    result["answer"] = "\n".join(answer_parts)

            elif is_tip_question and is_borough_question:
                data = self.computation.get_tips_by_borough()
                result["computation"] = data
                result["identified_concepts"].append("Tips by Borough")

                if not data.get("error"):
                    rows = data.get("data", [])
                    answer_parts = ["Tips by Borough (credit card only):"]
                    for row in rows[:5]:
                        borough = row.get("pickup_zone_borough", "Unknown")
                        avg_tip = row.get("avg_tip", 0)
                        cc_rate = row.get("credit_card_rate", 0)
                        answer_parts.append(f"  - {borough}: ${float(avg_tip):.2f} avg tip ({float(cc_rate)*100:.1f}% credit card)")
                    answer_parts.append("\nNote: Cash tips are not recorded in the data.")
                    result["answer"] = "\n".join(answer_parts)

            elif is_zone_question:
                data = self.computation.get_zone_performance(limit=10)
                result["computation"] = data
                result["identified_concepts"].append("Zone Performance")

                if not data.get("error"):
                    rows = data.get("data", [])
                    answer_parts = ["Top Zones by Revenue:"]
                    for row in rows[:10]:
                        zone = row.get("pickup_zone_zone_name", "Unknown")
                        borough = row.get("pickup_zone_borough", "Unknown")
                        revenue = row.get("total_revenue", 0)
                        trips = row.get("trip_count", 0)
                        answer_parts.append(f"  - {zone} ({borough}): ${revenue:,.2f} ({trips:,} trips)")
                    result["answer"] = "\n".join(answer_parts)

        # Add why context if it's a why question
        if is_why_question and result["context"]:
            if result["answer"]:
                result["answer"] += "\n\nKey Insights:\n" + "\n".join(f"  - {c}" for c in result["context"])

        return result

    def classify_trip(self, **kwargs) -> Dict[str, Any]:
        """Classify a trip using ontology rules."""
        classifications = self.ontology.classify_trip(**kwargs)

        result = {
            "classifications": classifications,
            "details": []
        }

        # Get context for each type
        for trip_type in classifications:
            for tt in self.ontology.get_trip_types():
                if tt["name"] == trip_type:
                    result["details"].append({
                        "type": tt["label"],
                        "context": tt.get("business_context"),
                        "fare_range": tt.get("avg_fare_range")
                    })
                    break

        return result

    def get_time_context(self, hour: int, day_of_week: int) -> Dict[str, Any]:
        """Get time context from ontology."""
        context_name = self.ontology.get_time_context(hour, day_of_week)

        # Get full context
        for tc in self.ontology.get_time_contexts():
            if tc["name"] == context_name:
                return {
                    "name": context_name,
                    "label": tc.get("label"),
                    "expected_demand": tc.get("expected_demand"),
                    "business_context": tc.get("business_context")
                }

        return {"name": context_name}

    def summarize(self) -> Dict[str, Any]:
        """Get summary of all 3 layers."""
        summary = {
            "technical": {
                "available": self.technical.is_available,
                "tables": [],
                "glossary_terms": 0
            },
            "semantic": {
                "available": self.computation.is_available,
                "dimensions": [],
                "measures": []
            },
            "ontology": self.ontology.summarize()
        }

        if self.technical.is_available:
            tables = self.technical.get_all_tables()
            summary["technical"]["tables"] = [t.get("name") for t in tables]
            summary["technical"]["glossary_terms"] = len(self.technical.get_glossary_terms())

        if self.computation.is_available:
            summary["semantic"]["dimensions"] = self.computation.available_dimensions
            summary["semantic"]["measures"] = self.computation.available_measures

        return summary


def main():
    """Demo the unified intelligence layer."""
    print("=" * 70)
    print("UNIFIED INTELLIGENCE LAYER")
    print("Technical + Semantic + Ontology = Intelligent Data Access")
    print("=" * 70)

    unified = UnifiedIntelligenceLayer()

    # Summary
    print("\n" + "=" * 70)
    print("LAYER SUMMARY")
    print("=" * 70)
    summary = unified.summarize()

    print("\n1. Technical Layer (OpenMetadata):")
    print(f"   Available: {summary['technical']['available']}")
    if summary['technical']['available']:
        print(f"   Tables: {summary['technical']['tables']}")
        print(f"   Glossary Terms: {summary['technical']['glossary_terms']}")

    print("\n2. Semantic/Computation Layer (boring-semantic-layer + PostgreSQL):")
    print(f"   Available: {summary['semantic']['available']}")
    if summary['semantic']['available']:
        print(f"   Dimensions ({len(summary['semantic']['dimensions'])}): {summary['semantic']['dimensions'][:5]}...")
        print(f"   Measures ({len(summary['semantic']['measures'])}): {summary['semantic']['measures'][:5]}...")

    print("\n3. Ontology Layer (OWL/RDF):")
    print(f"   Classes: {summary['ontology']['classes']}")
    print(f"   Trip Types: {summary['ontology']['trip_types']}")
    print(f"   Zone Types: {summary['ontology']['zone_types']}")
    print(f"   Time Contexts: {summary['ontology']['time_contexts']}")
    print(f"   Inference Rules: {summary['ontology']['inference_rules']}")

    # Demo 1: Understand a concept
    print("\n" + "=" * 70)
    print("DEMO 1: Understanding 'Manhattan'")
    print("=" * 70)

    concept_info = unified.understand_concept("Manhattan")

    if concept_info["ontology"]:
        print("\nOntology says:")
        print(f"  Label: {concept_info['ontology'].get('label')}")
        print(f"  Comment: {concept_info['ontology'].get('comment')}")
        if concept_info['ontology'].get('business_context'):
            print(f"  Business Context: {concept_info['ontology'].get('business_context')}")

    # Demo 2: Answer a question
    print("\n" + "=" * 70)
    print("DEMO 2: Question - 'What is the total revenue by borough?'")
    print("=" * 70)

    answer = unified.answer_question("What is the total revenue by borough?")

    print(f"\nIdentified Concepts: {answer['identified_concepts']}")
    if answer["answer"]:
        print(f"\nAnswer:\n{answer['answer']}")
    if answer["context"]:
        print(f"\nBusiness Context:")
        for ctx in answer["context"]:
            print(f"  - {ctx}")

    # Demo 3: Trip Classification
    print("\n" + "=" * 70)
    print("DEMO 3: Trip Classification")
    print("=" * 70)

    # Classify a JFK airport trip during rush hour
    trip = unified.classify_trip(
        rate_code_id=2,
        trip_distance=15,
        pickup_hour=8,
        day_of_week=2
    )

    print("\nTrip: JFK flat rate, 15 miles, Tuesday 8 AM")
    print(f"Classifications: {trip['classifications']}")
    for detail in trip["details"]:
        print(f"  - {detail['type']}: {detail.get('context', '')[:60]}...")

    # Demo 4: Time Context
    print("\n" + "=" * 70)
    print("DEMO 4: Time Context Analysis")
    print("=" * 70)

    times = [
        (8, 2, "Tuesday 8 AM"),
        (14, 3, "Wednesday 2 PM"),
        (23, 5, "Friday 11 PM"),
        (15, 6, "Saturday 3 PM")
    ]

    for hour, dow, desc in times:
        ctx = unified.get_time_context(hour, dow)
        demand = ctx.get("expected_demand", "N/A")
        print(f"  {desc}: {ctx['label']} (Demand: {demand})")

    print("\n" + "=" * 70)
    print("UNIFIED INTELLIGENCE LAYER DEMO COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
