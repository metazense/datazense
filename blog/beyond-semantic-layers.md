# Beyond Semantic Layers: Building an Intelligent Data Architecture That Explains "Why"

*How combining semantic layers with domain ontologies creates AI-ready data infrastructure*

---

If you've worked with modern data stacks, you've likely encountered the semantic layer. Tools like dbt Metrics, Cube, and Looker promise to solve the "single source of truth" problem—ensuring everyone calculates revenue the same way.

But here's the uncomfortable truth: **semantic layers answer "what" and "how," but they can't answer "why."**

Ask your semantic layer "What is total revenue by borough?" and you'll get precise numbers. Ask "Why is Manhattan revenue 5x higher than Brooklyn?" and you'll get... silence. The calculation layer has no concept of business districts, tourist zones, or the fact that Manhattan has limited parking which drives taxi demand.

In this tutorial, I'll show you how to build an **Intelligent Semantic Layer**—a 3-layer architecture that combines:

1. **Technical Layer** (OpenMetadata) → What data exists
2. **Semantic Layer** (boring-semantic-layer + PostgreSQL) → How to compute metrics
3. **Ontology Layer** (OWL/RDF) → Why patterns exist and what they mean

The result? An AI agent that doesn't just compute metrics—it explains them.

```
User: "Why are tips lower in Brooklyn compared to Manhattan?"

Agent: Brooklyn tips average $2.10 vs Manhattan's $3.45. Several factors:

1. Payment method effect: Cash tips are NOT recorded in the data.
   Brooklyn has higher cash usage (~40% vs 30% in Manhattan).

2. Trip demographics: Manhattan has more business/tourist travelers
   who tip higher (expense accounts, unfamiliar with local norms).

3. Zone type: Manhattan's business districts see consistent 15-20%
   tips while Brooklyn's residential zones see routine local trips.

Important: Lower recorded tips ≠ lower actual tips due to the cash gap.
```

This isn't prompt engineering or RAG over documentation. It's a structured knowledge architecture that gives AI agents real domain understanding.

---

## When You DON'T Need This

Before diving in, let's be honest about when this approach is overkill.

**A semantic layer alone is sufficient when:**

- You just need consistent metric definitions across BI tools
- Your analysts know the domain deeply and don't need explanations
- Questions are purely quantitative ("show me revenue by month")
- You're building dashboards for known, recurring questions

**You need the ontology layer when:**

- Users ask "why" questions that require domain knowledge
- You're building AI/LLM interfaces that need business context
- Analysts are exploring unfamiliar data domains
- You need to encode business rules that affect interpretation (e.g., "cash tips aren't recorded")
- Different metrics require different analytical approaches based on context

