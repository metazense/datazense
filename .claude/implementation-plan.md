# Implementation Plan: Mini Fabric IQ / Palantir AIP

## Vision

Build a small-scale proof-of-concept that demonstrates the **Microsoft Fabric IQ** and **Palantir AIP** pattern:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     INTELLIGENT SEMANTIC LAYER                          │
│                     (Mini Fabric IQ / Palantir AIP)                     │
│                                                                         │
│   User: "What is total revenue by borough and why is Manhattan highest?"│
│                                    │                                    │
│                                    ▼                                    │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                        AI AGENT                                  │  │
│   │   • Understands natural language questions                       │  │
│   │   • Calls tools to get data (semantic layer)                    │  │
│   │   • Calls tools to get context (ontology)                       │  │
│   │   • Reasons and explains (LLM)                                  │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                    │              │              │                      │
│         ┌─────────┴──┐    ┌──────┴──────┐    ┌──┴───────────┐         │
│         ▼            ▼    ▼             ▼    ▼              ▼         │
│   ┌──────────┐ ┌──────────┐ ┌───────────────┐ ┌──────────────┐       │
│   │ Semantic │ │ Ontology │ │  OpenMetadata │ │  PostgreSQL  │       │
│   │  Layer   │ │  (OWL)   │ │   (Catalog)   │ │   (Data)     │       │
│   │          │ │          │ │               │ │              │       │
│   │ COMPUTES │ │ EXPLAINS │ │  DOCUMENTS    │ │  STORES      │       │
│   │ metrics  │ │ why      │ │  what exists  │ │  2.76M trips │       │
│   └──────────┘ └──────────┘ └───────────────┘ └──────────────┘       │
│                                                                         │
│   Answer: "Manhattan generated $54M (90% of total revenue).            │
│   This dominance is due to:                                            │
│   • High business/tourist density (Midtown, Financial District)        │
│   • Limited parking drives taxi demand                                 │
│   • Airport connections (JFK/LGA flat rates)                          │
│   Brooklyn's $3M (5%) reflects residential character with lower        │
│   taxi usage and shorter average trips."                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Current State Assessment

### What Exists ✅
- PostgreSQL with 2.76M taxi trips (port 5433)
- OpenMetadata 1.7.1 with tables cataloged (port 8585)
- OpenMetadata Glossary with 18 business terms
- OWL Ontology with 28 classes, 6 relationships, 5 basic rules
- Python modules: `ontology_layer.py`, `unified_layer.py`
- Azure OpenAI credentials configured

### What's Missing ❌
- **Semantic Layer**: No computation engine (OpenMetadata Glossary is just text)
- **AI Agent**: No LLM integration that uses tools
- **Ontology Richness**: Missing Trip types, Zone types, instances, inference rules
- **Integration**: Layers exist but aren't connected to answer questions

---

## Phase 7: Add Semantic Layer (boring-semantic-layer)

### 7.1 Install Dependencies
```bash
uv add boring-semantic-layer "ibis-framework[postgres]" rdflib
```

**Files to create:**
- `src/semantic_layer.py` - PostgreSQL-backed semantic layer
- `semantic_model.yml` - Metric and dimension definitions

### 7.2 Create Semantic Model YAML

```yaml
# semantic_model.yml
zones:
  table: zones_tbl
  primary_key: location_id

  dimensions:
    location_id: _.location_id
    borough: _.borough
    zone_name: _.zone_name
    service_zone: _.service_zone

  measures:
    zone_count: _.count()

trips:
  table: trips_tbl
  time_dimension: pickup_datetime

  dimensions:
    # Time dimensions
    pickup_datetime: _.pickup_datetime
    dropoff_datetime: _.dropoff_datetime
    pickup_hour: _.pickup_datetime.hour()
    pickup_day_of_week: _.pickup_datetime.day_of_week()

    # Trip attributes
    passenger_count: _.passenger_count
    trip_distance: _.trip_distance

    # Foreign keys (for joins)
    vendor_id: _.vendor_id
    rate_code_id: _.rate_code_id
    payment_type: _.payment_type

  measures:
    # Volume metrics
    trip_count: _.count()

    # Revenue metrics
    total_revenue: (_.fare_amount + _.tip_amount).sum()
    total_fare: _.fare_amount.sum()
    total_tips: _.tip_amount.sum()
    avg_fare: _.fare_amount.mean()
    avg_tip: _.tip_amount.mean()
    avg_total: _.total_amount.mean()

    # Distance/Time metrics
    avg_distance: _.trip_distance.mean()
    total_distance: _.trip_distance.sum()

    # Derived metrics
    tip_percentage: (_.tip_amount / _.fare_amount).mean()
    avg_fare_per_mile: (_.fare_amount / _.trip_distance).mean()

    # Payment analysis (credit card trips only for tip analysis)
    credit_card_trips: (_.payment_type == 1).sum()
    cash_trips: (_.payment_type == 2).sum()
    credit_card_rate: (_.payment_type == 1).mean()

    # Airport trips (rate_code 2 or 3)
    airport_trips: ((_.rate_code_id == 2) | (_.rate_code_id == 3)).sum()
    airport_trip_rate: ((_.rate_code_id == 2) | (_.rate_code_id == 3)).mean()

  joins:
    pickup_zone:
      model: zones
      type: one
      with: _.pickup_location_id
    dropoff_zone:
      model: zones
      type: one
      with: _.dropoff_location_id

payment_types:
  table: payment_types_tbl
  primary_key: payment_type_id

  dimensions:
    payment_type_id: _.payment_type_id
    description: _.description

  measures:
    type_count: _.count()

rate_codes:
  table: rate_codes_tbl
  primary_key: rate_code_id

  dimensions:
    rate_code_id: _.rate_code_id
    description: _.description

  measures:
    code_count: _.count()
```

