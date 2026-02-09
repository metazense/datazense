# Intelligent Semantic Layer - Task List

## Project Overview
**Goal:** Prove the concept of a 3-layer metadata architecture:
- **Technical Layer** → What data exists (tables, columns, types)
- **Semantic Layer** → What data means (business terms, metrics)
- **Ontology Layer** → How concepts relate (domain model, reasoning)

Using PostgreSQL + NYC Taxi data + OpenMetadata as the foundation.

---

## Phase 1: Foundation - PostgreSQL + NYC Taxi Data ✅
> Goal: Get the database running with sample data

- [x] 1.1 Create Docker Compose file for PostgreSQL
- [x] 1.2 Download/prepare NYC Taxi dataset (1 month subset)
- [x] 1.3 Create database schema (trips, zones, payment_types, rate_codes)
- [x] 1.4 Load NYC Taxi data into PostgreSQL
- [x] 1.5 Verify data with sample queries

**Results:**
- 2,760,297 trips loaded
- 265 zones, 6 payment types, 6 rate codes
- $60M+ total revenue
- Database running on port 5433

---

## Phase 2: OpenMetadata Setup ✅
> Goal: Deploy OpenMetadata and connect to PostgreSQL

- [x] 2.1 Add OpenMetadata 1.7.1 to Docker Compose (PostgreSQL backend)
- [x] 2.2 Download and start all containers
- [x] 2.3 Configure NYC Taxi PostgreSQL connection
- [x] 2.4 Run metadata ingestion (4 tables registered)
- [x] 2.5 Verify technical metadata in OpenMetadata

**Results:**
- OpenMetadata UI: http://localhost:8585 (admin@open-metadata.org / admin)
- Service: `nyc_taxi_postgres`
- Database: `nyc_taxi.public`
- Tables: `trips` (20 cols), `zones` (4 cols), `payment_types` (2 cols), `rate_codes` (2 cols)

---

## Phase 3: Semantic Layer (OpenMetadata Glossary) ✅
> Goal: Define business terms and link them to technical columns

### 3.1 Create Glossary Structure
- [x] Create "NYC Taxi Business Glossary" in OpenMetadata
- [x] Define glossary categories: Metrics, Dimensions, Business Concepts

### 3.2 Define Business Metrics (7 terms)
- [x] Trip Revenue, Trip Count, Average Fare, Tip Percentage, Trip Duration, Trip Distance, Total Amount

### 3.3 Define Dimensions (7 terms)
- [x] Pickup Zone, Dropoff Zone, Borough, Payment Method, Rate Type, Pickup Date, Pickup Hour

### 3.4 Define Business Concepts (4 terms)
- [x] Airport Trip, Cash Payment, Peak Hours, Long Distance Trip

### 3.5 Column Descriptions & Links
- [x] Add business descriptions to 20 columns in trips table
- [x] Add business descriptions to 4 columns in zones table
- [x] Link 11 glossary terms to columns via Tags

**Results:**
- Glossary URL: http://localhost:8585/glossary/NYCTaxiBusinessGlossary
- Script: `scripts/create_semantic_layer.py`

---

## Phase 4: Ontology Layer (OWL/RDF) ✅
> Goal: Define domain concepts and relationships

### 4.1 Create Domain Ontology File
- [x] Create `ontology/nyc_taxi.ttl` (Turtle format)
- [x] Define 28 classes: Trip, Location, Borough (5 instances), PaymentType (4 instances), RateType (6 instances), Vendor
- [x] Define 6 relationships with SQL join mappings
- [x] Define 9 data properties with column mappings

### 4.2 Define Business Rules/Axioms
- [x] Tip Analysis Rule (exclude cash for tip analysis)
- [x] Airport Trip Rule (flat rates for rate_code 2,3)
- [x] Manhattan Dominance Rule (~90% of trips)
- [x] Peak Hours Rule (7-9 AM, 5-8 PM weekdays)
- [x] Revenue Calculation Rule (fare + tip)

