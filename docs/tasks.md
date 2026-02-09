# Implementation Tasks: Intelligent Semantic Layer UI

> **Version:** 1.0 | **Date:** 2026-02-09

**Legend:**
- `[ ]` Pending | `[~]` In Progress | `[x]` Complete
- `[B]` Backend | `[F]` Frontend | `[I]` Integration

---

## Phase 1: Backend API (FastAPI wrapper)

> **Priority:** MUST DO FIRST — Frontend depends on this

- [ ] **1.1** `[B]` Create backend project structure
  - Create `backend/` directory
  - Create `api/main.py` with FastAPI app
  - Create `api/routes/`, `api/services/`, `api/models/`
  - Add `requirements.txt` (fastapi, uvicorn, sse-starlette, python-dotenv)
  - Add CORS middleware for frontend

- [ ] **1.2** `[B]` Create Pydantic schemas
  - `ChatRequest`: messages list (role + content)
  - `ChatResponse`: answer, data, tools_used, reasoning_steps
  - `InsightItem`: variant, title, body
  - `HealthResponse`: status, layer availability
  - `CapabilitiesResponse`: dimensions, measures, tools, suggestions

- [ ] **1.3** `[B]` Create agent service wrapper
  - Import and initialize `NYCTaxiAgent`
  - Method: `ask(messages)` → structured response
  - Parse agent response into frontend-friendly format
  - Extract chart data from query results
  - Extract insights from answer text
  - Map `tools_used` to layer sources
  - Generate follow-up suggestions

- [ ] **1.4** `[B]` Implement `POST /api/chat` endpoint
  - Accept `ChatRequest`
  - Call agent service
  - Return structured `ChatResponse`
  - Handle errors gracefully

- [ ] **1.5** `[B]` Implement `GET /api/health` endpoint
  - Check all layer availability
  - Return layer status

- [ ] **1.6** `[B]` Implement `GET /api/capabilities` endpoint
  - Return available dimensions, measures, tools
  - Return suggested starter questions

- [ ] **1.7** `[B]` Test backend independently
  - curl `POST /api/chat` with test question
  - Verify response structure matches schema
  - Verify all 3 layers respond
  - *Depends on: 1.1-1.6*

---

## Phase 2: Frontend Scaffold

> **Priority:** Can start in parallel with Phase 1

- [ ] **2.1** `[F]` Initialize Next.js project
  - `npx create-next-app@latest frontend` (App Router, TypeScript, Tailwind)
  - Install shadcn/ui (`npx shadcn@latest init`)
  - Install Recharts
  - Configure Tailwind theme (professional colors, typography)
  - Set up fonts (Inter or Geist)

- [ ] **2.2** `[F]` Create TypeScript types
  - `ChatMessage` type (role, content, structured data)
  - `InsightCard` type (variant, title, body)
  - `ChartData` type (data array, chart type, keys)
  - `AgentResponse` type (text, chart, insights, sources, suggestions)
  - `Layer` type enum (technical, semantic, ontology)

- [ ] **2.3** `[F]` Install shadcn/ui components
  - button, card, badge, input, collapsible
  - scroll-area, separator, skeleton
  - avatar (for user/agent icons)

- [ ] **2.4** `[F]` Create root layout
  - `app/layout.tsx` with fonts, metadata, theme
  - Professional color scheme
  - Responsive container

---

## Phase 3: Core UI Components

> **Priority:** Build bottom-up (small components first)

- [ ] **3.1** `[F]` Build `SourceBadge` component
  - Three variants: Technical (blue), Semantic (green), Ontology (purple)
  - Small pill-shaped badge with label
  - Props: layer name, optional tooltip

- [ ] **3.2** `[F]` Build `InsightCard` component
  - Four variants: WARNING (amber), CONTEXT (blue), RULE (purple), INSIGHT (green)
  - Icon (left) + title (bold) + body text
  - Bordered card with colored left accent
  - Props: variant, title, body

- [ ] **3.3** `[F]` Build `MetricChart` component
  - Auto-detect chart type from data shape
  - Horizontal bar chart for categorical data (borough, zone)
  - Clean, minimal styling (no grid lines, subtle colors)
  - Responsive width, fixed height (~200px)
  - Props: data, xKey, yKey, chartType

- [ ] **3.4** `[F]` Build `DataTable` component
  - Simple table for metric results
  - Auto-format numbers (currency, percentages)
  - Compact styling
  - Props: data, columns

- [ ] **3.5** `[F]` Build `ReasoningPanel` component
  - Collapsible accordion (collapsed by default)
  - Shows list of tool calls with name + arguments
  - Monospace font for technical details
  - "Show reasoning" toggle button

- [ ] **3.6** `[F]` Build `SuggestedQuestions` component
  - Clickable cards/pills
  - Two modes:
    - a) Hero mode: 4 large cards with icons and descriptions
    - b) Follow-up mode: 2-3 small pills below a response
  - Props: `questions[]`, `onSelect` callback, `mode`

---

## Phase 4: Chat Interface

> **Priority:** Core UX — depends on Phase 3 components

- [ ] **4.1** `[F]` Build `ChatInput` component
  - Text input with send button
  - Submit on Enter, Shift+Enter for newline
  - Disabled state while agent is responding
  - Placeholder text: *"Ask about NYC taxi data..."*

