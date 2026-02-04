"""
Ontology Layer - Parse and query the NYC Taxi domain ontology.

This module provides functions to:
1. Load the OWL/TTL ontology
2. Query classes, relationships, and business rules
3. Extract SQL mapping hints for query generation
4. Link ontology concepts to glossary terms
"""

from pathlib import Path
from typing import Optional
from rdflib import Graph, Namespace, RDF, RDFS, OWL, XSD
from rdflib.namespace import SKOS


# Define namespaces
TAXI = Namespace("http://example.org/nyc-taxi#")


class OntologyLayer:
    """Interface to the NYC Taxi domain ontology."""

    def __init__(self, ontology_path: Optional[str] = None):
        """Load the ontology from file."""
        if ontology_path is None:
            ontology_path = Path(__file__).parent.parent / "ontology" / "nyc_taxi.ttl"

        self.graph = Graph()
        self.graph.parse(str(ontology_path), format="turtle")
        self.graph.bind("taxi", TAXI)
        self.graph.bind("owl", OWL)
        self.graph.bind("rdfs", RDFS)

    def get_classes(self) -> list[dict]:
        """Get all domain classes with their metadata."""
        query = """
            PREFIX taxi: <http://example.org/nyc-taxi#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>

            SELECT ?cls ?label ?comment ?table ?glossaryTerm
            WHERE {
                ?cls a owl:Class .
                OPTIONAL { ?cls rdfs:label ?label }
                OPTIONAL { ?cls rdfs:comment ?comment }
                OPTIONAL { ?cls taxi:mapsToTable ?table }
                OPTIONAL { ?cls taxi:glossaryTerm ?glossaryTerm }
                FILTER (!isBlank(?cls))
            }
        """
        results = self.graph.query(query)
        classes = []
        for row in results:
            classes.append({
                "uri": str(row.cls),
                "name": str(row.cls).split("#")[-1],
                "label": str(row.label) if row.label else None,
                "comment": str(row.comment) if row.comment else None,
                "maps_to_table": str(row.table) if row.table else None,
                "glossary_term": str(row.glossaryTerm) if row.glossaryTerm else None
            })
        return classes

    def get_main_classes(self) -> list[dict]:
        """Get only top-level domain classes (not subclasses)."""
        main_classes = ["Trip", "Location", "Borough", "PaymentType", "RateType", "Vendor"]
        all_classes = self.get_classes()
        return [c for c in all_classes if c["name"] in main_classes]

    def get_relationships(self) -> list[dict]:
        """Get all object properties (relationships) with SQL mappings."""
        query = """
            PREFIX taxi: <http://example.org/nyc-taxi#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>

            SELECT ?prop ?label ?comment ?domain ?range ?joinCondition ?glossaryTerm
            WHERE {
                ?prop a owl:ObjectProperty .
                OPTIONAL { ?prop rdfs:label ?label }
                OPTIONAL { ?prop rdfs:comment ?comment }
                OPTIONAL { ?prop rdfs:domain ?domain }
                OPTIONAL { ?prop rdfs:range ?range }
                OPTIONAL { ?prop taxi:mapsToJoin ?joinCondition }
                OPTIONAL { ?prop taxi:glossaryTerm ?glossaryTerm }
            }
        """
        results = self.graph.query(query)
        relationships = []
        for row in results:
            relationships.append({
                "uri": str(row.prop),
                "name": str(row.prop).split("#")[-1],
                "label": str(row.label) if row.label else None,
                "comment": str(row.comment) if row.comment else None,
                "domain": str(row.domain).split("#")[-1] if row.domain else None,
                "range": str(row.range).split("#")[-1] if row.range else None,
                "sql_join": str(row.joinCondition) if row.joinCondition else None,
                "glossary_term": str(row.glossaryTerm) if row.glossaryTerm else None
            })
        return relationships

    def get_data_properties(self) -> list[dict]:
        """Get all data properties (attributes/metrics) with SQL mappings."""
        query = """
            PREFIX taxi: <http://example.org/nyc-taxi#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>

            SELECT ?prop ?label ?comment ?domain ?column ?unit ?glossaryTerm ?businessRule
            WHERE {
                ?prop a owl:DatatypeProperty .
                OPTIONAL { ?prop rdfs:label ?label }
                OPTIONAL { ?prop rdfs:comment ?comment }
                OPTIONAL { ?prop rdfs:domain ?domain }
                OPTIONAL { ?prop taxi:mapsToColumn ?column }
                OPTIONAL { ?prop taxi:unit ?unit }
                OPTIONAL { ?prop taxi:glossaryTerm ?glossaryTerm }
                OPTIONAL { ?prop taxi:businessRule ?businessRule }
            }
        """
        results = self.graph.query(query)
        properties = []
        for row in results:
            properties.append({
                "uri": str(row.prop),
                "name": str(row.prop).split("#")[-1],
                "label": str(row.label) if row.label else None,
                "comment": str(row.comment) if row.comment else None,
                "domain": str(row.domain).split("#")[-1] if row.domain else None,
                "sql_column": str(row.column) if row.column else None,
                "unit": str(row.unit) if row.unit else None,
                "glossary_term": str(row.glossaryTerm) if row.glossaryTerm else None,
                "business_rule": str(row.businessRule) if row.businessRule else None
            })
        return properties

    def get_business_rules(self) -> list[dict]:
        """Get all business rules and their conditions."""
        query = """
            PREFIX taxi: <http://example.org/nyc-taxi#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT ?rule ?label ?comment ?condition ?reasoning ?formula ?glossaryTerm
            WHERE {
                ?rule rdfs:comment ?comment .
                FILTER (CONTAINS(str(?comment), "RULE:"))
                OPTIONAL { ?rule rdfs:label ?label }
                OPTIONAL { ?rule taxi:condition ?condition }
                OPTIONAL { ?rule taxi:reasoning ?reasoning }
                OPTIONAL { ?rule taxi:formula ?formula }
                OPTIONAL { ?rule taxi:glossaryTerm ?glossaryTerm }
            }
        """
        results = self.graph.query(query)
        rules = []
        for row in results:
            rules.append({
                "uri": str(row.rule),
                "name": str(row.rule).split("#")[-1],
                "label": str(row.label) if row.label else None,
                "description": str(row.comment) if row.comment else None,
                "condition": str(row.condition) if row.condition else None,
                "reasoning": str(row.reasoning) if row.reasoning else None,
                "formula": str(row.formula) if row.formula else None,
                "glossary_term": str(row.glossaryTerm) if row.glossaryTerm else None
            })
        return rules

    def get_query_patterns(self) -> list[dict]:
        """Get SQL query patterns for common analytics."""
        query = """
            PREFIX taxi: <http://example.org/nyc-taxi#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT ?pattern ?label ?comment ?sqlPattern
            WHERE {
                ?pattern taxi:sqlPattern ?sqlPattern .
                OPTIONAL { ?pattern rdfs:label ?label }
                OPTIONAL { ?pattern rdfs:comment ?comment }
            }
        """
        results = self.graph.query(query)
        patterns = []
        for row in results:
            patterns.append({
                "name": str(row.pattern).split("#")[-1],
                "label": str(row.label) if row.label else None,
                "comment": str(row.comment) if row.comment else None,
                "sql_pattern": str(row.sqlPattern) if row.sqlPattern else None
            })
        return patterns

    def get_path_between_concepts(self, source: str, target: str) -> list[dict]:
        """Find the relationship path between two concepts."""
        # Get all relationships
        relationships = self.get_relationships()

        # Simple path finding (for demo - could use proper graph algorithms)
        paths = []
        for rel in relationships:
            if rel["domain"] == source and rel["range"] == target:
                paths.append({
                    "path": f"{source} --{rel['name']}--> {target}",
                    "sql_join": rel["sql_join"]
                })
            # Check indirect paths through Location
            if source == "Trip" and target == "Borough":
                if rel["domain"] == "Trip" and rel["range"] == "Location":
                    for rel2 in relationships:
                        if rel2["domain"] == "Location" and rel2["range"] == "Borough":
                            paths.append({
                                "path": f"Trip --{rel['name']}--> Location --{rel2['name']}--> Borough",
                                "sql_joins": [rel["sql_join"], rel2["sql_join"]]
                            })
        return paths

    def get_concept_context(self, concept_name: str) -> dict:
        """Get full context for a concept including business insights."""
        query = f"""
            PREFIX taxi: <http://example.org/nyc-taxi#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>

            SELECT ?label ?comment ?context ?table ?column ?glossaryTerm
            WHERE {{
                taxi:{concept_name} rdfs:label ?label .
                OPTIONAL {{ taxi:{concept_name} rdfs:comment ?comment }}
                OPTIONAL {{ taxi:{concept_name} taxi:businessContext ?context }}
                OPTIONAL {{ taxi:{concept_name} taxi:mapsToTable ?table }}
                OPTIONAL {{ taxi:{concept_name} taxi:mapsToColumn ?column }}
                OPTIONAL {{ taxi:{concept_name} taxi:glossaryTerm ?glossaryTerm }}
            }}
        """
        results = list(self.graph.query(query))
        if not results:
            return {}

        row = results[0]
        return {
            "name": concept_name,
            "label": str(row.label) if row.label else None,
            "comment": str(row.comment) if row.comment else None,
            "business_context": str(row.context) if row.context else None,
            "maps_to_table": str(row.table) if row.table else None,
            "maps_to_column": str(row.column) if row.column else None,
            "glossary_term": str(row.glossaryTerm) if row.glossaryTerm else None
        }

    def generate_join_path(self, from_table: str, to_concept: str) -> str:
        """Generate SQL JOIN clauses to reach a concept from a table."""
        if from_table == "trips" and to_concept == "Borough":
            return "JOIN zones z ON trips.pickup_location_id = z.location_id"
        if from_table == "trips" and to_concept == "PaymentType":
            return "JOIN payment_types pt ON trips.payment_type = pt.payment_type_id"
        if from_table == "trips" and to_concept == "RateType":
            return "JOIN rate_codes rc ON trips.rate_code_id = rc.rate_code_id"
        return ""

    def get_trip_types(self) -> list[dict]:
        """Get all trip type subclasses with classification conditions."""
        query = """
            PREFIX taxi: <http://example.org/nyc-taxi#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>

            SELECT ?tripType ?label ?comment ?condition ?context ?fareRange ?distance
            WHERE {
                ?tripType rdfs:subClassOf taxi:Trip .
                ?tripType rdfs:label ?label .
                OPTIONAL { ?tripType rdfs:comment ?comment }
                OPTIONAL { ?tripType taxi:classificationCondition ?condition }
                OPTIONAL { ?tripType taxi:businessContext ?context }
                OPTIONAL { ?tripType taxi:avgFareRange ?fareRange }
                OPTIONAL { ?tripType taxi:typicalDistance ?distance }
            }
        """
        results = self.graph.query(query)
        trip_types = []
        for row in results:
            trip_types.append({
                "name": str(row.tripType).split("#")[-1],
                "label": str(row.label) if row.label else None,
                "comment": str(row.comment) if row.comment else None,
                "classification_condition": str(row.condition) if row.condition else None,
                "business_context": str(row.context) if row.context else None,
                "avg_fare_range": str(row.fareRange) if row.fareRange else None,
                "typical_distance": str(row.distance) if row.distance else None
            })
        return trip_types

    def get_zone_types(self) -> list[dict]:
        """Get all zone type classifications."""
        query = """
            PREFIX taxi: <http://example.org/nyc-taxi#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>

            SELECT ?zoneType ?label ?comment ?context ?examples ?zoneIds
            WHERE {
                ?zoneType rdfs:subClassOf taxi:ZoneType .
                ?zoneType rdfs:label ?label .
                OPTIONAL { ?zoneType rdfs:comment ?comment }
                OPTIONAL { ?zoneType taxi:businessContext ?context }
                OPTIONAL { ?zoneType taxi:exampleZones ?examples }
                OPTIONAL { ?zoneType taxi:zoneIds ?zoneIds }
            }
        """
        results = self.graph.query(query)
        zone_types = []
        for row in results:
            zone_types.append({
                "name": str(row.zoneType).split("#")[-1],
                "label": str(row.label) if row.label else None,
                "comment": str(row.comment) if row.comment else None,
                "business_context": str(row.context) if row.context else None,
                "example_zones": str(row.examples) if row.examples else None,
                "zone_ids": str(row.zoneIds) if row.zoneIds else None
            })
        return zone_types

    def get_time_contexts(self) -> list[dict]:
        """Get all time context definitions."""
        query = """
            PREFIX taxi: <http://example.org/nyc-taxi#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>

            SELECT ?timeCtx ?label ?comment ?condition ?context ?demand
            WHERE {
                ?timeCtx rdfs:subClassOf taxi:TimeContext .
                ?timeCtx rdfs:label ?label .
                OPTIONAL { ?timeCtx rdfs:comment ?comment }
                OPTIONAL { ?timeCtx taxi:timeCondition ?condition }
                OPTIONAL { ?timeCtx taxi:businessContext ?context }
                OPTIONAL { ?timeCtx taxi:expectedDemand ?demand }
            }
        """
        results = self.graph.query(query)
        time_contexts = []
        for row in results:
            time_contexts.append({
                "name": str(row.timeCtx).split("#")[-1],
                "label": str(row.label) if row.label else None,
                "comment": str(row.comment) if row.comment else None,
                "time_condition": str(row.condition) if row.condition else None,
                "business_context": str(row.context) if row.context else None,
                "expected_demand": str(row.demand) if row.demand else None
            })
        return time_contexts

    def get_zone_instances(self) -> list[dict]:
        """Get specific zone instances (JFK, Midtown, etc.)."""
        query = """
            PREFIX taxi: <http://example.org/nyc-taxi#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

            SELECT ?zone ?label ?locationId ?borough ?zoneType ?context ?revenue
            WHERE {
                ?zone rdf:type taxi:Location .
                ?zone rdfs:label ?label .
                OPTIONAL { ?zone taxi:locationId ?locationId }
                OPTIONAL { ?zone taxi:borough ?borough }
                OPTIONAL { ?zone taxi:zoneType ?zoneType }
                OPTIONAL { ?zone taxi:businessContext ?context }
                OPTIONAL { ?zone taxi:avgTripRevenue ?revenue }
            }
        """
        results = self.graph.query(query)
        zones = []
        for row in results:
            zones.append({
                "name": str(row.zone).split("#")[-1],
                "label": str(row.label) if row.label else None,
                "location_id": int(row.locationId) if row.locationId else None,
                "borough": str(row.borough) if row.borough else None,
                "zone_type": str(row.zoneType).split("#")[-1] if row.zoneType else None,
                "business_context": str(row.context) if row.context else None,
                "avg_trip_revenue": str(row.revenue) if row.revenue else None
            })
        return zones

    def get_inference_rules(self) -> list[dict]:
        """Get inference rules (trip classification, tip patterns, etc.)."""
        query = """
            PREFIX taxi: <http://example.org/nyc-taxi#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT ?rule ?label ?comment ?reasoning ?sqlExample ?metrics
            WHERE {
                ?rule rdfs:label ?label .
                ?rule rdfs:comment ?comment .
                FILTER (CONTAINS(str(?comment), "RULE:"))
                OPTIONAL { ?rule taxi:reasoning ?reasoning }
                OPTIONAL { ?rule taxi:sqlExample ?sqlExample }
                OPTIONAL { ?rule taxi:metrics ?metrics }
            }
        """
        results = self.graph.query(query)
        rules = []
        for row in results:
            rules.append({
                "name": str(row.rule).split("#")[-1],
                "label": str(row.label) if row.label else None,
                "description": str(row.comment) if row.comment else None,
                "reasoning": str(row.reasoning) if row.reasoning else None,
                "sql_example": str(row.sqlExample) if row.sqlExample else None,
                "metrics": str(row.metrics) if row.metrics else None
            })
        return rules

    def get_zone_by_id(self, location_id: int) -> dict:
        """Get zone information by location ID."""
        zones = self.get_zone_instances()
        for zone in zones:
            if zone.get("location_id") == location_id:
                return zone
        return {}

    def classify_trip(
        self,
        rate_code_id: int = None,
        trip_distance: float = None,
        pickup_hour: int = None,
        day_of_week: int = None,
        pickup_location_id: int = None,
        dropoff_location_id: int = None
    ) -> list[str]:
        """Classify a trip based on its attributes.

        Args:
            rate_code_id: Rate code (2=JFK, 3=Newark)
            trip_distance: Distance in miles
            pickup_hour: Hour of pickup (0-23)
            day_of_week: Day of week (0=Sun, 6=Sat)
            pickup_location_id: Pickup zone ID
            dropoff_location_id: Dropoff zone ID

        Returns:
            List of applicable trip type names
        """
        airport_zones = {1, 132, 138}  # Newark, JFK, LaGuardia
        trip_types = []

        # Airport trip check
        if rate_code_id in (2, 3):
            trip_types.append("AirportTrip")
        elif pickup_location_id in airport_zones or dropoff_location_id in airport_zones:
            trip_types.append("AirportTrip")

        # Distance-based classification
        if trip_distance is not None:
            if trip_distance > 10:
                trip_types.append("LongDistanceTrip")
            elif trip_distance < 2:
                trip_types.append("ShortTrip")

        # Time-based classification
        if pickup_hour is not None and day_of_week is not None:
            # Night trip
            if pickup_hour >= 22 or pickup_hour < 5:
                trip_types.append("NightTrip")

            # Weekend trip
            if day_of_week in (0, 6):
                trip_types.append("WeekendTrip")

            # Commute trip (weekday rush hours)
            if day_of_week in range(1, 6):  # Mon-Fri
                if (7 <= pickup_hour <= 9) or (17 <= pickup_hour <= 19):
                    trip_types.append("CommuteTrip")

        return trip_types if trip_types else ["StandardTrip"]

    def get_time_context(self, pickup_hour: int, day_of_week: int) -> str:
        """Determine the time context for a given time.

        Args:
            pickup_hour: Hour of pickup (0-23)
            day_of_week: Day of week (0=Sun, 6=Sat)

        Returns:
            Time context name
        """
        is_weekend = day_of_week in (0, 6)
        is_weekday = day_of_week in range(1, 6)

        # Night time
        if pickup_hour >= 22 or pickup_hour < 5:
            if day_of_week == 5 and pickup_hour >= 20:  # Friday night
                return "WeekendNight"
            if day_of_week == 6 and (pickup_hour >= 20 or pickup_hour < 4):  # Saturday night
                return "WeekendNight"
            return "NightTime"

        # Weekend day
        if is_weekend and 8 <= pickup_hour <= 20:
            return "WeekendDay"

        # Weekday rush hour
        if is_weekday:
            if (7 <= pickup_hour <= 9) or (17 <= pickup_hour <= 20):
                return "RushHour"
            if 10 <= pickup_hour <= 16:
                return "OffPeak"

        return "OffPeak"

    def get_context_for_analysis(self, analysis_type: str) -> dict:
        """Get relevant ontology context for a type of analysis.

        Args:
            analysis_type: One of 'revenue', 'tips', 'demand', 'airport', 'time'

        Returns:
            Dict with relevant rules, patterns, and context
        """
        context = {
            "analysis_type": analysis_type,
            "relevant_rules": [],
            "query_patterns": [],
            "business_insights": []
        }

        rules = self.get_inference_rules()
        patterns = self.get_query_patterns()

        if analysis_type == "revenue":
            context["relevant_rules"] = [r for r in rules
                if "Revenue" in r.get("name", "") or "revenue" in (r.get("reasoning") or "").lower()]
            context["query_patterns"] = [p for p in patterns
                if "Revenue" in p.get("name", "")]
            context["business_insights"] = [
                "Airport trips have highest per-trip revenue",
                "Manhattan dominates total revenue (~90%)",
                "Rush hours have highest trip volume"
            ]

        elif analysis_type == "tips":
            context["relevant_rules"] = [r for r in rules
                if "Tip" in r.get("name", "") or "tip" in (r.get("reasoning") or "").lower()]
            context["business_insights"] = [
                "Cash tips are NOT recorded - exclude payment_type=2 from tip analysis",
                "Tourist zones tend to have higher tip percentages",
                "Airport and business districts show consistent 15-20% tips"
            ]

        elif analysis_type == "demand":
            context["relevant_rules"] = [r for r in rules
                if "Demand" in r.get("name", "")]
            context["time_contexts"] = self.get_time_contexts()
            context["business_insights"] = [
                "Rush hours (7-9 AM, 5-8 PM weekdays) have highest demand",
                "Manhattan business districts dominate weekday demand",
                "Entertainment districts peak late night/weekends"
            ]

        elif analysis_type == "airport":
            context["relevant_rules"] = [r for r in rules
                if "Airport" in r.get("name", "") or "airport" in str(r.get("reasoning", "")).lower()]
            context["query_patterns"] = [p for p in patterns
                if "Airport" in p.get("name", "")]
            context["zone_instances"] = [z for z in self.get_zone_instances()
                if z.get("zone_type") == "AirportZone"]
            context["business_insights"] = [
                "JFK: Fixed $52 flat rate to Manhattan (rate_code=2)",
                "Newark: Metered + surcharge (rate_code=3)",
                "LaGuardia: Standard metered fare, closest to Manhattan"
            ]

        elif analysis_type == "time":
            context["time_contexts"] = self.get_time_contexts()
            context["query_patterns"] = [p for p in patterns
                if "Time" in p.get("name", "")]
            context["trip_types"] = [t for t in self.get_trip_types()
                if t.get("classification_condition") and "HOUR" in t.get("classification_condition", "")]

        return context

    def summarize(self) -> dict:
        """Get a summary of the ontology."""
        return {
            "classes": len(self.get_classes()),
            "main_classes": [c["name"] for c in self.get_main_classes()],
            "trip_types": len(self.get_trip_types()),
            "zone_types": len(self.get_zone_types()),
            "zone_instances": len(self.get_zone_instances()),
            "time_contexts": len(self.get_time_contexts()),
            "relationships": len(self.get_relationships()),
            "data_properties": len(self.get_data_properties()),
            "business_rules": len(self.get_business_rules()),
            "inference_rules": len(self.get_inference_rules()),
            "query_patterns": len(self.get_query_patterns())
        }