### 4.3 Link Ontology to Semantic Layer
- [x] `glossaryTerm` annotations link OWL classes to Glossary FQNs
- [x] `mapsToTable`, `mapsToColumn`, `mapsToJoin` annotations link to technical schema
- [x] Query patterns with SQL templates

**Results:**
- Ontology file: `ontology/nyc_taxi.ttl`
- Python parser: `src/ontology_layer.py`

---

## Phase 5: Integration Layer (Python API) ✅
> Goal: Query all 3 layers and demonstrate linkage

### 5.1 Create Python Modules
- [x] `src/ontology_layer.py` - Parse OWL file, query relationships
- [x] `src/unified_layer.py` - Combines all 3 layers:
  - TechnicalLayer: Query OpenMetadata for tables/columns
  - SemanticLayer: Query OpenMetadata Glossary for terms
  - OntologyLayer: Parse OWL file for relationships
  - UnifiedIntelligenceLayer: Combine all three

### 5.2 Demo Capabilities
- [x] Understand concept (e.g., "revenue") using all 3 layers
- [x] Generate query context from natural language question
- [x] Find join paths between concepts (Trip → Borough)
- [x] Suggest SQL patterns from ontology

### 5.3 Demo Output
- [x] Question: "What is total revenue by borough?"
- [x] Identified: Trip Revenue (metric), Borough (dimension)
- [x] Tables: trips, zones
- [x] Join: `trips.pickup_location_id = zones.location_id`
- [x] Generated SQL from ontology pattern

**Run demo:** `python src/unified_layer.py`

---

## Phase 6: Demo & Visualization [DEFERRED]
> Goal: Show the 3-layer concept visually

- [ ] 6.1 Visualize ontology (WebVOWL or Python networkx)
- [ ] 6.2 Create diagram: Technical ↔ Semantic ↔ Ontology mapping
- [ ] 6.3 Demo scenarios:
  - "What is total revenue by borough?" (uses all 3 layers)
  - "Why is Manhattan revenue highest?" (ontology reasoning)
  - "How does payment type affect tips?" (semantic + ontology)

---

## Phase 7: Add Semantic Layer (boring-semantic-layer) ✅
> Goal: Add actual computation layer that executes queries

- [x] 7.1 Install boring-semantic-layer + ibis-framework[postgres]
- [x] 7.2 Create semantic_model.yml with metrics and dimensions
- [x] 7.3 Create src/semantic_layer.py with PostgreSQL backend
- [x] 7.4 Verify queries execute against PostgreSQL

**Results:**
- Semantic model: `semantic_model.yml`
- Python module: `src/semantic_layer.py`
- 12 dimensions (including pickup_zone.borough, zone_name, etc.)
- 23 measures (trip_count, total_revenue, avg_fare, avg_tip, etc.)
- Joins working: trips → zones (via pickup_location_id)

**Test output:**
```
Manhattan: 2,483,419 trips, $44,075,886.52 revenue
Queens: 255,627 trips, $15,707,095.75 revenue
JFK Airport: 140,806 trips, $10,076,664.27 revenue
```

---

## Phase 8: Enrich Ontology ✅
> Goal: Add Trip types, Zone types, instances, inference rules

- [x] 8.1 Add Trip subclasses (AirportTrip, CommuteTrip, LongDistanceTrip, ShortTrip, NightTrip, WeekendTrip)
- [x] 8.2 Add Zone type subclasses (AirportZone, BusinessDistrict, ResidentialZone, TouristZone, TransitHub, EntertainmentDistrict)
- [x] 8.3 Add TimeContext classes (RushHour, OffPeak, NightTime, WeekendDay, WeekendNight)
- [x] 8.4 Add Zone instances (JFK, LaGuardia, Newark, Midtown, Times Square, Penn Station, etc. - 19 total)
- [x] 8.5 Add Inference rules (TripClassification, TipPattern, DemandPrediction, RevenueOptimization, ZonePerformance)