### 7.3 Create Semantic Layer Python Module

```python
# src/semantic_layer.py
"""
Semantic Layer - Powered by boring-semantic-layer + Ibis + PostgreSQL

This module provides the COMPUTATION layer that actually executes queries
and returns real data. It's the "WHAT" layer in the architecture.
"""

import os
import ibis
from pathlib import Path
from typing import Optional
from boring_semantic_layer import SemanticModel
from dotenv import load_dotenv

load_dotenv()


class SemanticLayer:
    """PostgreSQL-backed semantic layer using boring-semantic-layer."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5433,
        database: str = "nyc_taxi",
        user: str = "taxi_user",
        password: str = "taxi_password",
        yaml_path: Optional[str] = None
    ):
        # Connect to PostgreSQL via Ibis
        self.con = ibis.postgres.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )

        # Register tables
        self.tables = {
            "trips_tbl": self.con.table("trips"),
            "zones_tbl": self.con.table("zones"),
            "payment_types_tbl": self.con.table("payment_types"),
            "rate_codes_tbl": self.con.table("rate_codes"),
        }

        # Load semantic model
        if yaml_path is None:
            yaml_path = Path(__file__).parent.parent / "semantic_model.yml"

        self.models = SemanticModel.from_yaml(str(yaml_path), tables=self.tables)

        # Shortcuts
        self.trips = self.models["trips"]
        self.zones = self.models["zones"]

    @property
    def available_dimensions(self) -> list[str]:
        """Get all available dimensions including joined ones."""
        dims = list(self.trips.available_dimensions)
        # Add joined dimensions
        dims.extend([
            "pickup_zone.borough",
            "pickup_zone.zone_name",
            "pickup_zone.service_zone",
            "dropoff_zone.borough",
            "dropoff_zone.zone_name",
        ])
        return dims

    @property
    def available_measures(self) -> list[str]:
        """Get all available measures."""
        return list(self.trips.available_measures)

    def query(
        self,
        dimensions: list[str],
        measures: list[str],
        filters: Optional[dict] = None,
        order_by: Optional[list] = None,
        limit: Optional[int] = None
    ) -> dict:
        """
        Execute a semantic query and return results.

        Args:
            dimensions: List of dimensions to group by
            measures: List of measures to compute
            filters: Optional filters (not yet implemented in BSL)
            order_by: Optional ordering [(field, 'asc'|'desc'), ...]
            limit: Optional row limit

        Returns:
            Dict with 'data' (list of dicts) and 'columns' (list of names)
        """
        # Build query
        expr = self.trips.query(
            dimensions=dimensions,
            measures=measures,
            order_by=order_by,
            limit=limit
        )

        # Execute and convert to dict
        df = expr.execute()

        return {
            "data": df.to_dict(orient="records"),
            "columns": list(df.columns),
            "row_count": len(df)
        }

    def get_revenue_by_borough(self) -> dict:
        """Convenience method for common query."""
        return self.query(
            dimensions=["pickup_zone.borough"],
            measures=["trip_count", "total_revenue", "avg_fare", "avg_tip"],
            order_by=[("total_revenue", "desc")]
        )

    def get_tips_by_borough(self) -> dict:
        """Get tip metrics by borough (credit card only context needed)."""
        return self.query(
            dimensions=["pickup_zone.borough"],
            measures=["trip_count", "avg_tip", "tip_percentage", "credit_card_rate"],
            order_by=[("avg_tip", "desc")]
        )


# Test if run directly
if __name__ == "__main__":
    print("Testing Semantic Layer with PostgreSQL...")

    sl = SemanticLayer()

    print(f"\nAvailable dimensions: {sl.available_dimensions}")
    print(f"\nAvailable measures: {sl.available_measures}")

    print("\n=== Revenue by Borough ===")
    result = sl.get_revenue_by_borough()
    for row in result["data"]:
        print(f"  {row}")

    print("\n=== Tips by Borough ===")
    result = sl.get_tips_by_borough()
    for row in result["data"]:
        print(f"  {row}")
```

