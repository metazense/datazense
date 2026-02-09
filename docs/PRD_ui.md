# Product Requirements Document: Intelligent Semantic Layer UI

> **Version:** 1.0 | **Date:** 2026-02-09 | **Status:** Draft

---

## 1. Product Vision

Build a professional web UI that demonstrates the Intelligent Semantic Layer concept: an AI agent that doesn't just compute metrics—it explains WHY data patterns exist.

**Target:** Business pitch demo. Must look like a product, not a prototype.

**Core message:** *"Your semantic layer tells you WHAT. Ours tells you WHY."*

---

## 2. Problem Statement

Traditional semantic layers (dbt Metrics, Cube, Looker) compute metrics consistently but cannot explain them:

```
User: "Why are tips lower in Brooklyn?"
Traditional: [no capability]
Ours: "Brooklyn has 42% cash payments (tips not recorded), plus
       residential zones with routine local trips vs Manhattan's
       business/tourist districts."
```

No tool today combines metric computation with domain reasoning in a single interface.

---

## 3. Target Users (for pitch)

| Priority | Audience | Context |
|----------|----------|---------|
| Primary | Data team leads, CDOs, VPs of Analytics | Decision makers evaluating tools |
| Secondary | Data analysts exploring unfamiliar datasets | Day-to-day users |
| Tertiary | Investors evaluating the concept | Funding conversations |

These users will see the demo for 5-10 minutes. First impressions matter. The UI must look professional from second one.

---

## 4. Core Features (MVP)

### F1: Chat Interface
- Natural language input
- Streaming responses from AI agent
- Conversation history within session
- Suggested starter questions
- Follow-up question suggestions after each answer

### F2: Insight Cards (the differentiator)
- Structured answer format, NOT wall of text
- Data section: table/chart showing computed metrics
- Explanation section: boxed insight cards explaining "why"
- Warning callouts for data caveats (e.g., "cash tips not recorded")
- Source attribution (which layer provided each piece)

### F3: Layer Visibility (subtle, not primary)
- Collapsible "reasoning" panel showing tools called
- Color-coded badges: Technical (blue), Semantic (green), Ontology (purple)
- Shows which layer answered which part
- Collapsed by default—available for technical audiences

### F4: Data Visualization (supporting role)
- Auto-generated bar/line charts for metric results
- Inline within chat messages
- Simple and clean (Plotly or Recharts)
- Charts support the narrative, NOT the hero

### F5: Landing/Hero Section
- Brief tagline and value proposition
- 3-4 suggested questions that showcase each layer
- Clean, professional look before conversation starts

---

## 5. Non-Features (explicitly out of scope)

- User authentication / multi-user (not needed for demo)
- Chat history persistence across sessions
- File upload
- Dashboard builder / drag-and-drop
- Knowledge graph visualization (discussed and rejected—distracts from value)
- Custom theme/branding editor
- Export to PDF/PPT

---

## 6. User Flow

**Step 1:** User lands on hero screen
- Sees tagline: *"Ask your data WHY, not just WHAT"*
- Sees 4 suggested questions as clickable cards
- Clean, professional design

**Step 2:** User clicks a suggested question or types their own
- Chat message appears
- Streaming response begins

**Step 3:** Agent response renders as structured insight
- Mini chart (if metric data returned)
- Explanation cards (from ontology)
- Warning callout (if applicable)
- Source badges (Technical / Semantic / Ontology)
- Follow-up suggestions

**Step 4:** User continues conversation
- Follow-up questions maintain context
- Each response follows same structured format

---

## 7. Design Principles

| Principle | Description |
|-----------|-------------|
| **P1: Explanation is the hero** | Insight cards and text explanations are the primary content. Charts and data tables are supporting evidence. |
| **P2: Professional, not flashy** | Clean typography, muted colors, proper spacing. Should look like a B2B SaaS product, not a hackathon project. |
| **P3: Show, don't tell** | Don't explain the architecture—demonstrate it. The layer badges subtly show the 3-layer concept in action. |
| **P4: Progressive disclosure** | Simple answer first. Reasoning details available on click. Technical users can expand. Business users don't need to. |
| **P5: Fast first impression** | Hero screen loads instantly. First response streams. No loading spinners for more than 2 seconds on initial load. |

---

## 8. Suggested Starter Questions (showcase each layer)

| # | Question | Layer Showcased |
|---|----------|-----------------|
| Q1 | "What tables are available in the database?" | Technical Layer (OpenMetadata) |
| Q2 | "What is the total revenue by borough?" | Semantic Layer (metrics computation) |
| Q3 | "Why are tips lower in Brooklyn than Manhattan?" | Ontology Layer (reasoning + context) |
| Q4 | "What is revenue by borough and why does Manhattan dominate?" | Multi-Layer (all three together) |

---

## 9. Response Format Specification

Each agent response should render with this structure:

```
┌────────────────────────────────────────────────────────────────┐
│ [Optional: mini chart - bar/line]                             │
│                                                                │
│ [Answer text - markdown rendered]                             │
│                                                                │
│ [Insight Card 1: warning/context/rule - boxed, colored]       │
│ [Insight Card 2: if applicable]                               │
│                                                                │
│ [Source badges: Technical | Semantic | Ontology]              │
│ [Collapsible: Reasoning Steps - tools called]                 │
│                                                                │
│ [Follow-up suggestions: 2-3 clickable pills]                 │
└────────────────────────────────────────────────────────────────┘
```

**Insight Card Types:**

| Variant | Color | Purpose | Example |
|---------|-------|---------|---------|
| WARNING | Red/Orange | Data caveats | "Cash tips not recorded" |
| CONTEXT | Blue | Domain knowledge | "Manhattan has business districts" |
| RULE | Purple | Inference rule applied | "ManhattanDominance rule" |
| INSIGHT | Green | Analytical conclusion | "Lower recorded ≠ lower actual" |

---

## 10. Technical Constraints

| Component | Technology |
|-----------|------------|
| Backend | Existing Python agent (`src/agent.py`) wrapped in FastAPI |
| Frontend | Next.js (App Router) based on Vercel ai-chatbot template |
| Styling | Tailwind CSS + shadcn/ui (professional component library) |
| Charts | Recharts (included in Vercel template) or Plotly |
| Deployment | Vercel (frontend) + any Python host (backend) |
| LLM | Azure OpenAI (GPT-4) via existing agent |
| Database | PostgreSQL (port 5433) with 2.76M taxi trips |

---

## 11. Success Criteria

| # | Criteria |
|---|----------|
| S1 | First-time viewer understands the value within 30 seconds |
| S2 | "Why" questions produce structured insight cards, not text walls |
| S3 | Layer badges make the 3-layer architecture visible without explanation |
| S4 | Professional enough that a CDO wouldn't dismiss it as a "toy" |
| S5 | Full demo flow (4 questions) completes in under 3 minutes |

---

## 12. Inspiration / References

- **Vercel ai-chatbot:** Chat UX, streaming, component library
- **Perplexity.ai:** Source attribution, structured answers
- **ChatGPT:** Conversational flow, follow-up suggestions
- **Linear.app:** Clean B2B aesthetic, typography, spacing
