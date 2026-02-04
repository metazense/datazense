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

**Data Questions**
```
You: What is the total revenue by borough?