### 7.4 Verification
- [ ] `uv run python src/semantic_layer.py` returns actual data
- [ ] Queries execute against PostgreSQL (check logs)
- [ ] All measures compute correctly

---

## Phase 8: Enrich Ontology

### 8.1 Add Missing Classes

Add to `ontology/nyc_taxi.ttl`:

```turtle
# =============================================================================
# TRIP SUBCLASSES (for classification)
# =============================================================================

:AirportTrip a owl:Class ;
    rdfs:subClassOf :Trip ;
    rdfs:label "Airport Trip" ;
    rdfs:comment "Trip starting or ending at an airport zone (JFK, LaGuardia, Newark)" ;
    :classificationRule "rate_code_id IN (2, 3) OR pickup/dropoff zone is Airport" ;
    :businessContext "Higher tips expected (15-20%), often has luggage, may have flat rate" .

:CommuteTrip a owl:Class ;
    rdfs:subClassOf :Trip ;
    rdfs:label "Commute Trip" ;
    rdfs:comment "Rush hour trip from residential to business area" ;
    :classificationRule "7-9 AM or 5-7 PM weekday AND residential→business" ;
    :businessContext "Time-sensitive, recurring pattern, good shared ride candidate" .

:LongDistanceTrip a owl:Class ;
    rdfs:subClassOf :Trip ;
    rdfs:label "Long Distance Trip" ;
    rdfs:comment "Trip over 10 miles" ;
    :classificationRule "trip_distance > 10" ;
    :businessContext "Higher revenue per trip, often to/from airports or outer boroughs" .

# =============================================================================
# ZONE TYPE SUBCLASSES
# =============================================================================

:Airport a owl:Class ;
    rdfs:subClassOf :Location ;
    rdfs:label "Airport Zone" ;
    rdfs:comment "Zone serving JFK, LaGuardia, or Newark airports" ;
    :businessContext "Special fare rules, high tourist traffic, flight schedule driven demand" .

:BusinessDistrict a owl:Class ;
    rdfs:subClassOf :Location ;
    rdfs:label "Business District" ;
    rdfs:comment "Commercial/office zone with high weekday demand" ;
    :businessContext "Rush hour peaks, expense account trips, good tip rates" .

:ResidentialArea a owl:Class ;
    rdfs:subClassOf :Location ;
    rdfs:label "Residential Area" ;
    rdfs:comment "Primarily residential zone" ;
    :businessContext "Morning pickups to business, evening dropoffs from business" .

:TouristArea a owl:Class ;
    rdfs:subClassOf :Location ;
    rdfs:label "Tourist Area" ;
    rdfs:comment "High tourist traffic zone" ;
    :businessContext "Higher tip rates, airport connections, weekend peaks" .

:TransitHub a owl:Class ;
    rdfs:subClassOf :Location ;
    rdfs:label "Transit Hub" ;
    rdfs:comment "Major transit station zone (Penn Station, Grand Central)" ;
    :businessContext "High volume, short trips, commuter patterns" .

# =============================================================================
# TIME CONTEXT CLASSES
# =============================================================================

:TimeContext a owl:Class ;
    rdfs:label "Time Context" ;
    rdfs:comment "Temporal context affecting demand and patterns" .

:RushHour a owl:Class ;
    rdfs:subClassOf :TimeContext ;
    rdfs:label "Rush Hour" ;
    rdfs:comment "Peak commute: 7-9 AM and 5-7 PM weekdays" ;
    :businessContext "High demand, longer trips due to traffic, surge pricing" .

:OffPeak a owl:Class ;
    rdfs:subClassOf :TimeContext ;
    rdfs:label "Off-Peak" ;
    rdfs:comment "Non-rush weekday hours" ;
    :businessContext "Moderate demand, normal pricing, faster trips" .

:NightTime a owl:Class ;
    rdfs:subClassOf :TimeContext ;
    rdfs:label "Night Time" ;
    rdfs:comment "10 PM - 6 AM" ;
    :businessContext "Entertainment traffic, bar closings, safety considerations" .

:Weekend a owl:Class ;
    rdfs:subClassOf :TimeContext ;
    rdfs:label "Weekend" ;
    rdfs:comment "Saturday and Sunday" ;
    :businessContext "Leisure trips, tourist activity, later morning peaks" .
```

