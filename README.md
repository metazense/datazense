# DataZense

**Ask your data WHY, not just WHAT.**

DataZense is an AI-powered data analytics platform that combines three metadata layers to answer natural language questions with real business context — not just numbers.

## How It Works

DataZense routes every question through three intelligent layers:

```
User Question  -->  AI Agent  -->  Three Layers  -->  Contextual Answer
                                       |
                    +------------------+------------------+
                    |                  |                  |
             Technical Layer    Semantic Layer     Ontology Layer
             (OpenMetadata)      (Ibis + SQL)       (OWL/RDF)
                    |                  |                  |
                    +------------------+------------------+
                                       |
                               PostgreSQL DB
```

| Layer | What it does | Example |
|-------|-------------|---------|
| **Technical** | Discovers tables, columns, glossary terms from OpenMetadata catalog | "What tables exist?" |
| **Semantic** | Computes metrics (revenue, tips, counts) with dimensions (borough, zone, payment type) | "Total revenue by borough?" |
| **Ontology** | Applies domain knowledge and inference rules to explain patterns | "Why are Brooklyn tips lower?" |

The AI agent decides which layers to query and combines their results into a single answer with charts, tables, and insight cards.

## Datasets

| Dataset | Description | Records |
|---------|-------------|---------|
| **NYC Taxi** | Yellow taxi trip data with fare, tip, zone, and payment info | 2.76M trips |
| **Healthcare** | Synthea-generated patient encounters, conditions, and costs | Synthetic |

## Quick Start

### Prerequisites

- **Python 3.11+** with [uv](https://docs.astral.sh/uv/) package manager
- **Docker & Docker Compose**
- **Node.js 18+** with [pnpm](https://pnpm.io/)
- **Azure OpenAI API** access (endpoint + API key)

### 1. Clone and configure

```bash
git clone https://github.com/metazense/datazense.git
cd datazense

cp .env.example .env
# Edit .env with your Azure OpenAI credentials and Postgres settings
```

### 2. Start infrastructure

```bash
docker-compose up -d
```

This starts PostgreSQL (port 5433), OpenMetadata (port 8585), Elasticsearch, and Airflow.

Wait ~60 seconds for services to be healthy, then verify:

```bash
docker-compose ps
```

### 3. Install Python dependencies and load data

```bash
uv sync
uv run python scripts/load_data.py
```

### 4. Start the backend API

```bash
uvicorn backend.api.main:app --reload
```

Backend runs at `http://localhost:8000` — API docs at `http://localhost:8000/docs`

### 5. Start the frontend

```bash
cd frontend
pnpm install
pnpm dev
```

Frontend runs at `http://localhost:3000`

### 6. Open the app

Navigate to [http://localhost:3000](http://localhost:3000) and start asking questions.

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Required | Description |
|----------|----------|-------------|
| `POSTGRES_HOST` | Yes | Database host (default: `localhost`) |
| `POSTGRES_PORT` | Yes | Database port (default: `5433`) |
| `POSTGRES_DB` | Yes | Database name (default: `nyc_taxi`) |
| `POSTGRES_USER` | Yes | Database user |
| `POSTGRES_PASSWORD` | Yes | Database password |
| `AZURE_OPENAI_ENDPOINT` | Yes | Azure OpenAI endpoint URL |
| `AZURE_OPENAI_API_KEY` | Yes | Azure OpenAI API key |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Yes | Model deployment name (e.g. `gpt-4`) |
| `OPENMETADATA_HOST` | No | OpenMetadata URL (default: `http://localhost:8585`) |

## Project Structure

```
datazense/
├── backend/api/          # FastAPI backend (routes, services, models)
├── frontend/             # Next.js + React frontend
├── ontology/             # OWL/RDF domain knowledge files
├── scripts/              # Data loading and utility scripts
├── src/                  # Core layer implementations
├── docker-compose.yml    # Infrastructure (Postgres, OpenMetadata)
├── semantic_model.yml    # NYC Taxi semantic model definitions
└── semantic_model_healthcare.yml
```

## Tech Stack

- **Backend:** FastAPI, Azure OpenAI (function calling), Ibis, rdflib
- **Frontend:** Next.js 16, React 19, Tailwind CSS, Recharts, shadcn/ui
- **Data:** PostgreSQL, OpenMetadata, OWL/RDF ontologies
- **Infra:** Docker Compose, uv, pnpm

## License

See [LICENSE](LICENSE) for details.