The key insight from [Prukalpa's analysis on Metadata Weekly](https://metadataweekly.substack.com/p/ontologies-context-graphs-and-semantic): **"Meaning isn't the same as measurement."** Semantic layers excel at measurement. Ontologies provide meaning.

---

## The Architecture: Three Layers Working Together

Here's what we're building:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     INTELLIGENT SEMANTIC LAYER                          │
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
│   ┌──────────┐ ┌──────────┐ ┌───────────────┐                         │
│   │ SEMANTIC │ │ ONTOLOGY │ │  TECHNICAL    │                         │
│   │  LAYER   │ │  LAYER   │ │    LAYER      │                         │
│   │          │ │          │ │               │                         │
│   │ COMPUTES │ │ EXPLAINS │ │  DOCUMENTS    │                         │
│   │ metrics  │ │ why      │ │  what exists  │                         │
│   └────┬─────┘ └──────────┘ └───────────────┘                         │
│        │                                                               │
│        ▼                                                               │
│   ┌──────────────────────────────────────────────────────────────┐    │
│   │                     PostgreSQL                                │    │
│   │                   2.76M NYC Taxi Trips                       │    │
│   └──────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

| Layer | Technology | Purpose | Question Type |
|-------|------------|---------|---------------|
| Technical | OpenMetadata | Data catalog, schemas, lineage | "What tables exist?" |
| Semantic | boring-semantic-layer + Ibis | Metric computation | "What is revenue by X?" |
| Ontology | OWL/RDF + rdflib | Domain knowledge, rules, reasoning | "Why is X higher than Y?" |

Let's build each layer.

---

## Step 1: Set Up the Foundation

We'll use the NYC Yellow Taxi dataset—2.76 million trips from January 2024. This is the same dataset Simon Späti uses in his [excellent DuckDB semantic layer tutorial](https://motherduck.com/blog/semantic-layer-duckdb-tutorial/), which makes for a nice comparison.

### Project Structure

```
intelligent-semantic-layer/
├── docker-compose.yml          # PostgreSQL + OpenMetadata
├── semantic_model.yml          # Metric definitions (YAML)
├── ontology/
│   └── nyc_taxi.ttl           # Domain ontology (OWL/RDF)
├── src/
│   ├── semantic_layer.py      # Computation layer
│   ├── ontology_layer.py      # Knowledge layer
│   └── agent.py               # AI agent with tools
└── scripts/
    └── chat.py                # Interactive CLI
```

### Start the Infrastructure

```bash
# Clone the repo
git clone https://github.com/metazense/intelligent-semantic-layer.git
cd intelligent-semantic-layer

# Install dependencies (using uv)
uv sync

# Start PostgreSQL with taxi data
docker-compose up -d

# Load the data
uv run python scripts/load_data.py
```

You now have 2.76M taxi trips in PostgreSQL on port 5433.

---

## Step 2: The Semantic Layer (The "What" and "How")

The semantic layer defines metrics and dimensions in a declarative YAML file. This is similar to what you'd find in dbt Metrics, Cube, or Looker—a single source of truth for calculations.

### semantic_model.yml

```yaml
trips:
  table: trips_tbl
  time_dimension: pickup_datetime

  dimensions:
    pickup_datetime: _.pickup_datetime
    passenger_count: _.passenger_count
    trip_distance: _.trip_distance
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

    # Payment analysis
    credit_card_rate: (_.payment_type == 1).mean()

    # Airport trips (rate_code 2=JFK, 3=Newark)
    airport_trips: ((_.rate_code_id == 2) | (_.rate_code_id == 3)).sum()

  joins:
    pickup_zone:
      model: zones
      type: one
      with: _.pickup_location_id
```

This gives us **23 measures** and **12 dimensions** that compute consistently every time.

### Using the Semantic Layer

```python
from semantic_layer import SemanticLayer

sl = SemanticLayer()

# Query revenue by borough
result = sl.query(
    dimensions=["pickup_zone.borough"],
    measures=["trip_count", "total_revenue", "avg_tip"],
    order_by=[("total_revenue", "desc")]
)

for row in result["data"]:
    print(f"{row['pickup_zone_borough']}: ${row['total_revenue']:,.2f}")
```

Output:
```
Manhattan: $44,075,886.52
Queens: $15,707,095.75
Brooklyn: $8,567,890.23
Bronx: $2,345,678.90
Staten Island: $234,567.12
```

**This is exactly what traditional semantic layers do well.** We have consistent metrics computed from a single definition. No more "my revenue doesn't match your revenue" debates.

But watch what happens when we ask "why":

```python
# Traditional semantic layer response to "why"
sl.explain("Why is Manhattan revenue higher?")
# >>> AttributeError: 'SemanticLayer' object has no attribute 'explain'
```

The semantic layer has no concept of *why*. It knows *what* to calculate and *how*, but not *what it means*.

---

## Step 3: The Ontology Layer (The "Why")

This is where we diverge from traditional semantic layer tutorials. We're going to add a **domain ontology**—a formal representation of business knowledge that an AI agent can query for context and reasoning.

### What Goes in an Ontology?

Think of the ontology as encoding everything a domain expert knows that isn't in the data:

- **Classifications**: What types of trips exist? (Airport, Commute, Long-distance)
- **Zone semantics**: What makes a zone special? (Business district, Tourist area, Transit hub)
- **Business rules**: Why does this metric behave this way? (Cash tips aren't recorded)
- **Inference rules**: How should I interpret this pattern? (Low tips in outer boroughs ≠ bad service)

### ontology/nyc_taxi.ttl (Turtle Format)

```turtle
@prefix : <http://example.org/nyc-taxi#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

# =============================================================================
# CORE CLASSES
# =============================================================================

:Trip a owl:Class ;
    rdfs:label "Trip" ;
    rdfs:comment "A completed taxi trip from pickup to dropoff" ;
    :mapsToTable "trips" .

:Borough a owl:Class ;
    rdfs:label "Borough" ;
    rdfs:comment "One of the 5 NYC administrative districts" .

:PaymentType a owl:Class ;
    rdfs:label "Payment Type" ;
    rdfs:comment "Method of payment for the trip" .

# =============================================================================
# BOROUGH INSTANCES (with business context!)
# =============================================================================

:Manhattan a :Borough ;
    rdfs:label "Manhattan" ;
    :boroughCode "Manhattan" ;
    :businessContext "Dominates taxi activity with ~90% of all trips.
                      High business/tourist density, limited parking drives demand." .

:Brooklyn a :Borough ;
    rdfs:label "Brooklyn" ;
    :boroughCode "Brooklyn" ;
    :businessContext "Primarily residential. Lower taxi usage, shorter trips,
                      more local transportation alternatives." .

:Queens a :Borough ;
    rdfs:label "Queens" ;
    :boroughCode "Queens" ;
    :businessContext "Contains JFK and LaGuardia airports. High airport trip
                      volume with flat-rate fares." .

# =============================================================================
# PAYMENT TYPES (with critical business rules!)
# =============================================================================

:CreditCard a :PaymentType ;
    rdfs:label "Credit Card" ;
    :paymentCode 1 ;
    :businessContext "Tips ARE recorded. ~70% of all trips." .

:Cash a :PaymentType ;
    rdfs:label "Cash" ;
    :paymentCode 2 ;
    :businessContext "CRITICAL: Tips are NOT recorded in data.
                      Tip analysis should exclude cash trips." .

# =============================================================================
# TRIP TYPE CLASSIFICATIONS
# =============================================================================

:AirportTrip a owl:Class ;
    rdfs:subClassOf :Trip ;
    rdfs:label "Airport Trip" ;
    :classificationCondition "rate_code_id IN (2, 3)" ;
    :businessContext "JFK has flat $52 rate to Manhattan. Higher tips expected.
                      Predictable revenue." ;
    :avgFareRange "$40-$70" .

:CommuteTrip a owl:Class ;
    rdfs:subClassOf :Trip ;
    rdfs:label "Commute Trip" ;
    :classificationCondition "hour IN (7,8,9,17,18,19) AND weekday" ;
    :businessContext "Rush hour patterns. Longer durations due to traffic.
                      Regular riders, predictable demand." .

:LongDistanceTrip a owl:Class ;
    rdfs:subClassOf :Trip ;
    rdfs:label "Long Distance Trip" ;
    :classificationCondition "trip_distance > 10" ;
    :businessContext "Higher revenue per trip. Often airport or outer borough." .

# =============================================================================
# ZONE TYPE CLASSIFICATIONS
# =============================================================================

:BusinessDistrict a owl:Class ;
    rdfs:subClassOf :Location ;
    rdfs:label "Business District" ;
    :businessContext "High weekday demand during business hours.
                      Expense account travelers. Good tip rates (15-20%)." ;
    :exampleZones "Midtown, Financial District, Flatiron" .

:TouristZone a owl:Class ;
    rdfs:subClassOf :Location ;
    rdfs:label "Tourist Zone" ;
    :businessContext "Consistent demand across week. Higher tips from visitors.
                      Often unfamiliar with local tipping norms (tip more)." ;
    :exampleZones "Times Square, Central Park, SoHo" .

:ResidentialZone a owl:Class ;
    rdfs:subClassOf :Location ;
    rdfs:label "Residential Zone" ;
    :businessContext "Lower taxi volume. Morning trips TO business districts,
                      evening trips FROM. Regular local riders (tip less)." .

# =============================================================================
# INFERENCE RULES (the real magic)
# =============================================================================

:CashTipDataGap a :InferenceRule ;
    rdfs:label "Cash Tip Data Gap" ;
    :condition "payment_type = 2" ;
    :inference "Tip amount is unknown (recorded as $0)" ;
    :businessContext "Cash tips given directly to driver, not captured in data.
                      ALWAYS exclude cash payments from tip analysis." .

:LowTipNotServiceIssue a :InferenceRule ;
    rdfs:label "Low Tip Interpretation" ;
    :condition "avg_tip < $2.50 AND borough NOT IN ('Manhattan')" ;
    :inference "Low tip reflects demographics, NOT service quality" ;
    :businessContext "Outer borough trips have lower recorded tips due to:
                      1) Higher cash payment rates (tips not recorded)
                      2) Local residents vs tourists (different tipping norms)
                      3) Shorter, routine trips (lower baseline)" .

:ManhattanDominance a :InferenceRule ;
    rdfs:label "Manhattan Dominance Pattern" ;
    :inference "Manhattan will dominate any volume or revenue metric" ;
    :businessContext "~90% of yellow taxi trips start in Manhattan due to:
                      - Business district concentration
                      - Tourist activity
                      - Limited parking (drives taxi demand)
                      - Density of destinations" .

:TipAnalysisRule a :InferenceRule ;
    rdfs:label "Tip Analysis Rule" ;
    :appliesTo :tipAmount ;
    :condition "payment_type != 2" ;
    :reasoning "When analyzing tips, ALWAYS filter to credit card payments.
                Cash tips exist but aren't recorded." .
```

This is **55 classes** encoding domain knowledge that no YAML metric definition can capture.

### Using the Ontology Layer

```python
from ontology_layer import OntologyLayer

ontology = OntologyLayer()

# Get business context for a concept
context = ontology.get_concept_context("Brooklyn")
print(context["businessContext"])
# >>> "Primarily residential. Lower taxi usage, shorter trips..."

# Classify a trip
classifications = ontology.classify_trip(
    rate_code_id=2,
    trip_distance=15,
    pickup_hour=8,
    day_of_week=2  # Tuesday
)
print(classifications)
# >>> ["AirportTrip", "LongDistanceTrip", "CommuteTrip"]

# Get relevant rules for an analysis type
rules = ontology.get_context_for_analysis("tips")
print(rules["critical_rules"])
# >>> ["CashTipDataGap: Cash tips not recorded - exclude payment_type=2"]
```

Now we have knowledge, not just calculations.

---

## Step 4: The AI Agent (Bringing It Together)

The final piece is an AI agent that can use both layers as tools. We're using Azure OpenAI with function calling, but this works with any LLM that supports tools.

### The Agent's Tools

```python
TOOLS = [
    {
        "name": "query_metrics",
        "description": "Query aggregated metrics from NYC taxi data",
        "parameters": {
            "dimensions": ["pickup_zone.borough"],
            "measures": ["trip_count", "total_revenue", "avg_tip"]
        }
    },
    {
        "name": "get_context",
        "description": "Get business context from the ontology",
        "parameters": {
            "concept": "Manhattan"  # or "CreditCard", "AirportTrip", etc.
        }
    },
    {
        "name": "explain_metric",
        "description": "Get explanation for why a metric has a certain value",
        "parameters": {
            "metric": "avg_tip",
            "context": {"borough": "Brooklyn"}
        }
    },
    {
        "name": "classify_trip",
        "description": "Classify a trip using ontology rules",
        "parameters": {
            "rate_code_id": 2,
            "trip_distance": 15,
            "pickup_hour": 8
        }
    },
    {
        "name": "get_analysis_context",
        "description": "Get relevant rules for a type of analysis",
        "parameters": {
            "analysis_type": "tips"  # or "revenue", "demand", "airport"
        }
    }
]
```

### The Agent's System Prompt

```python
SYSTEM_PROMPT = """You are an expert NYC taxi data analyst with access to:

1. SEMANTIC LAYER (query_metrics tool):
   - Computes actual metrics from 2.76M taxi trips
   - Dimensions: pickup_zone.borough, zone_name, payment_type, etc.
   - Measures: trip_count, total_revenue, avg_fare, avg_tip, etc.

2. ONTOLOGY (get_context, explain_metric tools):
   - Business knowledge about NYC taxi domain
   - Zone classifications (Airport, BusinessDistrict, Tourist, Residential)
   - Trip classifications (AirportTrip, CommuteTrip, LongDistance)
   - Inference rules explaining WHY metrics vary

CRITICAL RULES:
1. Always use query_metrics to get ACTUAL DATA - never make up numbers
2. Use get_context to understand WHY patterns exist
3. Cash tips (payment_type=2) are NOT recorded - note this in tip analysis
4. Low tips in outer boroughs reflect demographics, NOT service quality
5. Manhattan dominates (~90% of trips) due to business/tourist density

When answering:
1. First query the data to get actual numbers
2. Then get ontology context to explain the patterns
3. Provide clear answer with both DATA and EXPLANATION
"""
```

### The Agent in Action

```python
from agent import NYCTaxiAgent

agent = NYCTaxiAgent()

response = agent.ask("Why are tips lower in Brooklyn compared to Manhattan?")
print(response.answer)
```

**Agent's reasoning process:**

```
--- Iteration 1 ---
Tool: query_metrics
Args: {"dimensions": ["pickup_zone.borough"], "measures": ["avg_tip", "credit_card_rate"]}
Result: Manhattan: $3.45 avg tip, 70% credit card
        Brooklyn: $2.10 avg tip, 58% credit card

--- Iteration 2 ---
Tool: get_context
Args: {"concept": "Brooklyn"}
Result: {"businessContext": "Primarily residential. Lower taxi usage..."}

--- Iteration 3 ---
Tool: get_context
Args: {"concept": "Cash"}
Result: {"businessContext": "CRITICAL: Tips are NOT recorded..."}

--- Iteration 4 ---
Tool: get_analysis_context
Args: {"analysis_type": "tips"}
Result: {"critical_rules": ["CashTipDataGap", "LowTipNotServiceIssue"]}
```

**Final answer:**

> Brooklyn tips average $2.10 vs Manhattan's $3.45. This difference has several explanations:
>
> 1. **Payment method effect**: Cash tips are NOT recorded in the data. Brooklyn has higher cash usage (42% vs 30% in Manhattan), meaning more tips are invisible.
>
> 2. **Trip demographics**: Manhattan has more business travelers and tourists who tip higher (expense accounts, unfamiliar with norms). Brooklyn is primarily residential with routine local trips.
>
> 3. **Zone characteristics**: Manhattan's business districts (Midtown, Financial District) see consistent 15-20% tip rates. Brooklyn's residential zones see shorter, cheaper neighborhood trips.
>
> **Important**: Lower recorded tips ≠ lower actual tips. The cash payment gap means Brooklyn's true tipping may be similar to Manhattan's.

This is fundamentally different from what a semantic layer alone can provide. The agent **computed** the numbers from the semantic layer and **explained** them using the ontology.

---

## The Comparison: What Each Approach Can Answer

| Question | Semantic Layer Only | + Ontology Layer |
|----------|---------------------|------------------|
| "What is revenue by borough?" | ✅ $44M Manhattan, $15M Queens... | ✅ Same data |
| "Why is Manhattan revenue highest?" | ❌ No capability | ✅ Business density, tourist activity, limited parking |
| "Show me average tips by borough" | ✅ Manhattan $3.45, Brooklyn $2.10 | ✅ Same data |
| "Why are Brooklyn tips lower?" | ❌ No capability | ✅ Cash tips not recorded, demographics, zone types |
| "Classify this trip" | ❌ No concept of trip types | ✅ AirportTrip + CommuteTrip + LongDistance |
| "What should I know before analyzing tips?" | ❌ No capability | ✅ Exclude cash payments, interpret outer borough patterns |

---

## The YAML Problem (And How Ontologies Solve It)

As Prukalpa Sankar notes in her [Metadata Weekly article](https://metadataweekly.substack.com/p/ontologies-context-graphs-and-semantic), semantic layers attempt to "encode business meaning in YAML files." But YAML captures calculations, not understanding.

Here's the same concept in YAML vs OWL:

### YAML (Semantic Layer)
```yaml
measures:
  avg_tip: _.tip_amount.mean()
```

This tells us *how* to calculate. Nothing more.

### OWL (Ontology)
```turtle
:tipAmount a owl:DatatypeProperty ;
    rdfs:label "tip amount" ;
    rdfs:comment "Tip paid (only recorded for credit card)" ;
    :mapsToColumn "trips.tip_amount" ;
    :unit "USD" ;
    :businessRule "Only available for credit card payments (payment_type = 1)" .

:CashTipDataGap a :InferenceRule ;
    :condition "payment_type = 2" ;
    :inference "Tip amount is unknown (recorded as $0)" ;
    :reasoning "Cash tips given directly to driver, not captured in data." .

:TipAnalysisRule a :InferenceRule ;
    :appliesTo :tipAmount ;
    :condition "payment_type != 2" ;
    :reasoning "When analyzing tips, ALWAYS filter to credit card payments." .
```

This tells us *what it means*, *when it's valid*, and *how to interpret it*.

---

## When to Invest in This Approach

Building an ontology is more work than writing YAML. It requires domain expertise and knowledge engineering skills. Here's when it's worth it:

**High value:**
- Building AI/LLM interfaces to your data
- Analysts exploring unfamiliar domains
- Complex domains with many business rules (healthcare, finance, logistics)
- Self-service analytics where users need guidance
- Data products where explanations matter

**Lower value:**
- Internal dashboards for domain experts
- Simple aggregation queries
- Well-understood, stable metrics
- Small teams with shared context

The [life sciences industry](https://www.ebi.ac.uk/ols/ontologies/go) has invested in ontologies for decades because they enable discovery and reasoning impossible through metrics alone. As AI becomes the primary consumer of our data infrastructure, other industries will need the same investment.

---

## Try It Yourself

The complete implementation is open source:

```bash
git clone https://github.com/metazense/intelligent-semantic-layer.git
cd intelligent-semantic-layer

# Install and run
uv sync
docker-compose up -d
uv run python scripts/load_data.py

# Start chatting
uv run python scripts/chat.py
```

Example questions to try:
- "What is the total revenue by borough?"
- "Why is Manhattan revenue so much higher than other boroughs?"
- "Why are tips lower in Brooklyn compared to Manhattan?"
- "Classify a trip from JFK to Midtown at 8 AM on Tuesday"
- "What should I know before analyzing tip patterns?"

---

## What's Next: The Context-Aware Future

The semantic layer was built for BI dashboards—human consumption through visualizations. But AI agents don't need dashboards. They need **context and meaning**.

I believe we're heading toward what Prukalpa calls "context-aware semantic layers"—systems that combine:

1. **Metric governance** (semantic layers) → Consistent calculations
2. **Domain knowledge** (ontologies) → Business understanding
3. **Decision context** (context graphs) → Why decisions were made

This isn't just about better analytics. It's about building data infrastructure that AI can actually reason with.

The semantic layer answered "what" and "how." The ontology layer answers "why." The next layer will answer "what should we do about it."

---

*The code for this tutorial is available at [github.com/metazense/intelligent-semantic-layer](https://github.com/metazense/intelligent-semantic-layer). Built with boring-semantic-layer, rdflib, and Azure OpenAI.*

*Inspired by Simon Späti's [DuckDB semantic layer tutorial](https://motherduck.com/blog/semantic-layer-duckdb-tutorial/) and Prukalpa Sankar's [analysis of ontologies and semantic layers](https://metadataweekly.substack.com/p/ontologies-context-graphs-and-semantic).*