### 8.2 Add Zone Instances

```turtle
# =============================================================================
# ZONE INSTANCES
# =============================================================================

:JFKAirport a :Airport ;
    :locationId 132 ;
    :zoneName "JFK Airport" ;
    :inBorough :Queens ;
    rdfs:label "JFK Airport" ;
    :businessContext "Major international hub, $70 flat rate to Manhattan, high tip rates" .

:LaGuardiaAirport a :Airport ;
    :locationId 138 ;
    :zoneName "LaGuardia Airport" ;
    :inBorough :Queens ;
    rdfs:label "LaGuardia Airport" ;
    :businessContext "Domestic flights, metered fare, closer to Manhattan than JFK" .

:NewarkAirport a :Airport ;
    :locationId 1 ;
    :zoneName "Newark Airport" ;
    :inBorough :EWR ;
    rdfs:label "Newark Airport" ;
    :businessContext "New Jersey, highest fares due to distance and tolls" .

:MidtownCenter a :BusinessDistrict ;
    :locationId 161 ;
    :zoneName "Midtown Center" ;
    :inBorough :Manhattan ;
    rdfs:label "Midtown Center" ;
    :businessContext "Highest taxi density, office buildings, extreme rush hour congestion" .

:TimesSquare a :TouristArea, :BusinessDistrict ;
    :locationId 230 ;
    :zoneName "Times Sq/Theatre District" ;
    :inBorough :Manhattan ;
    rdfs:label "Times Square" ;
    :businessContext "Major tourist destination, generous tips, evening/weekend peaks" .

:FinancialDistrict a :BusinessDistrict ;
    :locationId 87 ;
    :zoneName "Financial District North" ;
    :inBorough :Manhattan ;
    rdfs:label "Financial District" ;
    :businessContext "Wall Street, heavy morning arrivals/evening departures, expense accounts" .

:PennStation a :TransitHub ;
    :locationId 186 ;
    :zoneName "Penn Station/Madison Sq West" ;
    :inBorough :Manhattan ;
    rdfs:label "Penn Station" ;
    :businessContext "Major rail hub, high volume, short trips to hotels/offices" .

:UpperEastSide a :ResidentialArea ;
    :locationId 236 ;
    :zoneName "Upper East Side North" ;
    :inBorough :Manhattan ;
    rdfs:label "Upper East Side" ;
    :businessContext "Affluent residential, high income, good tips, medical centers" .

# =============================================================================
# TIME CONTEXT INSTANCES
# =============================================================================

:MorningRush a :RushHour ;
    rdfs:label "Morning Rush" ;
    :hourRange "7-9" ;
    :dayType "weekday" ;
    :businessContext "Residential→Business flow, high demand, surge pricing likely" .

:EveningRush a :RushHour ;
    rdfs:label "Evening Rush" ;
    :hourRange "17-19" ;
    :dayType "weekday" ;
    :businessContext "Business→Residential flow, also airport trips" .

:Midday a :OffPeak ;
    rdfs:label "Midday" ;
    :hourRange "10-16" ;
    :dayType "weekday" ;
    :businessContext "Business meetings, errands, tourists, moderate demand" .

:LateNight a :NightTime ;
    rdfs:label "Late Night" ;
    :hourRange "22-4" ;
    :businessContext "Entertainment, bar closings, safety considerations" .
```

### 8.3 Add Inference Rules

```turtle
# =============================================================================
# INFERENCE RULES
# =============================================================================

:AirportTripClassification a :InferenceRule ;
    rdfs:label "Airport Trip Classification" ;
    :condition "rate_code_id IN (2, 3) OR pickup_zone.type = 'Airport' OR dropoff_zone.type = 'Airport'" ;
    :inference "Trip is AirportTrip" ;
    :businessContext "Expected tip 15-20%, likely has luggage, may have flat rate fare" .

:CommuteTripClassification a :InferenceRule ;
    rdfs:label "Commute Trip Classification" ;
    :condition "is_rush_hour AND pickup_zone.type = 'Residential' AND dropoff_zone.type = 'Business'" ;
    :inference "Trip is CommuteTrip" ;
    :businessContext "Likely recurring, time-sensitive, good shared ride candidate" .

:HighTipIndicator a :InferenceRule ;
    rdfs:label "High Tip Indicator" ;
    :condition "tip_amount / fare_amount > 0.20 AND payment_type = 1" ;
    :inference "High customer satisfaction" ;
    :businessContext "Good service quality, tourist/business traveler, or generous tipper" .

:LowTipNotServiceIssue a :InferenceRule ;
    rdfs:label "Low Tip Not Service Issue" ;
    :condition "tip_percentage < 0.12 AND pickup_zone.borough != 'Manhattan' AND dropoff_zone.borough != 'Manhattan'" ;
    :inference "Low tip reflects demographics, not service quality" ;
    :businessContext "Outer borough trips have lower tips due to income levels and local tipping norms" .

:ManhattanDominance a :InferenceRule ;
    rdfs:label "Manhattan Dominance Pattern" ;
    :condition "pickup_zone.borough = 'Manhattan'" ;
    :inference "Expect ~90% of all trips" ;
    :businessContext "Business density, tourist activity, limited parking drives taxi demand" .

:CashTipDataGap a :InferenceRule ;
    rdfs:label "Cash Tip Data Gap" ;
    :condition "payment_type = 2" ;
    :inference "Tip amount is unknown (recorded as $0)" ;
    :businessContext "Cash tips given directly to driver, not captured in data system" .
```

