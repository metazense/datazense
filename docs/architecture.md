# Architecture Document: Intelligent Semantic Layer UI

> **Version:** 1.0 | **Date:** 2026-02-09

---

## 1. System Overview

```
                    ┌─────────────────────────────────────┐
                    │          FRONTEND (Next.js)          │
                    │                                      │
                    │  App Router + React Server Components│
                    │  shadcn/ui + Tailwind CSS            │
                    │  Vercel AI SDK (streaming)           │
                    │                                      │
                    │  Pages:                              │
                    │  - / (hero + chat)                   │
                    │                                      │
                    │  Components:                         │
                    │  - ChatInterface                     │
                    │  - InsightCard                       │
                    │  - MetricChart                       │
                    │  - SourceBadge                       │
                    │  - ReasoningPanel                    │
                    │  - SuggestedQuestions                │
                    └──────────────┬──────────────────────┘
                                   │
                                   │ HTTP/SSE (streaming)
                                   │ POST /api/chat
                                   │
                    ┌──────────────▼──────────────────────┐
                    │          BACKEND (FastAPI)           │
                    │                                      │
                    │  Wraps existing Python agent         │
                    │  Streaming SSE responses             │
                    │                                      │
                    │  Endpoints:                          │
                    │  - POST /api/chat (streaming)        │
                    │  - GET  /api/health                  │
                    │  - GET  /api/capabilities            │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │       EXISTING PYTHON AGENT          │
                    │       (src/agent.py)                 │
                    │                                      │
                    │  NYCTaxiAgent                        │
                    │  - 10 tools (function calling)       │
                    │  - Azure OpenAI (GPT-4)              │
                    │  - Agentic loop (max 5 iterations)   │
                    └──┬───────────┬───────────┬──────────┘
                       │           │           │
              ┌────────▼──┐  ┌────▼────┐  ┌───▼──────────┐
              │ TECHNICAL │  │SEMANTIC │  │  ONTOLOGY    │
              │  LAYER    │  │ LAYER   │  │   LAYER      │
              │           │  │         │  │              │
              │OpenMetadata│ │BSL+Ibis │  │ OWL/RDF     │
              │(optional) │  │+Postgres│  │ (rdflib)    │
              └───────────┘  └────┬────┘  └──────────────┘
                                  │
                           ┌──────▼──────┐
                           │ PostgreSQL  │
                           │ Port 5433   │
                           │ 2.76M trips │
                           └─────────────┘
```

---

## 2. Frontend Architecture