def main():
    """Demo the ontology layer."""
    print("=" * 70)
    print("NYC Taxi Domain Ontology - Enriched Version")
    print("=" * 70)

    onto = OntologyLayer()

    # Summary
    summary = onto.summarize()
    print(f"\nOntology Summary:")
    print(f"  Total Classes: {summary['classes']}")
    print(f"  Main Classes: {', '.join(summary['main_classes'])}")
    print(f"  Trip Types: {summary['trip_types']}")
    print(f"  Zone Types: {summary['zone_types']}")
    print(f"  Zone Instances: {summary['zone_instances']}")
    print(f"  Time Contexts: {summary['time_contexts']}")
    print(f"  Relationships: {summary['relationships']}")
    print(f"  Data Properties: {summary['data_properties']}")
    print(f"  Business Rules: {summary['business_rules']}")
    print(f"  Inference Rules: {summary['inference_rules']}")
    print(f"  Query Patterns: {summary['query_patterns']}")

    # Trip Types
    print(f"\n" + "=" * 70)
    print("TRIP TYPES (Classification)")
    print("=" * 70)
    for tt in onto.get_trip_types():
        print(f"\n  {tt['label']}:")
        if tt['classification_condition']:
            print(f"    Condition: {tt['classification_condition'][:60]}...")
        if tt['business_context']:
            print(f"    Context: {tt['business_context'][:60]}...")
        if tt['avg_fare_range']:
            print(f"    Fare Range: {tt['avg_fare_range']}")

    # Zone Types
    print(f"\n" + "=" * 70)
    print("ZONE TYPES")
    print("=" * 70)
    for zt in onto.get_zone_types():
        print(f"\n  {zt['label']}:")
        if zt['business_context']:
            print(f"    Context: {zt['business_context'][:70]}...")
        if zt['example_zones']:
            print(f"    Examples: {zt['example_zones']}")

    # Time Contexts
    print(f"\n" + "=" * 70)
    print("TIME CONTEXTS")
    print("=" * 70)
    for tc in onto.get_time_contexts():
        print(f"\n  {tc['label']} (Demand: {tc.get('expected_demand', 'N/A')}):")
        if tc['time_condition']:
            cond = tc['time_condition'][:70] + "..." if len(tc.get('time_condition', '')) > 70 else tc['time_condition']
            print(f"    Condition: {cond}")

    # Zone Instances (airports and key zones)
    print(f"\n" + "=" * 70)
    print("KEY ZONE INSTANCES")
    print("=" * 70)
    zones = onto.get_zone_instances()
    airports = [z for z in zones if z.get('zone_type') == 'AirportZone']
    business = [z for z in zones if z.get('zone_type') == 'BusinessDistrict'][:3]

    print("\n  Airports:")
    for z in airports:
        print(f"    {z['label']} (ID: {z['location_id']}, {z['borough']})")
        if z['business_context']:
            print(f"      {z['business_context'][:60]}...")

    print("\n  Business Districts (sample):")
    for z in business:
        print(f"    {z['label']} (ID: {z['location_id']})")

    # Trip Classification Demo
    print(f"\n" + "=" * 70)
    print("TRIP CLASSIFICATION DEMO")
    print("=" * 70)

    # Example 1: JFK Airport trip
    trip1 = onto.classify_trip(rate_code_id=2, trip_distance=15)
    print(f"\n  JFK flat rate trip (15 miles): {trip1}")

    # Example 2: Short Manhattan trip during rush hour
    trip2 = onto.classify_trip(trip_distance=1.5, pickup_hour=8, day_of_week=2)
    print(f"  Short weekday morning trip: {trip2}")

    # Example 3: Late night long trip
    trip3 = onto.classify_trip(trip_distance=12, pickup_hour=23, day_of_week=5)
    print(f"  Late Friday long trip: {trip3}")

    # Example 4: Weekend trip
    trip4 = onto.classify_trip(trip_distance=5, pickup_hour=14, day_of_week=6)
    print(f"  Saturday afternoon trip: {trip4}")

    # Time Context Demo
    print(f"\n  Time Context Examples:")
    print(f"    Tuesday 8 AM: {onto.get_time_context(8, 2)}")
    print(f"    Wednesday 2 PM: {onto.get_time_context(14, 3)}")
    print(f"    Friday 11 PM: {onto.get_time_context(23, 5)}")
    print(f"    Saturday 3 PM: {onto.get_time_context(15, 6)}")

    # Context for Analysis
    print(f"\n" + "=" * 70)
    print("ANALYSIS CONTEXT - Tips")
    print("=" * 70)
    tip_context = onto.get_context_for_analysis("tips")
    print(f"\n  Business Insights:")
    for insight in tip_context['business_insights']:
        print(f"    - {insight}")

    print(f"\n" + "=" * 70)
    print("ANALYSIS CONTEXT - Airport")
    print("=" * 70)
    airport_context = onto.get_context_for_analysis("airport")
    print(f"\n  Business Insights:")
    for insight in airport_context['business_insights']:
        print(f"    - {insight}")

    # Inference Rules
    print(f"\n" + "=" * 70)
    print("INFERENCE RULES")
    print("=" * 70)
    for rule in onto.get_inference_rules()[:3]:
        print(f"\n  {rule['label']}:")
        if rule['reasoning']:
            # Print first few lines of reasoning
            lines = rule['reasoning'].strip().split('\n')[:3]
            for line in lines:
                print(f"    {line.strip()}")

    print(f"\n" + "=" * 70)
    print("ONTOLOGY LAYER DEMO COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