### 8.4 Update ontology_layer.py

Enhance `src/ontology_layer.py` to:
- Load new classes and instances
- Implement `classify_trip()` method
- Implement `explain_metric()` method
- Implement `get_instance_context()` method

---

## Phase 9: Build AI Agent

### 9.1 Create Agent Module

```python
# src/agent.py
"""
NYC Taxi AI Agent - Mini Fabric IQ

Combines:
- Semantic Layer (data queries via PostgreSQL)
- Ontology (knowledge, context, rules)
- LLM (Azure OpenAI for reasoning)

The agent can:
1. Query actual data using the semantic layer
2. Get business context from the ontology
3. Classify trips using ontology rules
4. Explain why metrics have certain values
5. Answer natural language questions about NYC taxi data
"""

import os
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

from semantic_layer import SemanticLayer
from ontology_layer import OntologyLayer


@dataclass
class AgentResponse:
    """Response from the agent."""
    question: str
    answer: str
    data: Optional[Dict] = None
    sources: List[str] = field(default_factory=list)
    reasoning: Optional[str] = None


class NYCTaxiAgent:
    """
    AI Agent for NYC Taxi data analysis.

    Implements the Fabric IQ / Palantir AIP pattern:
    - Semantic Layer for computation
    - Ontology for reasoning
    - LLM for natural language understanding
    """

    SYSTEM_PROMPT = """You are an expert NYC taxi data analyst with access to:

1. SEMANTIC LAYER (query_metrics tool):
   - Computes actual metrics from 2.76M taxi trips in PostgreSQL
   - Dimensions: pickup_zone.borough, pickup_zone.zone_name, pickup_datetime, etc.
   - Measures: trip_count, total_revenue, avg_fare, avg_tip, tip_percentage, etc.

2. ONTOLOGY (get_context, explain_metric, classify_trip tools):
   - Business knowledge about NYC taxi domain
   - Zone classifications (Airport, BusinessDistrict, Residential, Tourist)
   - Trip classifications (AirportTrip, CommuteTrip, LongDistance)
   - Inference rules explaining WHY metrics vary

AVAILABLE DIMENSIONS:
- pickup_zone.borough (Manhattan, Brooklyn, Queens, Bronx, Staten Island)
- pickup_zone.zone_name (e.g., "JFK Airport", "Midtown Center")
- pickup_zone.service_zone (Yellow Zone, Boro Zone, Airports)
- dropoff_zone.borough, dropoff_zone.zone_name
- pickup_datetime, pickup_hour, pickup_day_of_week
- payment_type, rate_code_id, vendor_id

AVAILABLE MEASURES:
- trip_count, total_revenue, total_fare, total_tips
- avg_fare, avg_tip, avg_total, avg_distance
- tip_percentage, avg_fare_per_mile
- credit_card_trips, cash_trips, credit_card_rate
- airport_trips, airport_trip_rate

CRITICAL RULES:
1. Always use query_metrics to get ACTUAL DATA - never make up numbers
2. Use get_context to understand WHY patterns exist
3. When analyzing tips, note that cash tips (payment_type=2) are NOT recorded
4. Low tips in outer boroughs reflect demographics, NOT service quality
5. Manhattan dominates (~90%) due to business/tourist density

When answering:
1. First query the data to get actual numbers
2. Then get ontology context to explain the patterns
3. Provide clear answer with both DATA and EXPLANATION
"""

    TOOLS = [
        {
            "type": "function",
            "function": {
                "name": "query_metrics",
                "description": "Query aggregated metrics from NYC taxi data. Returns actual computed values.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dimensions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Dimensions to group by (e.g., ['pickup_zone.borough'])"
                        },
                        "measures": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Measures to compute (e.g., ['trip_count', 'total_revenue'])"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Max rows to return (default: 10)"
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
                "description": "Get business context and knowledge about an entity from the ontology.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "entity_type": {
                            "type": "string",
                            "description": "Type: Borough, Zone, PaymentType, RateType, Trip, TimeContext"
                        },
                        "entity_name": {
                            "type": "string",
                            "description": "Name (e.g., 'Manhattan', 'JFK Airport', 'CreditCard')"
                        }
                    },
                    "required": ["entity_type", "entity_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "explain_metric",
                "description": "Get explanation for why a metric has a certain value using ontology rules.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "metric": {
                            "type": "string",
                            "description": "Metric name (e.g., 'avg_tip', 'total_revenue')"
                        },
                        "context": {
                            "type": "object",
                            "description": "Context like {borough: 'Brooklyn'} or {zone_type: 'Airport'}"
                        }
                    },
                    "required": ["metric"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "classify_trip",
                "description": "Classify a trip type using ontology rules.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pickup_zone": {"type": "string"},
                        "dropoff_zone": {"type": "string"},
                        "hour": {"type": "integer"},
                        "is_weekday": {"type": "boolean"},
                        "rate_code": {"type": "integer"}
                    },
                    "required": ["pickup_zone", "dropoff_zone"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_inference_rules",
                "description": "Get relevant inference rules for a topic.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "Topic like 'tips', 'revenue', 'airport', 'manhattan'"
                        }
                    },
                    "required": ["topic"]
                }
            }
        }
    ]

    def __init__(self):
        """Initialize agent with semantic layer, ontology, and LLM."""
        # Initialize layers
        self.semantic = SemanticLayer()
        self.ontology = OntologyLayer()

        # Initialize Azure OpenAI
        self.client = None
        self.deployment = None
        self._init_azure_openai()

    def _init_azure_openai(self):
        """Initialize Azure OpenAI client."""
        try:
            from openai import AzureOpenAI

            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
            self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")

            if not endpoint or not api_key:
                print("Warning: Azure OpenAI not configured. Running in offline mode.")
                return

            self.client = AzureOpenAI(
                azure_endpoint=endpoint,
                api_key=api_key,
                api_version=api_version
            )
            print(f"Connected to Azure OpenAI (deployment: {self.deployment})")

        except ImportError:
            print("openai package not installed. Running in offline mode.")

    def _execute_tool(self, tool_name: str, arguments: Dict) -> Any:
        """Execute a tool and return result."""

        if tool_name == "query_metrics":
            return self.semantic.query(
                dimensions=arguments.get("dimensions", []),
                measures=arguments.get("measures", []),
                limit=arguments.get("limit", 10)
            )

        elif tool_name == "get_context":
            return self.ontology.get_concept_context(
                arguments.get("entity_name", "")
            )

        elif tool_name == "explain_metric":
            return self.ontology.explain_metric(
                metric=arguments.get("metric", ""),
                context=arguments.get("context", {})
            )

        elif tool_name == "classify_trip":
            return self.ontology.classify_trip(
                pickup_zone=arguments.get("pickup_zone"),
                dropoff_zone=arguments.get("dropoff_zone"),
                hour=arguments.get("hour", 12),
                is_weekday=arguments.get("is_weekday", True),
                rate_code=arguments.get("rate_code", 1)
            )

        elif tool_name == "get_inference_rules":
            return self.ontology.get_rules_for_topic(
                arguments.get("topic", "")
            )

        return {"error": f"Unknown tool: {tool_name}"}

    def ask(self, question: str, verbose: bool = False) -> AgentResponse:
        """
        Ask a question about NYC taxi data.

        The agent will:
        1. Use LLM to understand the question
        2. Call semantic layer to get actual data
        3. Call ontology to get business context
        4. Generate an informed answer with data + explanation
        """
        if self.client is None:
            return self._ask_offline(question)

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": question}
        ]

        reasoning_steps = []
        collected_data = {}

        # Agentic loop
        max_iterations = 6
        for i in range(max_iterations):
            if verbose:
                print(f"\n--- Iteration {i+1} ---")

            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=messages,
                tools=self.TOOLS,
                tool_choice="auto"
            )

            assistant_message = response.choices[0].message

            # Check if done
            if not assistant_message.tool_calls:
                return AgentResponse(
                    question=question,
                    answer=assistant_message.content or "I couldn't generate an answer.",
                    data=collected_data if collected_data else None,
                    sources=list(collected_data.keys()),
                    reasoning="\n".join(reasoning_steps) if reasoning_steps else None
                )

            # Process tool calls
            messages.append(assistant_message)

            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)

                if verbose:
                    print(f"Tool: {tool_name}")
                    print(f"Args: {arguments}")

                result = self._execute_tool(tool_name, arguments)
                collected_data[f"{tool_name}_{len(collected_data)}"] = result
                reasoning_steps.append(f"Called {tool_name}({arguments})")

                if verbose:
                    print(f"Result: {str(result)[:300]}...")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, default=str)
                })

        return AgentResponse(
            question=question,
            answer="Reached max iterations without completing analysis.",
            data=collected_data,
            reasoning="\n".join(reasoning_steps)
        )

    def _ask_offline(self, question: str) -> AgentResponse:
        """Answer using ontology only (no LLM)."""
        # Simple keyword matching for offline mode
        q = question.lower()

        if "revenue" in q and "borough" in q:
            data = self.semantic.get_revenue_by_borough()
            context = self.ontology.get_concept_context("Manhattan")
            return AgentResponse(
                question=question,
                answer=f"Revenue by borough:\n{data}\n\nContext: Manhattan dominates due to business/tourist density.",
                data=data,
                reasoning="Offline mode - direct query"
            )

        if "tip" in q:
            data = self.semantic.get_tips_by_borough()
            return AgentResponse(
                question=question,
                answer=f"Tips by borough:\n{data}\n\nNote: Cash tips not recorded. Outer borough tips lower due to demographics, not service.",
                data=data,
                reasoning="Offline mode - direct query"
            )

        return AgentResponse(
            question=question,
            answer="Offline mode: Please configure Azure OpenAI for full capabilities.",
            reasoning="No LLM available"
        )


def main():
    """Interactive CLI."""
    print("=" * 70)
    print("NYC TAXI AI AGENT - Mini Fabric IQ")
    print("Semantic Layer + Ontology + Azure OpenAI")
    print("=" * 70)

    agent = NYCTaxiAgent()

    print("\nExample questions:")
    print("  - What is total revenue by borough?")
    print("  - Why is Manhattan revenue highest?")
    print("  - Why are tips lower in Brooklyn?")
    print("  - Classify a trip from JFK to Midtown at 8am")
    print("\nType 'quit' to exit.\n")

    while True:
        try:
            question = input("\nYou: ").strip()
            if not question:
                continue
            if question.lower() in ['quit', 'exit', 'q']:
                break

            print("\nThinking...")
            response = agent.ask(question, verbose=True)
            print(f"\nAgent: {response.answer}")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
```

