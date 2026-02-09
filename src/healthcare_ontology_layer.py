"""
Healthcare Ontology Layer - Parse and query the healthcare domain ontology.

Same pattern as OntologyLayer but for SNOMED CT-inspired healthcare concepts.
Provides business context, classification rules, and domain knowledge
for healthcare data analysis.
"""

from pathlib import Path
from typing import Optional
from rdflib import Graph, Namespace, RDF, RDFS, OWL


HC = Namespace("http://example.org/healthcare#")


class HealthcareOntologyLayer:
    """Interface to the healthcare domain ontology."""

    def __init__(self, ontology_path: Optional[str] = None):
        if ontology_path is None:
            ontology_path = Path(__file__).parent.parent / "ontology" / "healthcare.ttl"

        self.graph = Graph()
        self.graph.parse(str(ontology_path), format="turtle")
        self.graph.bind("hc", HC)
        self.graph.bind("owl", OWL)
        self.graph.bind("rdfs", RDFS)

    def get_classes(self) -> list[dict]:
        """Get all domain classes with metadata."""
        query = """
            PREFIX hc: <http://example.org/healthcare#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>

            SELECT ?cls ?label ?comment ?table ?context
            WHERE {
                ?cls a owl:Class .
                OPTIONAL { ?cls rdfs:label ?label }
                OPTIONAL { ?cls rdfs:comment ?comment }
                OPTIONAL { ?cls hc:mapsToTable ?table }
                OPTIONAL { ?cls hc:businessContext ?context }
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
                "business_context": str(row.context) if row.context else None,
            })
        return classes

    def get_main_classes(self) -> list[dict]:
        """Get only top-level domain classes."""
        main = ["Patient", "Encounter", "Condition", "Medication", "Procedure",
                "Organization", "Provider", "Payer"]
        all_classes = self.get_classes()
        return [c for c in all_classes if c["name"] in main]

    def get_relationships(self) -> list[dict]:
        """Get all object properties with SQL join mappings."""
        query = """
            PREFIX hc: <http://example.org/healthcare#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>

            SELECT ?prop ?label ?comment ?domain ?range ?joinCondition
            WHERE {
                ?prop a owl:ObjectProperty .
                OPTIONAL { ?prop rdfs:label ?label }
                OPTIONAL { ?prop rdfs:comment ?comment }
                OPTIONAL { ?prop rdfs:domain ?domain }
                OPTIONAL { ?prop rdfs:range ?range }
                OPTIONAL { ?prop hc:mapsToJoin ?joinCondition }
            }
        """
        results = self.graph.query(query)
        relationships = []
        for row in results:
            relationships.append({
                "name": str(row.prop).split("#")[-1],
                "label": str(row.label) if row.label else None,
                "domain": str(row.domain).split("#")[-1] if row.domain else None,
                "range": str(row.range).split("#")[-1] if row.range else None,
                "sql_join": str(row.joinCondition) if row.joinCondition else None,
            })
        return relationships

    def get_data_properties(self) -> list[dict]:
        """Get all data properties with column mappings."""
        query = """
            PREFIX hc: <http://example.org/healthcare#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>

            SELECT ?prop ?label ?comment ?domain ?column ?context
            WHERE {
                ?prop a owl:DatatypeProperty .
                OPTIONAL { ?prop rdfs:label ?label }
                OPTIONAL { ?prop rdfs:comment ?comment }
                OPTIONAL { ?prop rdfs:domain ?domain }
                OPTIONAL { ?prop hc:mapsToColumn ?column }
                OPTIONAL { ?prop hc:businessContext ?context }
            }
        """
        results = self.graph.query(query)
        properties = []
        for row in results:
            properties.append({
                "name": str(row.prop).split("#")[-1],
                "label": str(row.label) if row.label else None,
                "comment": str(row.comment) if row.comment else None,
                "domain": str(row.domain).split("#")[-1] if row.domain else None,
                "sql_column": str(row.column) if row.column else None,
                "business_context": str(row.context) if row.context else None,
            })
        return properties

    def get_business_rules(self) -> list[dict]:
        """Get all business rules (classes with RULE: in comment)."""
        query = """
            PREFIX hc: <http://example.org/healthcare#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT ?rule ?label ?comment ?condition ?reasoning ?formula ?metrics
            WHERE {
                ?rule rdfs:comment ?comment .
                FILTER (CONTAINS(str(?comment), "RULE:"))
                OPTIONAL { ?rule rdfs:label ?label }
                OPTIONAL { ?rule hc:condition ?condition }
                OPTIONAL { ?rule hc:reasoning ?reasoning }
                OPTIONAL { ?rule hc:formula ?formula }
                OPTIONAL { ?rule hc:metrics ?metrics }
            }
        """
        results = self.graph.query(query)
        rules = []
        for row in results:
            rules.append({
                "name": str(row.rule).split("#")[-1],
                "label": str(row.label) if row.label else None,
                "description": str(row.comment) if row.comment else None,
                "condition": str(row.condition) if row.condition else None,
                "reasoning": str(row.reasoning) if row.reasoning else None,
                "formula": str(row.formula) if row.formula else None,
                "metrics": str(row.metrics) if row.metrics else None,
            })
        return rules

    def get_encounter_types(self) -> list[dict]:
        """Get encounter subclasses with classification conditions."""
        query = """
            PREFIX hc: <http://example.org/healthcare#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT ?type ?label ?comment ?condition ?context ?costRange
            WHERE {
                ?type rdfs:subClassOf hc:Encounter .
                ?type rdfs:label ?label .
                OPTIONAL { ?type rdfs:comment ?comment }
                OPTIONAL { ?type hc:classificationCondition ?condition }
                OPTIONAL { ?type hc:businessContext ?context }
                OPTIONAL { ?type hc:avgCostRange ?costRange }
            }
        """
        results = self.graph.query(query)
        types = []
        for row in results:
            types.append({
                "name": str(row.type).split("#")[-1],
                "label": str(row.label) if row.label else None,
                "comment": str(row.comment) if row.comment else None,
                "classification_condition": str(row.condition) if row.condition else None,
                "business_context": str(row.context) if row.context else None,
                "avg_cost_range": str(row.costRange) if row.costRange else None,
            })
        return types

    def get_condition_categories(self) -> list[dict]:
        """Get condition subclasses (disease categories)."""
        query = """
            PREFIX hc: <http://example.org/healthcare#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT ?cond ?label ?comment ?snomed ?context ?meds
            WHERE {
                ?cond rdfs:subClassOf+ hc:Condition .
                ?cond rdfs:label ?label .
                OPTIONAL { ?cond rdfs:comment ?comment }
                OPTIONAL { ?cond hc:snomedCode ?snomed }
                OPTIONAL { ?cond hc:businessContext ?context }
                OPTIONAL { ?cond hc:commonMedications ?meds }
            }
        """
        results = self.graph.query(query)
        categories = []
        for row in results:
            categories.append({
                "name": str(row.cond).split("#")[-1],
                "label": str(row.label) if row.label else None,
                "comment": str(row.comment) if row.comment else None,
                "snomed_code": str(row.snomed) if row.snomed else None,
                "business_context": str(row.context) if row.context else None,
                "common_medications": str(row.meds) if row.meds else None,
            })
        return categories

    def get_concept_context(self, concept_name: str) -> dict:
        """Get full context for a concept."""
        query = f"""
            PREFIX hc: <http://example.org/healthcare#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT ?label ?comment ?context ?table ?column
            WHERE {{
                hc:{concept_name} rdfs:label ?label .
                OPTIONAL {{ hc:{concept_name} rdfs:comment ?comment }}
                OPTIONAL {{ hc:{concept_name} hc:businessContext ?context }}
                OPTIONAL {{ hc:{concept_name} hc:mapsToTable ?table }}
                OPTIONAL {{ hc:{concept_name} hc:mapsToColumn ?column }}
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
        }

    def classify_encounter(
        self,
        encounter_class: str = None,
        total_claim_cost: float = None,
        payer_coverage: float = None,
    ) -> list[str]:
        """Classify an encounter based on attributes.

        Returns list of applicable classification labels.
        """
        classifications = []

        # Encounter class
        class_map = {
            "emergency": "EmergencyEncounter",
            "inpatient": "InpatientEncounter",
            "ambulatory": "AmbulatoryEncounter",
            "wellness": "WellnessEncounter",
            "urgentcare": "UrgentCareEncounter",
        }
        if encounter_class:
            ec = encounter_class.lower()
            if ec in class_map:
                classifications.append(class_map[ec])

        # Cost classification
        if total_claim_cost is not None:
            if total_claim_cost > 10000:
                classifications.append("HighCost")
            elif total_claim_cost > 1000:
                classifications.append("ModerateCost")
            else:
                classifications.append("LowCost")

        # Coverage gap
        if total_claim_cost and payer_coverage is not None:
            if total_claim_cost > 0:
                ratio = payer_coverage / total_claim_cost
                if ratio < 0.5:
                    classifications.append("CoverageGap")
                elif ratio > 0.9:
                    classifications.append("WellCovered")

        return classifications if classifications else ["Unclassified"]

    def get_context_for_analysis(self, analysis_type: str) -> dict:
        """Get relevant context for a type of analysis.

        Args:
            analysis_type: One of 'cost', 'conditions', 'demographics',
                          'coverage', 'utilization', 'readmission'
        """
        context = {
            "analysis_type": analysis_type,
            "relevant_rules": [],
            "business_insights": [],
        }

        rules = self.get_business_rules()

        if analysis_type == "cost":
            context["relevant_rules"] = [r for r in rules
                if "Cost" in r.get("name", "") or "cost" in (r.get("reasoning") or "").lower()]
            context["encounter_types"] = self.get_encounter_types()
            context["business_insights"] = [
                "Inpatient encounters drive the highest total costs",
                "Emergency visits cost 5-10x more than ambulatory for similar conditions",
                "Chronic conditions account for 75%+ of spending",
                "Out-of-pocket = total_claim_cost - payer_coverage",
            ]

        elif analysis_type == "conditions":
            context["relevant_rules"] = [r for r in rules
                if "Chronic" in r.get("name", "")]
            context["condition_categories"] = self.get_condition_categories()
            context["business_insights"] = [
                "Chronic conditions (diabetes, hypertension) drive repeated encounters",
                "Comorbidities multiply cost exponentially",
                "Preventive management reduces acute episodes",
                "Depression is often comorbid and increases cost of all conditions",
            ]

        elif analysis_type == "demographics":
            context["relevant_rules"] = [r for r in rules
                if "Demographic" in r.get("name", "") or "Disparity" in r.get("name", "")]
            context["business_insights"] = [
                "Income is the strongest predictor of healthcare utilization patterns",
                "Lower income correlates with higher emergency and lower wellness rates",
                "Racial disparities persist even after controlling for income",
                "Geographic (county) variations reflect provider availability",
            ]

        elif analysis_type == "coverage":
            context["relevant_rules"] = [r for r in rules
                if "Coverage" in r.get("name", "") or "coverage" in (r.get("reasoning") or "").lower()]
            context["business_insights"] = [
                "Coverage ratio = payer_coverage / total_claim_cost",
                "Low coverage leads to delayed care and medication non-adherence",
                "Medication costs are the first thing patients cut when coverage is low",
                "Coverage gaps vary significantly by payer and encounter type",
            ]

        elif analysis_type == "utilization":
            context["relevant_rules"] = [r for r in rules
                if "Emergency" in r.get("name", "") or "Preventive" in r.get("name", "")]
            context["encounter_types"] = self.get_encounter_types()
            context["business_insights"] = [
                "High ED-to-wellness ratio indicates access problems",
                "Wellness visits are the most cost-effective intervention",
                "Urgent care growth reduces overall system costs",
                "Ambulatory visits are the most common encounter type",
            ]

        elif analysis_type == "readmission":
            context["relevant_rules"] = [r for r in rules
                if "Readmission" in r.get("name", "")]
            context["business_insights"] = [
                "30-day readmission is a CMS quality measure",
                "High rates trigger financial penalties for hospitals",
                "Heart failure, COPD, and pneumonia have highest readmission rates",
                "Adequate discharge planning and follow-up reduce readmissions",
            ]

        return context

    def summarize(self) -> dict:
        return {
            "classes": len(self.get_classes()),
            "main_classes": [c["name"] for c in self.get_main_classes()],
            "encounter_types": len(self.get_encounter_types()),
            "condition_categories": len(self.get_condition_categories()),
            "relationships": len(self.get_relationships()),
            "data_properties": len(self.get_data_properties()),
            "business_rules": len(self.get_business_rules()),
        }


def main():
    """Demo the healthcare ontology layer."""
    print("=" * 70)
    print("Healthcare Domain Ontology")
    print("=" * 70)

    onto = HealthcareOntologyLayer()

    # Summary
    summary = onto.summarize()
    print(f"\nOntology Summary:")
    print(f"  Total Classes: {summary['classes']}")
    print(f"  Main Classes: {', '.join(summary['main_classes'])}")
    print(f"  Encounter Types: {summary['encounter_types']}")
    print(f"  Condition Categories: {summary['condition_categories']}")
    print(f"  Relationships: {summary['relationships']}")
    print(f"  Data Properties: {summary['data_properties']}")
    print(f"  Business Rules: {summary['business_rules']}")

    # Encounter Types
    print(f"\n" + "=" * 70)
    print("ENCOUNTER TYPES")
    print("=" * 70)
    for et in onto.get_encounter_types():
        print(f"\n  {et['label']}:")
        if et["classification_condition"]:
            print(f"    Condition: {et['classification_condition']}")
        if et["avg_cost_range"]:
            print(f"    Cost Range: {et['avg_cost_range']}")
        if et["business_context"]:
            print(f"    Context: {et['business_context'][:80]}...")

    # Condition Categories
    print(f"\n" + "=" * 70)
    print("CONDITION CATEGORIES")
    print("=" * 70)
    for cc in onto.get_condition_categories():
        print(f"\n  {cc['label']}:")
        if cc["snomed_code"]:
            print(f"    SNOMED: {cc['snomed_code']}")
        if cc["common_medications"]:
            print(f"    Medications: {cc['common_medications']}")

    # Business Rules
    print(f"\n" + "=" * 70)
    print("BUSINESS RULES")
    print("=" * 70)
    for rule in onto.get_business_rules():
        print(f"\n  {rule['label']}:")
        desc = rule.get("description", "")
        if desc:
            print(f"    {desc[:100]}")

    # Classification Demo
    print(f"\n" + "=" * 70)
    print("ENCOUNTER CLASSIFICATION DEMO")
    print("=" * 70)
    print(f"  Emergency, $3000, $1000 coverage: {onto.classify_encounter('emergency', 3000, 1000)}")
    print(f"  Wellness, $200, $180 coverage: {onto.classify_encounter('wellness', 200, 180)}")
    print(f"  Inpatient, $25000, $20000 coverage: {onto.classify_encounter('inpatient', 25000, 20000)}")
    print(f"  Ambulatory, $500, $100 coverage: {onto.classify_encounter('ambulatory', 500, 100)}")

    # Analysis Context
    print(f"\n" + "=" * 70)
    print("ANALYSIS CONTEXT - Cost")
    print("=" * 70)
    ctx = onto.get_context_for_analysis("cost")
    for insight in ctx["business_insights"]:
        print(f"  - {insight}")

    print(f"\n" + "=" * 70)
    print("ONTOLOGY LAYER DEMO COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