- [ ] **4.2** `[F]` Build `ChatMessage` component (user)
  - Simple text bubble, right-aligned
  - User avatar/icon

- [ ] **4.3** `[F]` Build `ChatMessage` component (agent)
  - Structured layout:
    1. `MetricChart` (if data present)
    2. Markdown-rendered text
    3. `InsightCards` (if insights present)
    4. `SourceBadges` (from tools_used)
    5. `ReasoningPanel` (collapsible)
    6. `SuggestedQuestions` (follow-ups)
  - Agent avatar/icon

- [ ] **4.4** `[F]` Build `ChatInterface` container
  - Scrollable message list
  - Auto-scroll to bottom on new message
  - Hero state (no messages yet) → show `SuggestedQuestions`
  - Chat state (messages exist) → show conversation

- [ ] **4.5** `[F]` Build main page (`app/page.tsx`)
  - Header with logo/title
  - ChatInterface as main content
  - Responsive layout (works on laptop screens)
  - *Depends on: 3.1-3.6, 4.1-4.4*

---

## Phase 5: Frontend-Backend Integration

> **Priority:** Connect everything

- [ ] **5.1** `[I]` Create API client (`lib/api.ts`)
  - Function: `sendMessage(messages)` → `AgentResponse`
  - POST to `/api/chat`
  - Parse response JSON
  - Error handling

- [ ] **5.2** `[I]` Create response parser (`lib/parse-response.ts`)
  - Parse agent answer text into sections
  - Extract chart data from `response.data`
  - Detect insight patterns in text
  - Map `tools_used` to source layers
  - Generate follow-up suggestions

- [ ] **5.3** `[I]` Create Next.js API route (`app/api/chat/route.ts`)
  - Proxy requests from frontend to FastAPI backend
  - Handle CORS
  - Stream or forward responses

- [ ] **5.4** `[I]` Wire `ChatInterface` to API
  - On submit: call API, show loading state
  - On response: parse and render structured message
  - Handle errors with user-friendly messages

- [ ] **5.5** `[I]` End-to-end test
  - Start backend (`uvicorn`)
  - Start frontend (`pnpm dev`)
  - Test all 4 suggested questions
  - Verify: chart renders, insights render, sources show
  - *Depends on: Phase 1 (backend), Phase 4 (frontend)*

---

## Phase 6: Polish and Demo Readiness

> **Priority:** Make it pitch-ready

- [ ] **6.1** `[F]` Loading states
  - Skeleton loader while agent processes
  - Typing indicator (3 dots animation)
  - Smooth transitions for insight cards appearing

- [ ] **6.2** `[F]` Error states
  - Backend unreachable → friendly message
  - Agent error → show error with retry button
  - Empty response → "I couldn't generate an answer"

- [ ] **6.3** `[F]` Responsive design check
  - Test on 13" laptop (primary demo device)
  - Test on external monitor
  - Ensure chat doesn't overflow

- [ ] **6.4** `[F]` Typography and spacing audit
  - Consistent heading sizes
  - Proper line heights in insight cards
  - Chart label readability
  - Color contrast accessibility

- [ ] **6.5** `[F]` Hero screen polish
  - Tagline: *"Ask your data WHY, not just WHAT"*
  - Subtitle: brief value proposition
  - 4 starter question cards with icons
  - Clean, impressive first impression

- [ ] **6.6** `[I]` Demo rehearsal
  - Run through 4 demo questions
  - Check response times (target: < 8 seconds per answer)
  - Screenshot for pitch deck
  - Fix any visual glitches

---

## Phase 7: Optional Enhancements

> **Priority:** Nice-to-have after MVP

- [ ] **7.1** `[I]` Streaming responses
  - Upgrade FastAPI to SSE streaming
  - Use Vercel AI SDK `useChat` hook
  - Text streams in real-time
  - Cards appear after stream completes

- [ ] **7.2** `[F]` Dark mode support
  - Toggle in header
  - Tailwind `dark:` classes

- [ ] **7.3** `[F]` Mobile responsive
  - Stack layout for narrow screens
  - Touch-friendly input

- [ ] **7.4** `[B]` Chat history persistence
  - Store conversations in PostgreSQL or localStorage
  - Sidebar with past conversations

- [ ] **7.5** `[F]` Export conversation
  - Copy to clipboard button
  - Download as markdown

---

## Task Dependencies

```
Phase 1 (Backend) ──────────────────────┐
                                         ├──→ Phase 5 (Integration) ──→ Phase 6 (Polish)
Phase 2 (Scaffold) → Phase 3 (Components)│
                     → Phase 4 (Chat UI) ┘

Phase 7 (Enhancements) → After Phase 6 is complete
```

---

## Task Summary

| Phase | Description | Tasks |
|-------|-------------|-------|
| Phase 1 | Backend API | 7 tasks |
| Phase 2 | Frontend Scaffold | 4 tasks |
| Phase 3 | Core Components | 6 tasks |
| Phase 4 | Chat Interface | 5 tasks |
| Phase 5 | Integration | 5 tasks |
| Phase 6 | Polish | 6 tasks |
| Phase 7 | Enhancements | 5 tasks (optional) |
| **Total** | | **38 tasks (33 required + 5 optional)** |