---

## Phase 10: Integration & Testing

### 10.1 Update unified_layer.py

Connect all layers in the existing module:

```python
# src/unified_layer.py - Updated to use semantic layer

from semantic_layer import SemanticLayer
from ontology_layer import OntologyLayer
from agent import NYCTaxiAgent

class UnifiedIntelligenceLayer:
    """
    Unified layer combining:
    - Technical (OpenMetadata catalog)
    - Semantic (boring-semantic-layer + PostgreSQL)
    - Ontology (OWL/RDF reasoning)
    - Agent (Azure OpenAI)
    """

    def __init__(self):
        self.semantic = SemanticLayer()
        self.ontology = OntologyLayer()
        self.agent = NYCTaxiAgent()

    def ask(self, question: str) -> dict:
        """Natural language interface - the Fabric IQ experience."""
        response = self.agent.ask(question)
        return {
            "question": response.question,
            "answer": response.answer,
            "data": response.data,
            "sources": response.sources,
            "reasoning": response.reasoning
        }

    def query(self, dimensions: list, measures: list, **kwargs) -> dict:
        """Direct semantic layer query."""
        return self.semantic.query(dimensions, measures, **kwargs)

    def explain(self, concept: str) -> dict:
        """Get ontology explanation for a concept."""
        return self.ontology.get_concept_context(concept)
```

