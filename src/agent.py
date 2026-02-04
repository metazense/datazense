"""
NYC Taxi AI Agent - Powered by Azure OpenAI + Semantic Layer + Ontology

This agent combines:
1. Semantic Layer (boring-semantic-layer + PostgreSQL) - For metric computation
2. Ontology Layer (OWL/RDF) - For business context and reasoning
3. Azure OpenAI (GPT-4) - For natural language understanding

The agent can:
- Query metrics using natural language
- Explain why metrics have certain values
- Classify trips based on ontology rules
- Provide business context for data insights

Usage:
    from agent import NYCTaxiAgent

    agent = NYCTaxiAgent()
    response = agent.ask("What is the total revenue by borough?")
    print(response.answer)
"""

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass
class AgentResponse:
    """Response from the agent."""
    question: str
    answer: str
    data: Optional[List[Dict]] = None
    reasoning_steps: List[str] = field(default_factory=list)
    tools_used: List[str] = field(default_factory=list)
    error: Optional[str] = None


class NYCTaxiAgent:
    """
    AI Agent for NYC Taxi data analysis.

    Combines semantic layer (computation) with ontology (reasoning)
    to provide intelligent, context-aware answers.
    """

    # System prompt for the LLM
    SYSTEM_PROMPT = """You are an expert NYC taxi data analyst with access to a 3-layer metadata architecture:

1. **Technical Layer (OpenMetadata)**: Database catalog with tables, columns, types, and glossary terms
2. **Semantic Layer (PostgreSQL)**: Metric computation with dimensions and measures
3. **Ontology Layer (OWL/RDF)**: Business context, rules, and domain knowledge

## Available Dimensions (for grouping in query_metrics)
- pickup_zone.borough: NYC borough (Manhattan, Brooklyn, Queens, Bronx, Staten Island)
- pickup_zone.zone_name: Specific zone name (JFK Airport, Midtown Center, etc.)
- payment_type: Payment method (1=Credit Card, 2=Cash, 3=No Charge, 4=Dispute)
- rate_code_id: Rate type (1=Standard, 2=JFK Flat Rate, 3=Newark, etc.)
- vendor_id: Taxi vendor (1=CMT, 2=VeriFone)

## Available Measures (for computation in query_metrics)
- trip_count: Number of trips
- total_revenue: Sum of fare + tip (USD)
- total_fare, total_tips, avg_fare, avg_tip, avg_distance
- credit_card_rate: Percentage of credit card payments
- airport_trips: Count of airport trips (rate_code 2 or 3)

## Technical Metadata Tools (OpenMetadata)
- list_tables: Show all tables in the database
- get_table_schema: Get columns, types, descriptions for a table
- get_glossary_terms: Get business term definitions (metrics, dimensions, concepts)
- search_metadata: Search across all metadata for a keyword

## Important Business Rules
1. Cash tips are NOT recorded - exclude payment_type=2 from tip analysis
2. JFK Airport trips use flat $52 rate (rate_code_id=2)
3. Manhattan dominates taxi activity (~90% of trips)
4. Rush hours are 7-9 AM and 5-8 PM on weekdays

## Your Approach
1. For data questions: Use query_metrics to get actual numbers
2. For "why" questions: Use get_context and explain_metric for insights
3. For schema/metadata questions: Use list_tables, get_table_schema, get_glossary_terms
4. For searching: Use search_metadata to find relevant tables, columns, or terms
5. For trip classification: Use classify_trip with ontology rules
6. NEVER make up numbers - always query the data
7. Provide context from the ontology to explain patterns

Be concise but informative. Include actual numbers when available."""

    # Tool definitions for function calling
    TOOLS = [
        {
            "type": "function",
            "function": {
                "name": "query_metrics",
                "description": "Query aggregated metrics from NYC taxi data. Use this to get actual numbers like trip counts, revenue, tips, etc.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dimensions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Dimensions to group by. Options: pickup_zone.borough, pickup_zone.zone_name, payment_type, rate_code_id, vendor_id"
                        },
                        "measures": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Measures to compute. Options: trip_count, total_revenue, avg_fare, avg_tip, avg_distance, credit_card_rate, airport_trips"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of rows to return (default 10)"
                        }
                    },
                    "required": ["dimensions", "measures"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_context",
                "description": "Get business context and domain knowledge from the ontology. Use this to understand what concepts mean.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "concept": {
                            "type": "string",
                            "description": "The concept to look up: Manhattan, Brooklyn, Queens, JFKAirport, CreditCard, Cash, RushHour, etc."
                        }
                    },
                    "required": ["concept"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_measure_info",
                "description": "Get detailed information about a metric including how it's calculated and how to interpret it.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "measure_name": {
                            "type": "string",
                            "description": "The measure name: trip_count, total_revenue, avg_fare, avg_tip, avg_distance, etc."
                        }
                    },
                    "required": ["measure_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "explain_metric",
                "description": "Get explanation for why a metric has a certain value, with business context.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "metric": {
                            "type": "string",
                            "description": "The metric to explain"
                        },
                        "value": {
                            "type": "number",
                            "description": "The observed value"
                        },
                        "context": {
                            "type": "object",
                            "description": "Context like borough, zone, payment_type",
                            "additionalProperties": {"type": "string"}
                        },
                        "comparison_value": {
                            "type": "number",
                            "description": "Optional value to compare against"
                        }
                    },
                    "required": ["metric", "value"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "classify_trip",
                "description": "Classify a trip using ontology rules to determine its type (Airport, Commute, LongDistance, etc.)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "rate_code_id": {
                            "type": "integer",
                            "description": "Rate code (2=JFK, 3=Newark)"
                        },
                        "trip_distance": {
                            "type": "number",
                            "description": "Trip distance in miles"
                        },
                        "pickup_hour": {
                            "type": "integer",
                            "description": "Hour of pickup (0-23)"
                        },
                        "day_of_week": {
                            "type": "integer",
                            "description": "Day of week (0=Sunday, 6=Saturday)"
                        },
                        "pickup_location_id": {
                            "type": "integer",
                            "description": "Pickup zone ID"
                        },
                        "dropoff_location_id": {
                            "type": "integer",
                            "description": "Dropoff zone ID"
                        }
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_analysis_context",
                "description": "Get relevant ontology rules and insights for a type of analysis (revenue, tips, demand, airport, time)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "analysis_type": {
                            "type": "string",
                            "enum": ["revenue", "tips", "demand", "airport", "time"],
                            "description": "Type of analysis to get context for"
                        }
                    },
                    "required": ["analysis_type"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "list_tables",
                "description": "List all tables in the NYC Taxi database from OpenMetadata catalog. Returns table names and basic info.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_table_schema",
                "description": "Get detailed schema for a table including all columns, their types, and descriptions from OpenMetadata.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "Name of the table: trips, zones, payment_types, or rate_codes"
                        }
                    },
                    "required": ["table_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_glossary_terms",
                "description": "Get business glossary terms from OpenMetadata. These define business meanings for metrics and dimensions.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "enum": ["all", "metrics", "dimensions", "concepts"],
                            "description": "Category of terms to retrieve"
                        }
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_metadata",
                "description": "Search across technical metadata (tables, columns) and glossary terms for a keyword.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "keyword": {
                            "type": "string",
                            "description": "Keyword to search for in table names, column names, and descriptions"
                        }
                    },
                    "required": ["keyword"]
                }
            }
        }
    ]

    def __init__(self):
        """Initialize the agent with semantic layer, ontology, and technical layer."""
        self.client = None
        self.deployment = None
        self.semantic_layer = None
        self.ontology = None
        self.technical_layer = None

        # Initialize components
        self._init_technical_layer()
        self._init_semantic_layer()
        self._init_ontology()
        self._init_azure_openai()

    def _init_technical_layer(self):
        """Initialize the technical layer for OpenMetadata queries."""
        try:
            from unified_layer import TechnicalLayer
            self.technical_layer = TechnicalLayer()
            if self.technical_layer.is_available:
                print("Technical layer initialized (OpenMetadata)")
            else:
                print("Technical layer: OpenMetadata not available")
        except Exception as e:
            print(f"Warning: Could not initialize technical layer: {e}")

    def _init_semantic_layer(self):
        """Initialize the semantic layer for data queries."""
        try:
            from semantic_layer import SemanticLayer
            self.semantic_layer = SemanticLayer()
            print("Semantic layer initialized (PostgreSQL backend)")
        except Exception as e:
            print(f"Warning: Could not initialize semantic layer: {e}")
            print("Data queries will not be available")

    def _init_ontology(self):
        """Initialize the ontology layer for business context."""
        try:
            from ontology_layer import OntologyLayer
            self.ontology = OntologyLayer()
            print("Ontology layer initialized")
        except Exception as e:
            print(f"Warning: Could not initialize ontology: {e}")
            print("Business context will be limited")

    def _init_azure_openai(self):
        """Initialize Azure OpenAI client."""
        try:
            from openai import AzureOpenAI

            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            # Support multiple env var names for deployment
            self.deployment = (
                os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") or
                os.getenv("AZURE_OPENAI_DEPLOYMENT") or
                "gpt-4"
            )
            api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

            if not endpoint or not api_key:
                print("Azure OpenAI credentials not configured")
                print("Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY")
                print("Running in offline mode (ontology-only)")
                return

            self.client = AzureOpenAI(
                azure_endpoint=endpoint,
                api_key=api_key,
                api_version=api_version
            )
            print(f"Azure OpenAI initialized (deployment: {self.deployment})")

        except ImportError:
            print("openai package not installed. Running in offline mode")
        except Exception as e:
            print(f"Could not initialize Azure OpenAI: {e}")
            print("Running in offline mode")

    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool and return results."""

        if tool_name == "query_metrics":
            if self.semantic_layer is None:
                return {"error": "Semantic layer not available"}

            dimensions = arguments.get("dimensions", [])
            measures = arguments.get("measures", [])
            limit = arguments.get("limit", 10)

            # Map common names to actual dimension/measure names
            dim_map = {
                "borough": "pickup_zone.borough",
                "zone": "pickup_zone.zone_name",
                "zone_name": "pickup_zone.zone_name"
            }
            dimensions = [dim_map.get(d, d) for d in dimensions]

            result = self.semantic_layer.query(
                dimensions=dimensions,
                measures=measures,
                order_by=[(measures[0], "desc")] if measures else None,
                limit=limit
            )
            return result

        elif tool_name == "get_context":
            if self.ontology is None:
                return {"error": "Ontology not available"}

            concept = arguments.get("concept", "")
            context = self.ontology.get_concept_context(concept)

            if not context:
                # Try zone instances
                zones = self.ontology.get_zone_instances()
                for zone in zones:
                    if zone.get("name", "").lower() == concept.lower():
                        return zone

                # Try looking up by partial match
                for zone in zones:
                    if concept.lower() in zone.get("label", "").lower():
                        return zone

            return context if context else {"message": f"No context found for '{concept}'"}

        elif tool_name == "get_measure_info":
            measure_name = arguments.get("measure_name", "")

            # Measure definitions with business context
            measure_info = {
                "trip_count": {
                    "name": "trip_count",
                    "description": "Total number of taxi trips",
                    "calculation": "COUNT(*)",
                    "unit": "trips",
                    "business_context": "Volume indicator. Manhattan has ~90% of all trips.",
                    "interpretation": "Higher counts indicate busier areas/times."
                },
                "total_revenue": {
                    "name": "total_revenue",
                    "description": "Sum of fare + tip amounts",
                    "calculation": "SUM(fare_amount + tip_amount)",
                    "unit": "USD",
                    "business_context": "Primary business metric. Airport trips have higher per-trip revenue.",
                    "interpretation": "Revenue = volume * average fare. Can increase either."
                },
                "avg_fare": {
                    "name": "avg_fare",
                    "description": "Average fare per trip",
                    "calculation": "AVG(fare_amount)",
                    "unit": "USD",
                    "business_context": "Reflects trip distance and rate type. JFK has $52 flat rate.",
                    "interpretation": "Higher in areas with longer trips or airport service."
                },
                "avg_tip": {
                    "name": "avg_tip",
                    "description": "Average tip per trip",
                    "calculation": "AVG(tip_amount)",
                    "unit": "USD",
                    "business_context": "IMPORTANT: Cash tips not recorded. Only credit card tips are in data.",
                    "interpretation": "Lower tips in outer boroughs reflect demographics, not service quality.",
                    "varies_by": {
                        "payment_type": "Cash tips not recorded - exclude from tip analysis",
                        "borough": "Manhattan tips higher due to tourists and business travelers",
                        "zone_type": "Airport and tourist zones have higher tips"
                    }
                },
                "avg_distance": {
                    "name": "avg_distance",
                    "description": "Average trip distance in miles",
                    "calculation": "AVG(trip_distance)",
                    "unit": "miles",
                    "business_context": "Indicates trip type. Short trips (<2mi) common in Manhattan.",
                    "interpretation": "Airport trips average 10-20 miles. Manhattan trips average 2-3 miles."
                },
                "credit_card_rate": {
                    "name": "credit_card_rate",
                    "description": "Percentage of trips paid by credit card",
                    "calculation": "AVG(payment_type = 1)",
                    "unit": "ratio (0-1)",
                    "business_context": "Higher in Manhattan (~70%). Important for tip analysis validity.",
                    "interpretation": "Low credit card rate means tip data is less representative."
                }
            }

            return measure_info.get(measure_name, {
                "name": measure_name,
                "message": "Measure found in semantic layer but no additional context available"
            })

        elif tool_name == "explain_metric":
            metric = arguments.get("metric", "")
            value = arguments.get("value", 0)
            context = arguments.get("context", {})
            comparison_value = arguments.get("comparison_value")

            explanations = []

            # Get measure info
            measure_info = self._execute_tool("get_measure_info", {"measure_name": metric})
            if measure_info.get("description"):
                explanations.append(f"{measure_info['description']}: ${value:.2f}" if "USD" in measure_info.get("unit", "") else f"{measure_info['description']}: {value}")

            # Add borough context
            if context.get("borough") and self.ontology:
                borough_ctx = self.ontology.get_concept_context(context["borough"])
                if borough_ctx and borough_ctx.get("business_context"):
                    explanations.append(f"\nBorough context: {borough_ctx['business_context']}")

            # Add varies_by factors
            if measure_info.get("varies_by"):
                for factor, explanation in measure_info["varies_by"].items():
                    if factor in context or factor == "payment_type":
                        explanations.append(f"\n{factor.title()} effect: {explanation}")

            # Add comparison
            if comparison_value is not None:
                diff = value - comparison_value
                direction = "higher" if diff > 0 else "lower"
                explanations.append(f"\nThis is ${abs(diff):.2f} {direction} than the comparison value (${comparison_value:.2f})")

            # Add interpretation guidance
            if measure_info.get("interpretation"):
                explanations.append(f"\nInterpretation: {measure_info['interpretation']}")

            return {"explanation": " ".join(explanations)}

        elif tool_name == "classify_trip":
            if self.ontology is None:
                return {"error": "Ontology not available"}

            classifications = self.ontology.classify_trip(
                rate_code_id=arguments.get("rate_code_id"),
                trip_distance=arguments.get("trip_distance"),
                pickup_hour=arguments.get("pickup_hour"),
                day_of_week=arguments.get("day_of_week"),
                pickup_location_id=arguments.get("pickup_location_id"),
                dropoff_location_id=arguments.get("dropoff_location_id")
            )

            # Get context for each classification
            result = {
                "classifications": classifications,
                "details": []
            }

            for trip_type in classifications:
                trip_types = self.ontology.get_trip_types()
                for tt in trip_types:
                    if tt["name"] == trip_type:
                        result["details"].append({
                            "type": tt["label"],
                            "context": tt.get("business_context", ""),
                            "fare_range": tt.get("avg_fare_range", "")
                        })
                        break

            return result

        elif tool_name == "get_analysis_context":
            if self.ontology is None:
                return {"error": "Ontology not available"}

            analysis_type = arguments.get("analysis_type", "")
            return self.ontology.get_context_for_analysis(analysis_type)

        elif tool_name == "list_tables":
            if self.technical_layer is None or not self.technical_layer.is_available:
                # Fallback to hardcoded info if OpenMetadata not available
                return {
                    "tables": [
                        {"name": "trips", "description": "NYC Yellow Taxi trip records", "columns": 20, "rows": "~2.76M"},
                        {"name": "zones", "description": "TLC taxi zone lookup", "columns": 4, "rows": 265},
                        {"name": "payment_types", "description": "Payment type codes", "columns": 2, "rows": 6},
                        {"name": "rate_codes", "description": "Rate code definitions", "columns": 2, "rows": 6}
                    ],
                    "source": "fallback (OpenMetadata not available)"
                }

            tables = self.technical_layer.get_all_tables()
            return {
                "tables": [
                    {
                        "name": t.get("name"),
                        "description": t.get("description", ""),
                        "fqn": t.get("fullyQualifiedName", "")
                    }
                    for t in tables
                ],
                "source": "OpenMetadata"
            }

        elif tool_name == "get_table_schema":
            table_name = arguments.get("table_name", "")

            # Fallback schema definitions
            fallback_schemas = {
                "trips": {
                    "name": "trips",
                    "description": "NYC Yellow Taxi trip records for January 2024",
                    "columns": [
                        {"name": "vendor_id", "type": "INTEGER", "description": "Taxi vendor (1=CMT, 2=VeriFone)"},
                        {"name": "pickup_datetime", "type": "TIMESTAMP", "description": "When the meter was engaged"},
                        {"name": "dropoff_datetime", "type": "TIMESTAMP", "description": "When the meter was disengaged"},
                        {"name": "passenger_count", "type": "INTEGER", "description": "Number of passengers"},
                        {"name": "trip_distance", "type": "DECIMAL", "description": "Trip distance in miles"},
                        {"name": "pickup_location_id", "type": "INTEGER", "description": "TLC zone where trip started"},
                        {"name": "dropoff_location_id", "type": "INTEGER", "description": "TLC zone where trip ended"},
                        {"name": "rate_code_id", "type": "INTEGER", "description": "Rate type (1=Standard, 2=JFK, 3=Newark, etc.)"},
                        {"name": "payment_type", "type": "INTEGER", "description": "Payment method (1=Credit, 2=Cash, 3=NoCharge, 4=Dispute)"},
                        {"name": "fare_amount", "type": "DECIMAL", "description": "Base fare from the meter"},
                        {"name": "tip_amount", "type": "DECIMAL", "description": "Tip amount (credit card only)"},
                        {"name": "tolls_amount", "type": "DECIMAL", "description": "Toll charges"},
                        {"name": "total_amount", "type": "DECIMAL", "description": "Total charge to passenger"},
                        {"name": "congestion_surcharge", "type": "DECIMAL", "description": "NYC congestion surcharge"},
                        {"name": "airport_fee", "type": "DECIMAL", "description": "Airport pickup fee"}
                    ]
                },
                "zones": {
                    "name": "zones",
                    "description": "TLC taxi zone lookup table",
                    "columns": [
                        {"name": "location_id", "type": "INTEGER", "description": "Unique zone identifier"},
                        {"name": "borough", "type": "VARCHAR", "description": "NYC borough name"},
                        {"name": "zone_name", "type": "VARCHAR", "description": "Zone name (e.g., JFK Airport, Midtown)"},
                        {"name": "service_zone", "type": "VARCHAR", "description": "Service zone category"}
                    ]
                },
                "payment_types": {
                    "name": "payment_types",
                    "description": "Payment type lookup table",
                    "columns": [
                        {"name": "payment_type_id", "type": "INTEGER", "description": "Payment type code"},
                        {"name": "description", "type": "VARCHAR", "description": "Payment type name"}
                    ]
                },
                "rate_codes": {
                    "name": "rate_codes",
                    "description": "Rate code lookup table",
                    "columns": [
                        {"name": "rate_code_id", "type": "INTEGER", "description": "Rate code"},
                        {"name": "description", "type": "VARCHAR", "description": "Rate type name"}
                    ]
                }
            }

            if self.technical_layer is None or not self.technical_layer.is_available:
                if table_name in fallback_schemas:
                    return {**fallback_schemas[table_name], "source": "fallback"}
                return {"error": f"Table '{table_name}' not found"}

            # Try OpenMetadata
            table_fqn = f"nyc_taxi_postgres.nyc_taxi.public.{table_name}"
            table_info = self.technical_layer.get_table(table_fqn)

            if not table_info:
                if table_name in fallback_schemas:
                    return {**fallback_schemas[table_name], "source": "fallback"}
                return {"error": f"Table '{table_name}' not found"}

            return {
                "name": table_info.get("name"),
                "description": table_info.get("description", ""),
                "columns": [
                    {
                        "name": col.get("name"),
                        "type": col.get("dataType"),
                        "description": col.get("description", "")
                    }
                    for col in table_info.get("columns", [])
                ],
                "source": "OpenMetadata"
            }

        elif tool_name == "get_glossary_terms":
            category = arguments.get("category", "all")

            # Fallback glossary
            fallback_glossary = {
                "metrics": [
                    {"name": "Trip Revenue", "definition": "fare_amount + tip_amount for a trip"},
                    {"name": "Trip Count", "definition": "Number of completed taxi trips"},
                    {"name": "Average Fare", "definition": "Mean fare_amount per trip"},
                    {"name": "Average Tip", "definition": "Mean tip_amount per trip (credit card only)"},
                    {"name": "Total Amount", "definition": "Full charge including all fees"}
                ],
                "dimensions": [
                    {"name": "Borough", "definition": "NYC administrative district (Manhattan, Brooklyn, etc.)"},
                    {"name": "Pickup Zone", "definition": "TLC-defined taxi zone where trip started"},
                    {"name": "Payment Method", "definition": "How passenger paid (Credit Card, Cash, etc.)"},
                    {"name": "Rate Type", "definition": "Fare calculation method (Standard, JFK Flat, etc.)"}
                ],
                "concepts": [
                    {"name": "Airport Trip", "definition": "Trip to/from JFK, LaGuardia, or Newark airports"},
                    {"name": "Cash Payment", "definition": "Payment in cash - tips NOT recorded"},
                    {"name": "Peak Hours", "definition": "7-9 AM and 5-8 PM on weekdays"},
                    {"name": "Long Distance Trip", "definition": "Trip over 10 miles"}
                ]
            }

            if self.technical_layer is None or not self.technical_layer.is_available:
                if category == "all":
                    return {**fallback_glossary, "source": "fallback"}
                return {category: fallback_glossary.get(category, []), "source": "fallback"}

            # Try OpenMetadata
            terms = self.technical_layer.get_glossary_terms()
            if not terms:
                if category == "all":
                    return {**fallback_glossary, "source": "fallback"}
                return {category: fallback_glossary.get(category, []), "source": "fallback"}

            result = {"metrics": [], "dimensions": [], "concepts": [], "source": "OpenMetadata"}
            for term in terms:
                fqn = term.get("fullyQualifiedName", "")
                item = {
                    "name": term.get("displayName", term.get("name")),
                    "definition": term.get("description", "")
                }
                if "Metrics" in fqn:
                    result["metrics"].append(item)
                elif "Dimensions" in fqn:
                    result["dimensions"].append(item)
                elif "BusinessConcepts" in fqn:
                    result["concepts"].append(item)

            if category == "all":
                return result
            return {category: result.get(category, []), "source": "OpenMetadata"}

        elif tool_name == "search_metadata":
            keyword = arguments.get("keyword", "").lower()

            results = {
                "tables": [],
                "columns": [],
                "glossary_terms": [],
                "ontology_concepts": []
            }

            # Search in semantic layer dimensions/measures
            if self.semantic_layer:
                for dim in self.semantic_layer.available_dimensions:
                    if keyword in dim.lower():
                        results["columns"].append({"name": dim, "type": "dimension"})
                for measure in self.semantic_layer.available_measures:
                    if keyword in measure.lower():
                        results["columns"].append({"name": measure, "type": "measure"})

            # Search in ontology
            if self.ontology:
                for cls in self.ontology.get_classes():
                    label = cls.get("label") or ""
                    comment = cls.get("comment") or ""
                    if keyword in label.lower() or keyword in comment.lower():
                        results["ontology_concepts"].append({
                            "name": label,
                            "type": "class",
                            "comment": comment[:100] if comment else ""
                        })

            # Search in technical layer
            if self.technical_layer and self.technical_layer.is_available:
                for term in self.technical_layer.get_glossary_terms():
                    name = term.get("displayName", "").lower()
                    desc = term.get("description", "").lower()
                    if keyword in name or keyword in desc:
                        results["glossary_terms"].append({
                            "name": term.get("displayName"),
                            "definition": term.get("description", "")[:100]
                        })

            return results

        return {"error": f"Unknown tool: {tool_name}"}

    def _ask_offline(self, question: str) -> AgentResponse:
        """Answer using only ontology (no LLM)."""
        question_lower = question.lower()

        # Pattern matching for common questions
        if any(word in question_lower for word in ["revenue", "money", "earn"]):
            if self.semantic_layer:
                result = self.semantic_layer.get_revenue_by_borough(limit=5)
                data = result.get("data", [])

                answer_parts = ["Revenue by Borough:"]
                for row in data:
                    borough = row.get("pickup_zone_borough", "Unknown")
                    revenue = row.get("total_revenue", 0)
                    trips = row.get("trip_count", 0)
                    answer_parts.append(f"- {borough}: ${revenue:,.2f} ({trips:,} trips)")

                return AgentResponse(
                    question=question,
                    answer="\n".join(answer_parts),
                    data=data,
                    tools_used=["query_metrics"]
                )

        if any(word in question_lower for word in ["tip", "tips"]):
            if self.semantic_layer:
                result = self.semantic_layer.get_tips_by_borough(limit=5)
                data = result.get("data", [])

                answer_parts = ["Tips by Borough (credit card only):"]
                for row in data:
                    borough = row.get("pickup_zone_borough", "Unknown")
                    avg_tip = row.get("avg_tip", 0)
                    cc_rate = row.get("credit_card_rate", 0)
                    answer_parts.append(f"- {borough}: ${avg_tip:.2f} avg tip ({cc_rate*100:.1f}% credit card)")

                answer_parts.append("\nNote: Cash tips are not recorded in the data.")

                return AgentResponse(
                    question=question,
                    answer="\n".join(answer_parts),
                    data=data,
                    tools_used=["query_metrics", "get_context"]
                )

        if any(word in question_lower for word in ["airport", "jfk", "laguardia"]):
            context = self.ontology.get_context_for_analysis("airport") if self.ontology else {}

            if self.semantic_layer:
                result = self.semantic_layer.get_airport_analysis()
                data = result.get("data", [])

                answer_parts = ["Airport Trip Analysis:"]
                for row in data:
                    rate_code = row.get("rate_code_id", 0)
                    trips = row.get("trip_count", 0)
                    avg_fare = row.get("avg_fare", 0)

                    rate_name = {1: "Standard", 2: "JFK Flat Rate", 3: "Newark"}.get(rate_code, f"Rate {rate_code}")
                    answer_parts.append(f"- {rate_name}: {trips:,} trips, ${avg_fare:.2f} avg fare")

                if context.get("business_insights"):
                    answer_parts.append("\nKey Insights:")
                    for insight in context["business_insights"]:
                        answer_parts.append(f"- {insight}")

                return AgentResponse(
                    question=question,
                    answer="\n".join(answer_parts),
                    data=data,
                    tools_used=["query_metrics", "get_analysis_context"]
                )

        # Default: return ontology summary
        if self.ontology:
            summary = self.ontology.summarize()
            return AgentResponse(
                question=question,
                answer=f"I'm running in offline mode (no LLM). I can answer basic questions about revenue, tips, and airports.\n\nOntology has {summary['classes']} classes, {summary['trip_types']} trip types, {summary['inference_rules']} inference rules.",
                tools_used=[]
            )

        return AgentResponse(
            question=question,
            answer="Running in offline mode with limited capabilities.",
            tools_used=[]
        )

    def ask(self, question: str, verbose: bool = False) -> AgentResponse:
        """
        Ask the agent a question about NYC taxi data.

        Args:
            question: Natural language question
            verbose: Print reasoning steps if True

        Returns:
            AgentResponse with answer, data, and reasoning
        """
        # Offline mode if no LLM
        if self.client is None:
            return self._ask_offline(question)

        # Build messages
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": question}
        ]

        reasoning_steps = []
        tools_used = []
        collected_data = []

        # Agentic loop (max 5 iterations)
        for iteration in range(5):
            if verbose:
                print(f"\n--- Iteration {iteration + 1} ---")

            try:
                response = self.client.chat.completions.create(
                    model=self.deployment,
                    messages=messages,
                    tools=self.TOOLS,
                    tool_choice="auto"
                )
            except Exception as e:
                return AgentResponse(
                    question=question,
                    answer=f"Error calling LLM: {str(e)}",
                    error=str(e),
                    tools_used=tools_used
                )

            assistant_message = response.choices[0].message

            # If no tool calls, we're done
            if not assistant_message.tool_calls:
                return AgentResponse(
                    question=question,
                    answer=assistant_message.content or "No answer generated",
                    data=collected_data if collected_data else None,
                    reasoning_steps=reasoning_steps,
                    tools_used=tools_used
                )

            # Add assistant message to history
            messages.append({
                "role": "assistant",
                "content": assistant_message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in assistant_message.tool_calls
                ]
            })

            # Execute each tool call
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name

                try:
                    arguments = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    arguments = {}

                if verbose:
                    print(f"Tool: {tool_name}")
                    print(f"Args: {json.dumps(arguments, indent=2)}")

                # Execute tool
                result = self._execute_tool(tool_name, arguments)

                tools_used.append(tool_name)
                reasoning_steps.append(f"Called {tool_name} with {arguments}")

                # Collect data from query_metrics
                if tool_name == "query_metrics" and isinstance(result, dict):
                    if result.get("data"):
                        collected_data.extend(result["data"])

                if verbose:
                    print(f"Result: {json.dumps(result, indent=2, default=str)[:500]}...")

                # Add tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, default=str)
                })

        # Max iterations reached
        return AgentResponse(
            question=question,
            answer="Maximum iterations reached. Please try a simpler question.",
            reasoning_steps=reasoning_steps,
            tools_used=tools_used
        )

    def summary(self) -> Dict[str, Any]:
        """Get a summary of agent capabilities."""
        return {
            "llm_available": self.client is not None,
            "llm_deployment": self.deployment,
            "technical_layer_available": self.technical_layer is not None and self.technical_layer.is_available,
            "semantic_layer_available": self.semantic_layer is not None,
            "ontology_available": self.ontology is not None,
            "available_tools": [t["function"]["name"] for t in self.TOOLS],
            "semantic_dimensions": self.semantic_layer.available_dimensions if self.semantic_layer else [],
            "semantic_measures": self.semantic_layer.available_measures if self.semantic_layer else [],
            "ontology_summary": self.ontology.summarize() if self.ontology else {}
        }


# =============================================================================
# CLI Demo
# =============================================================================

def main():
    """Demo the NYC Taxi Agent."""
    print("=" * 70)
    print("NYC TAXI AI AGENT")
    print("=" * 70)

    # Initialize agent
    agent = NYCTaxiAgent()

    # Show capabilities
    print("\n--- Agent Capabilities ---")
    summary = agent.summary()
    print(f"LLM Available: {summary['llm_available']}")
    if summary['llm_available']:
        print(f"LLM Deployment: {summary['llm_deployment']}")
    print(f"Semantic Layer: {summary['semantic_layer_available']}")
    print(f"Ontology: {summary['ontology_available']}")
    print(f"Tools: {', '.join(summary['available_tools'])}")

    # Demo questions
    demo_questions = [
        "What is the total revenue by borough?",
        "Which zones have the highest trip count?",
        "Why are tips lower in Brooklyn compared to Manhattan?",
    ]

    print("\n" + "=" * 70)
    print("DEMO QUESTIONS")
    print("=" * 70)

    for question in demo_questions:
        print(f"\n>>> {question}")
        print("-" * 50)

        response = agent.ask(question, verbose=False)
        print(response.answer)

        if response.tools_used:
            print(f"\n[Tools used: {', '.join(response.tools_used)}]")

    print("\n" + "=" * 70)
    print("AGENT DEMO COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