- **Based on:** Vercel ai-chatbot (https://github.com/vercel/ai-chatbot)
- **Framework:** Next.js 14+ (App Router)
- **Styling:** Tailwind CSS + shadcn/ui
- **Streaming:** Vercel AI SDK (`useChat` hook)

### 2.1 Folder Structure

```
frontend/
├── app/
│   ├── layout.tsx              # Root layout (fonts, theme)
│   ├── page.tsx                # Main page (hero + chat)
│   ├── globals.css             # Global styles + Tailwind
│   └── api/
│       └── chat/
│           └── route.ts        # API route → proxies to FastAPI backend
│
├── components/
│   ├── ui/                     # shadcn/ui base components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── badge.tsx
│   │   ├── collapsible.tsx
│   │   └── ...
│   │
│   ├── chat/
│   │   ├── chat-interface.tsx  # Main chat container
│   │   ├── chat-message.tsx    # Single message (user or agent)
│   │   ├── chat-input.tsx      # Input box with submit
│   │   └── suggested-questions.tsx  # Clickable starter questions
│   │
│   ├── insights/
│   │   ├── insight-card.tsx    # Boxed insight (warning, context, rule)
│   │   ├── metric-chart.tsx    # Auto-generated chart from data
│   │   ├── data-table.tsx      # Simple data table for results
│   │   └── source-badge.tsx    # Technical | Semantic | Ontology badge
│   │
│   ├── reasoning/
│   │   └── reasoning-panel.tsx # Collapsible tool call trace
│   │
│   └── layout/
│       ├── hero.tsx            # Landing hero section
│       ├── header.tsx          # Top bar
│       └── footer.tsx          # Footer
│
├── lib/
│   ├── api.ts                  # Backend API client
│   ├── types.ts                # TypeScript types
│   ├── parse-response.ts       # Parse agent response into structured format
│   └── utils.ts                # Utilities
│
├── hooks/
│   └── use-chat-agent.ts       # Custom hook wrapping useChat
│
├── public/
│   └── logo.svg
│
├── tailwind.config.ts
├── next.config.ts
├── package.json
└── tsconfig.json
```

### 2.2 Key Components

**ChatInterface**
- Manages conversation state
- Renders message list
- Handles input and submission
- Shows hero on empty state

**ChatMessage**
- Parses agent response into structured sections
- Renders: chart → text → insight cards → sources → follow-ups
- User messages render as simple text bubbles

**InsightCard**
- Four variants: WARNING (amber), CONTEXT (blue), RULE (purple), INSIGHT (green)
- Icon + title + description
- Compact, scannable

**MetricChart**
- Auto-detects chart type from data shape
- Borough/zone data → horizontal bar chart
- Time data → line chart
- Uses Recharts (included in Vercel template ecosystem)

**SourceBadge**
- Three badges: Technical (blue), Semantic (green), Ontology (purple)
- Shows which layers contributed to the answer
- Derived from `tools_used` in agent response

**ReasoningPanel**
- Collapsible accordion
- Shows each tool call: name, arguments, result summary
- Collapsed by default

**SuggestedQuestions**
- 4 clickable cards on hero screen
- 2-3 pill buttons after each response (follow-ups)

### 2.3 Data Flow (Chat Message)

1. User types question → POST to Next.js API route
2. Next.js API route → proxies to FastAPI backend (SSE stream)
3. FastAPI streams agent response tokens
4. Frontend receives stream → renders incrementally
5. On stream complete → parse response into structured format
6. Render: chart + text + insight cards + sources

---

## 3. Backend Architecture

- **Framework:** FastAPI
- **Purpose:** Thin wrapper around existing `NYCTaxiAgent`
- **Streaming:** Server-Sent Events (SSE)

### 3.1 Folder Structure

```
backend/
├── api/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── chat.py             # POST /api/chat (streaming)
│   │   └── health.py           # GET /api/health, /api/capabilities
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   └── agent_service.py    # Wraps NYCTaxiAgent for streaming
│   │
│   └── models/
│       ├── __init__.py
│       └── schemas.py          # Pydantic models for request/response
│
├── requirements.txt            # FastAPI, uvicorn, sse-starlette
└── Dockerfile
```

### 3.2 API Endpoints

#### `POST /api/chat`

**Request:**
```json
{
  "messages": [
    {"role": "user", "content": "Why are tips lower in Brooklyn?"}
  ]
}
```

**Response:** Server-Sent Events stream
```
data: {"type": "text", "content": "Brooklyn tips..."}
data: {"type": "tool_call", "name": "query_metrics", "args": {...}}
data: {"type": "tool_result", "name": "query_metrics", "result": {...}}
data: {"type": "text", "content": "...average $2.10..."}
data: {"type": "data", "chart_data": [...], "chart_type": "bar"}
data: {"type": "insight", "variant": "warning", "title": "...", "body": "..."}
data: {"type": "sources", "layers": ["semantic", "ontology"]}
data: {"type": "suggestions", "questions": ["Compare payment...", "..."]}
data: {"type": "done"}
```

#### `GET /api/health`

**Response:**
```json
{
  "status": "ok",
  "layers": {
    "technical": true,
    "semantic": true,
    "ontology": true,
    "llm": true
  }
}
```

#### `GET /api/capabilities`

**Response:**
```json
{
  "dimensions": ["pickup_zone.borough", "..."],
  "measures": ["trip_count", "total_revenue", "..."],
  "tools": ["query_metrics", "get_context", "..."],
  "suggested_questions": ["..."]
}
```

### 3.3 Streaming Approach

**Option A (simpler): Non-streaming**
- Agent runs to completion
- Return full structured response as JSON
- Frontend renders all at once
- Pros: Simpler, reliable
- Cons: User waits for full response (3-8 seconds)

**Option B (better UX): Streaming with post-processing**
- Stream LLM text tokens in real-time
- After stream completes, send structured data (chart, insights, sources)
- Frontend shows text streaming, then "pops in" the cards
- Pros: Feels responsive
- Cons: More complex

**Recommendation:** Start with Option A, upgrade to B after MVP works.

---

## 4. Response Parsing

The agent returns an `AgentResponse` with:
- `answer`: str (markdown text)
- `data`: list[dict] (metric results)
- `tools_used`: list[str]
- `reasoning_steps`: list[str]

The frontend parser (`parse-response.ts`) transforms this into:

```json
{
  "text": "Brooklyn tips average $2.10...",
  "chart": {
    "type": "bar",
    "data": [{"borough": "Manhattan", "avg_tip": 3.45}],
    "xKey": "borough",
    "yKey": "avg_tip"
  },
  "insights": [
    {
      "variant": "warning",
      "title": "Cash Tips Not Recorded",
      "body": "42% of Brooklyn payments are cash..."
    },
    {
      "variant": "context",
      "title": "Zone Demographics",
      "body": "Manhattan has business districts..."
    }
  ],
  "sources": ["semantic", "ontology"],
  "reasoning": [
    "Called query_metrics with {dimensions: ['borough'], measures: ['avg_tip']}",
    "Called get_context with {concept: 'Brooklyn'}"
  ],
  "suggestions": [
    "Compare payment types across boroughs",
    "Show airport trip revenue"
  ]
}
```

**Parsing strategy:**
- **Chart:** If `data[]` contains numeric values grouped by a category → auto-chart
- **Insights:** Parse markdown for callout patterns (`>`, `**`, `WARNING:`, `Note:`, etc.) OR have the backend explicitly tag insights
- **Sources:** Map `tools_used` to layer names
- **Suggestions:** Generate from context or have agent include them

---

## 5. Tech Stack Summary

| Component | Technology | Reason |
|-----------|------------|--------|
| Frontend | Next.js 14 (App Router) | Production-grade React framework |
| UI Components | shadcn/ui + Radix UI | Professional, accessible |
| Styling | Tailwind CSS | Fast, consistent |
| Charts | Recharts | Lightweight, React-native |
| Chat/Streaming | Vercel AI SDK | `useChat` hook, SSE handling |
| Backend | FastAPI | Python, async, fast |
| Agent | NYCTaxiAgent (existing) | Our 3-layer agent |
| LLM | Azure OpenAI GPT-4 | Existing integration |
| Database | PostgreSQL | 2.76M taxi trips |
| Ontology | rdflib + OWL/RDF | 55 classes, 10 rules |
| Semantic Layer | boring-semantic-layer | 23 measures, 12 dimensions |
| Package Manager | pnpm (frontend), uv (backend) | Fast, disk-efficient |

---

## 6. Deployment

### Development
- **Frontend:** `pnpm dev` (localhost:3000)
- **Backend:** `uvicorn api.main:app` (localhost:8000)
- **Database:** `docker-compose up -d` (localhost:5433)

### Production (when ready)
- **Frontend:** Vercel (auto-deploy from git)
- **Backend:** Azure App Service, Railway, or Fly.io
- **Database:** Existing Docker or managed Postgres

---

## 7. Environment Variables

### Frontend (`.env.local`)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Backend (`.env`)
```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DB=nyc_taxi
POSTGRES_USER=taxi_user
POSTGRES_PASSWORD=taxi_password
AZURE_OPENAI_ENDPOINT=https://...
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview
CORS_ORIGINS=http://localhost:3000
```