### 10.2 Create Demo Script

```python
# scripts/demo_fabric_iq.py
"""
Demo: Mini Fabric IQ Experience

Shows the full stack working together:
1. Natural language question
2. Semantic layer computes data
3. Ontology provides context
4. Agent explains the answer
"""

from src.unified_layer import UnifiedIntelligenceLayer

def main():
    print("=" * 70)
    print("DEMO: Mini Fabric IQ / Palantir AIP")
    print("=" * 70)

    uil = UnifiedIntelligenceLayer()

    questions = [
        "What is total revenue by borough?",
        "Why is Manhattan revenue so much higher than other boroughs?",
        "Why are tips lower in Brooklyn compared to Manhattan?",
        "What types of trips go to JFK Airport?",
    ]

    for q in questions:
        print(f"\n{'='*70}")
        print(f"QUESTION: {q}")
        print("="*70)

        result = uil.ask(q)

        print(f"\nANSWER:\n{result['answer']}")

        if result.get('data'):
            print(f"\nDATA SOURCES: {result.get('sources', [])}")

        input("\nPress Enter for next question...")


if __name__ == "__main__":
    main()
```

### 10.3 Verification Checklist

- [ ] `uv run python src/semantic_layer.py` - Returns actual PostgreSQL data
- [ ] `uv run python src/ontology_layer.py` - Loads enriched ontology
- [ ] `uv run python src/agent.py` - Interactive agent works
- [ ] `uv run python scripts/demo_fabric_iq.py` - Full demo runs