**Results:**
- Ontology: 55 classes (6 trip types, 6 zone types, 5 time contexts, 19 zone instances)
- 10 inference rules with SQL conditions and business reasoning
- 5 query patterns for trip classification, time context, airport analysis
- Python helpers: `classify_trip()`, `get_time_context()`, `get_context_for_analysis()`
- Updated `src/ontology_layer.py` with new query methods

---

## Phase 9: Build AI Agent ✅
> Goal: Create agent that uses semantic layer + ontology

- [x] 9.1 Create src/agent.py with Azure OpenAI integration
- [x] 9.2 Define tools: query_metrics, get_context, get_measure_info, explain_metric, classify_trip, get_analysis_context
- [x] 9.3 Implement agentic loop with tool calling (max 5 iterations)
- [x] 9.4 Test demo questions with live data

**Results:**
- Agent class: `NYCTaxiAgent` in `src/agent.py`
- 6 tools available for LLM function calling
- Integrates: Azure OpenAI (gpt-5.1) + SemanticLayer + OntologyLayer
- Offline mode fallback when LLM not available
- Answers combine quantitative data with qualitative ontology insights

**Demo output:**
```
>>> Why are tips lower in Brooklyn compared to Manhattan?
[Uses get_context for both boroughs + domain knowledge]
- Payment method effect: Cash tips not recorded, Brooklyn has higher cash share
- Trip purpose: Manhattan has more business/tourist trips with higher tips
- Trip length: Brooklyn has shorter, cheaper neighborhood trips
```

---

## Phase 10: Integration & Demo ✅
> Goal: Connect all layers and create demo

- [x] 10.1 Update src/unified_layer.py to use semantic layer (ComputationLayer)
- [x] 10.2 Create scripts/demo_fabric_iq.py (comprehensive demo)
- [x] 10.3 Test end-to-end scenarios

**Results:**
- `src/unified_layer.py`: UnifiedIntelligenceLayer combining all 3 layers
- `scripts/demo_fabric_iq.py`: Full demo with --interactive mode
- All layers working: Technical (OpenMetadata), Semantic (Ibis/PG), Ontology (OWL)

**Demo capabilities:**
- Layer overview and status
- Concept understanding across layers
- Question answering with real data + business context
- Trip classification using ontology inference rules
- Time context analysis (RushHour, OffPeak, Weekend, etc.)
- AI Agent natural language interface

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Database | PostgreSQL 16 (port 5433) |
| Data | NYC Taxi Jan 2024 (2.76M trips) |
| Technical Layer | OpenMetadata 1.7.1 (port 8585) |
| Semantic Layer | boring-semantic-layer 0.1.4 + Ibis 10.8.0 |
| Ontology Layer | OWL/RDF file + Python rdflib |
| AI Agent | Azure OpenAI (gpt-5.1) |
| Integration | Python + FastAPI |
| Package Manager | uv |

---

## Docker Services

| Service | Container | Port | Status |
|---------|-----------|------|--------|
| NYC Taxi DB | nyc-taxi-postgres | 5433 | ✅ Running |
| OpenMetadata DB | openmetadata-postgres | 5434 | ✅ Running |
| OpenMetadata UI | openmetadata-server | 8585 | ✅ Running |
| Elasticsearch | elasticsearch | 9200 | ✅ Running |
| Airflow | openmetadata-ingestion | 8080 | ✅ Running |

---

## Quick Reference

**Start services:**
```powershell
cd "C:\Users\Hicham\OneDrive\python\learning\intelligent-semantic-layer"
docker-compose up -d
```

**OpenMetadata UI:**
- URL: http://localhost:8585
- Login: admin@open-metadata.org / admin
- Path: Databases → nyc_taxi_postgres → nyc_taxi → public

**Database connection:**
```
postgresql://taxi_user:taxi_password@127.0.0.1:5433/nyc_taxi
```

---

## Status Legend
- [ ] Not started
- [x] Completed
- [~] In progress

---

*Last updated: 2026-02-03 (Phase 10 complete - Mini Fabric IQ MVP)*
