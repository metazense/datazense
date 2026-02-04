# Intelligent Semantic Layer

**A 3-layer metadata architecture for AI-powered data analytics**

Combining OpenMetadata + Semantic Layer + Domain Ontology to enable natural language queries that don't just compute metrics - they explain *why*.

---

## The Problem

Traditional semantic layers (dbt Metrics, Cube.dev, etc.) answer "what" and "how":
- What is the revenue by borough? -> $44M Manhattan, $15M Queens
- How do we calculate it? -> SUM(fare_amount + tip_amount)

But when analysts ask "why", semantic layers fall short:
- Why are tips lower in Brooklyn? -> No answer

## The Solution

This project implements a **3-layer metadata architecture** inspired by Microsoft Fabric IQ and Palantir AIP:

```
User Question --> AI Agent --> 3 Metadata Layers --> Intelligent Answer
                                    |
                 +------------------+------------------+
                 |                  |                  |
          Technical Layer    Semantic Layer    Ontology Layer
          (OpenMetadata)      (Ibis/PG)         (OWL/RDF)
                 |                  |                  |
                 +------------------+------------------+
                                    |
                            PostgreSQL DB
                         (2.76M Taxi Trips)
```

### The Three Layers

| Layer | Technology | Purpose | Answers |
|-------|------------|---------|---------|
| Technical | OpenMetadata | Data catalog | "What data exists?" |
| Semantic | boring-semantic-layer + Ibis | Metric computation | "How do we calculate?" |
| Ontology | OWL/RDF (rdflib) | Domain knowledge | "What does it mean? Why?" |

---

## Key Features

**AI Agent with Tool Calling**
- Natural language interface powered by Azure OpenAI
- 10 specialized tools for querying data, context, and metadata
- Multi-turn reasoning with function calling

**Real Semantic Layer**
- 12 dimensions (borough, zone, payment type, etc.)
- 23 measures (revenue, tips, distance, etc.)
- Actual computation against PostgreSQL (not just definitions)

**Rich Domain Ontology (55 OWL classes)**
- Trip Types: AirportTrip, CommuteTrip, LongDistanceTrip, NightTrip, WeekendTrip
- Zone Types: Airport, BusinessDistrict, Residential, Tourist, TransitHub
- Time Contexts: RushHour, OffPeak, NightTime, WeekendDay, WeekendNight
- 10 Inference Rules for trip classification, tip patterns, demand prediction

**OpenMetadata Integration**
- Table and column metadata
- Business glossary (21 terms)
- Data lineage tracking

---

## Quick Start

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- Azure OpenAI API access (optional, for AI agent)

### Setup

```bash
# Clone the repo
git clone https://github.com/yourusername/intelligent-semantic-layer.git
cd intelligent-semantic-layer

# Install dependencies
uv sync

# Start infrastructure (PostgreSQL + OpenMetadata)
docker-compose up -d

# Load sample data
uv run python scripts/load_data.py

# Configure Azure OpenAI (optional)
cp .env.example .env
# Edit .env with your credentials

# Run the AI assistant
uv run python scripts/chat.py
```

---

## Example Interactions

### Technical Layer (OpenMetadata) Questions
```
You: What tables are available in the database?
Agent: [Uses list_tables tool]
       Found 4 tables: trips (2.76M rows), zones (265 rows),
       payment_types (6 rows), rate_codes (6 rows)

You: Show me the schema for the trips table
Agent: [Uses get_table_schema tool]
       The trips table has 15 columns including:
       - pickup_datetime (TIMESTAMP): When the meter was engaged
       - fare_amount (DECIMAL): Base fare from the meter
       - tip_amount (DECIMAL): Tip amount (credit card only)
       - payment_type (INTEGER): Payment method (1=Credit, 2=Cash)
       ...

You: What glossary terms are defined for metrics?
Agent: [Uses get_glossary_terms tool]
       Metrics glossary includes: Trip Revenue, Trip Count, Average Fare,
       Average Tip, Total Amount - each with business definitions.
```

### Semantic Layer (Metrics & Dimensions) Questions
```
You: What is the total revenue by borough?
Agent: [Uses query_metrics tool]
       Revenue by Borough:
       - Manhattan: $44,234,567 (2.1M trips)
       - Queens: $15,123,456 (450K trips)
       - Brooklyn: $8,567,890 (280K trips)
       - Bronx: $2,345,678 (85K trips)
       - Staten Island: $234,567 (8K trips)

You: Show me average tip by payment type
Agent: [Uses query_metrics tool]
       Average Tips:
       - Credit Card: $3.45
       - Cash: $0.00 (tips not recorded)

       Note: Cash tips are given directly to driver and not captured in data.

You: Which zones have the highest trip count?
Agent: [Uses query_metrics tool]
       Top zones by trip volume:
       1. Midtown Center: 245,678 trips
       2. Upper East Side South: 198,456 trips
       3. Midtown East: 187,234 trips
       ...
```

### Ontology & Reasoning Questions
```
You: Why are tips lower in Brooklyn compared to Manhattan?
Agent: [Uses get_context + explain_metric tools]
       Brooklyn tips average $2.10 vs Manhattan's $3.45. Several factors:

       1. Payment mix: Brooklyn has higher cash usage (~40% vs 30%).
          Cash tips are NOT recorded in the data.
       2. Trip types: Manhattan has more tourist/business travelers who
          tip higher.
       3. Zone demographics: Manhattan business districts see expense
          account travelers.

       Important: Lower recorded tips ≠ lower actual tips due to cash gap.

You: Classify a trip with rate_code=2 and distance=15 miles at 8 AM
Agent: [Uses classify_trip tool]
       This trip classifies as:
       - AirportTrip: rate_code=2 indicates JFK Flat Rate ($52 to Manhattan)
       - CommuteTrip: 8 AM on weekday is rush hour
       - LongDistanceTrip: 15 miles exceeds 10-mile threshold

       Expected fare: $52 flat rate + tip (~$60-70 total)

You: What factors affect tip patterns?
Agent: [Uses get_analysis_context tool]
       Tip Pattern Rules from ontology:
       1. Cash tips (payment_type=2) are NOT recorded - exclude from analysis
       2. Airport trips: Higher tips from travelers
       3. Business districts: Consistent 15-20% tip rates
       4. Tourist zones: Higher tips from visitors
       5. Night trips: Often higher tips (late-night premium)
       6. Commute trips: Lower tips (routine daily trips)

You: Tell me about the business context for JFK Airport zone
Agent: [Uses get_context tool]
       JFK Airport (location_id: 132):
       - Borough: Queens
       - Zone Type: Airport Zone
       - Business Context: Major international airport with flat $52 rate
         to Manhattan (rate_code=2). High average fare, predictable revenue.
       - Typical Revenue: $52-$70 per trip
       - Related Rule: AirportTripRule - flat rates provide revenue stability
```

### Multi-Layer Combined Questions
```
You: What is the revenue by borough and why does Manhattan dominate?
Agent: [Uses query_metrics + get_context + get_analysis_context tools]

       Revenue by Borough:
       - Manhattan: $44.2M (78% of total)
       - Queens: $15.1M (13%)
       - Brooklyn: $8.6M (7%)
       - Bronx/Staten Island: $2.6M (2%)

       Why Manhattan dominates (from ontology):
       1. ManhattanDominanceRule: ~90% of yellow taxi trips originate here
       2. Business district concentration drives demand
       3. Tourist activity in Midtown, Times Square
       4. Limited parking makes taxis essential
       5. Higher fares due to congestion surcharge

       Queens revenue boosted by JFK/LaGuardia airport trips ($52+ fares).
```

---