---

## Phase 11: Update Documentation

### 11.1 Update tasks.md

Mark Phases 7-10 as complete (when done).

### 11.2 Create Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     INTELLIGENT SEMANTIC LAYER                          │
│                                                                         │
│                          ┌─────────────┐                               │
│                          │   User      │                               │
│                          │  Question   │                               │
│                          └──────┬──────┘                               │
│                                 │                                       │
│                                 ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                        AI AGENT                                   │  │
│  │                   (Azure OpenAI + Tools)                         │  │
│  │                                                                   │  │
│  │  Tools:                                                          │  │
│  │  • query_metrics()    → Semantic Layer                          │  │
│  │  • get_context()      → Ontology                                │  │
│  │  • explain_metric()   → Ontology                                │  │
│  │  • classify_trip()    → Ontology                                │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│           │                              │                              │
│           ▼                              ▼                              │
│  ┌─────────────────────┐      ┌─────────────────────┐                 │
│  │   SEMANTIC LAYER    │      │     ONTOLOGY        │                 │
│  │                     │      │                     │                 │
│  │ boring-semantic-    │      │  OWL/RDF (Turtle)   │                 │
│  │ layer + Ibis        │      │                     │                 │
│  │                     │      │  • 28+ classes      │                 │
│  │ • Metrics (15+)     │      │  • 6 relationships  │                 │
│  │ • Dimensions (12+)  │      │  • 10+ rules        │                 │
│  │ • Joins             │      │  • Zone instances   │                 │
│  └──────────┬──────────┘      └─────────────────────┘                 │
│             │                                                          │
│             ▼                                                          │
│  ┌─────────────────────┐      ┌─────────────────────┐                 │
│  │    PostgreSQL       │      │   OpenMetadata      │                 │
│  │                     │      │                     │                 │
│  │  • trips (2.76M)    │      │  • Table catalog    │                 │
│  │  • zones (265)      │      │  • Glossary terms   │                 │
│  │  • payment_types    │      │  • Lineage          │                 │
│  │  • rate_codes       │      │  • Data quality     │                 │
│  └─────────────────────┘      └─────────────────────┘                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Summary: Files to Create/Modify

### New Files
| File | Purpose |
|------|---------|
| `semantic_model.yml` | Metric and dimension definitions |
| `src/semantic_layer.py` | PostgreSQL-backed semantic layer |
| `src/agent.py` | AI agent with tool calling |
| `scripts/demo_fabric_iq.py` | End-to-end demo |

### Modified Files
| File | Changes |
|------|---------|
| `pyproject.toml` | Add boring-semantic-layer, ibis-framework[postgres], rdflib |
| `ontology/nyc_taxi.ttl` | Add Trip types, Zone types, instances, rules |
| `src/ontology_layer.py` | Add classify_trip(), explain_metric(), get_rules_for_topic() |
| `src/unified_layer.py` | Connect semantic layer and agent |
| `.claude/tasks.md` | Update with Phases 7-11 |

---

## Estimated Effort

| Phase | Effort | Dependencies |
|-------|--------|--------------|
| Phase 7: Semantic Layer | 2-3 hours | None |
| Phase 8: Enrich Ontology | 2-3 hours | None |
| Phase 9: Build Agent | 3-4 hours | Phases 7, 8 |
| Phase 10: Integration | 1-2 hours | Phases 7, 8, 9 |
| Phase 11: Documentation | 1 hour | Phase 10 |

**Total: 9-13 hours**

---

## Success Criteria

The implementation is complete when:

1. ✅ `uv run python src/semantic_layer.py` returns actual PostgreSQL data
2. ✅ Agent can answer: "What is total revenue by borough?"
3. ✅ Agent can answer: "Why is Manhattan revenue highest?" with ontology context
4. ✅ Agent can answer: "Why are tips lower in Brooklyn?" with correct explanation
5. ✅ Demo script runs end-to-end without errors

This completes the **Mini Fabric IQ / Palantir AIP** proof-of-concept.
