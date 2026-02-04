#!/usr/bin/env python
"""
Mini Fabric IQ Demo - Intelligent Semantic Layer

This script demonstrates a small-scale proof-of-concept comparable to:
- Microsoft Fabric IQ
- Palantir AIP

Architecture:
    ┌──────────────────────────────────────────────────────────────────┐
    │                    User Natural Language Query                    │
    │              "Why are tips lower in Brooklyn?"                    │
    └─────────────────────────────┬────────────────────────────────────┘
                                  │
                                  ▼
    ┌──────────────────────────────────────────────────────────────────┐
    │                      AI Agent (Azure OpenAI)                      │
    │    - Understands intent                                          │
    │    - Calls appropriate tools                                      │
    │    - Synthesizes answer                                          │
    └─────────────────────────────┬────────────────────────────────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
                    ▼             ▼             ▼
    ┌──────────────────┐ ┌──────────────┐ ┌──────────────────┐
    │  Technical Layer │ │Semantic Layer│ │  Ontology Layer  │
    │  (OpenMetadata)  │ │  (Ibis/PG)   │ │   (OWL/RDF)      │
    │                  │ │              │ │                  │
    │  - Tables        │ │ - Metrics    │ │ - Concepts       │
    │  - Columns       │ │ - Dimensions │ │ - Rules          │
    │  - Lineage       │ │ - Joins      │ │ - Inference      │
    └────────┬─────────┘ └──────┬───────┘ └────────┬─────────┘
             │                  │                   │
             └──────────────────┼───────────────────┘
                                │
                                ▼
    ┌──────────────────────────────────────────────────────────────────┐
    │                   PostgreSQL (2.76M NYC Taxi Trips)               │
    └──────────────────────────────────────────────────────────────────┘

Usage:
    python scripts/demo_fabric_iq.py
    python scripts/demo_fabric_iq.py --interactive
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from unified_layer import UnifiedIntelligenceLayer


def print_header(title: str, char: str = "="):
    """Print a formatted header."""
    print()
    print(char * 70)
    print(f"  {title}")
    print(char * 70)


def print_subheader(title: str):
    """Print a formatted subheader."""
    print()
    print(f"--- {title} ---")


def demo_layer_overview(unified: UnifiedIntelligenceLayer):
    """Demo 1: Show what each layer provides."""
    print_header("LAYER OVERVIEW: What Each Layer Provides")

    summary = unified.summarize()

    print_subheader("1. Technical Layer (OpenMetadata)")
    print(f"   Status: {'Available' if summary['technical']['available'] else 'Not Running'}")
    if summary['technical']['available']:
        print(f"   Tables: {', '.join(summary['technical']['tables'])}")
        print(f"   Glossary Terms: {summary['technical']['glossary_terms']}")
    print("   Purpose: Catalog of WHAT data exists (tables, columns, types)")

    print_subheader("2. Semantic Layer (boring-semantic-layer + PostgreSQL)")
    print(f"   Status: {'Available' if summary['semantic']['available'] else 'Not Running'}")
    if summary['semantic']['available']:
        print(f"   Dimensions: {len(summary['semantic']['dimensions'])}")
        print(f"   Measures: {len(summary['semantic']['measures'])}")
    print("   Purpose: HOW to compute metrics (queries, joins, aggregations)")

    print_subheader("3. Ontology Layer (OWL/RDF)")
    print(f"   Classes: {summary['ontology']['classes']}")
    print(f"   Trip Types: {summary['ontology']['trip_types']}")
    print(f"   Zone Types: {summary['ontology']['zone_types']}")
    print(f"   Time Contexts: {summary['ontology']['time_contexts']}")
    print(f"   Inference Rules: {summary['ontology']['inference_rules']}")
    print("   Purpose: WHAT data means (business context, rules, reasoning)")


def demo_concept_understanding(unified: UnifiedIntelligenceLayer):
    """Demo 2: Show how a concept is understood across layers."""
    print_header("CONCEPT UNDERSTANDING: 'Manhattan'")

    concept = unified.understand_concept("Manhattan")

    print_subheader("Ontology Layer (Business Context)")
    if concept["ontology"]:
        print(f"   Label: {concept['ontology'].get('label')}")
        print(f"   Definition: {concept['ontology'].get('comment')}")
        if concept['ontology'].get('business_context'):
            print(f"   Business Context: {concept['ontology'].get('business_context')}")

    print_subheader("Semantic Layer (Computation)")
    if concept["semantic"]:
        print(f"   Type: {concept['semantic'].get('type')}")
        print(f"   Name: {concept['semantic'].get('name')}")
    else:
        print("   (Used as a filter value, not a dimension/measure)")

    print_subheader("Technical Layer (Catalog)")
    if concept["technical"]:
        term = concept["technical"].get("glossary_term", {})
        print(f"   Glossary Term: {term.get('name')}")
        if term.get('description'):
            desc = term['description'][:100] + "..." if len(term.get('description', '')) > 100 else term.get('description')
            print(f"   Description: {desc}")


def demo_question_answering(unified: UnifiedIntelligenceLayer):
    """Demo 3: Show question answering with real data."""
    print_header("QUESTION ANSWERING: Data + Context")

    questions = [
        "What is the total revenue by borough?",
        "How do tips vary by borough?",
        "Which zones have the most trips?"
    ]

    for question in questions:
        print_subheader(f"Q: {question}")

        answer = unified.answer_question(question)

        print(f"\nIdentified: {', '.join(answer['identified_concepts'])}")

        if answer["answer"]:
            print(f"\n{answer['answer']}")

        if answer["context"]:
            print("\nBusiness Context (from Ontology):")
            for ctx in answer["context"][:2]:
                print(f"  - {ctx}")


def demo_trip_classification(unified: UnifiedIntelligenceLayer):
    """Demo 4: Show ontology-based trip classification."""
    print_header("TRIP CLASSIFICATION: Ontology Inference")

    scenarios = [
        {
            "desc": "JFK Airport trip, Tuesday 8 AM",
            "params": {"rate_code_id": 2, "trip_distance": 15, "pickup_hour": 8, "day_of_week": 2}
        },
        {
            "desc": "Short Manhattan trip, Friday 11 PM",
            "params": {"trip_distance": 1.5, "pickup_hour": 23, "day_of_week": 5}
        },
        {
            "desc": "Long trip, Saturday afternoon",
            "params": {"trip_distance": 12, "pickup_hour": 14, "day_of_week": 6}
        }
    ]

    for scenario in scenarios:
        print_subheader(scenario["desc"])

        result = unified.classify_trip(**scenario["params"])

        print(f"   Classifications: {result['classifications']}")
        for detail in result["details"]:
            ctx = detail.get("context", "")
            ctx_short = ctx[:50] + "..." if ctx and len(ctx) > 50 else ctx
            print(f"   - {detail['type']}: {ctx_short}")


def demo_time_context(unified: UnifiedIntelligenceLayer):
    """Demo 5: Show time-based context."""
    print_header("TIME CONTEXT: When Matters")

    times = [
        (8, 1, "Monday 8 AM (Rush Hour)"),
        (14, 3, "Wednesday 2 PM (Off-Peak)"),
        (22, 5, "Friday 10 PM (Weekend Night)"),
        (11, 6, "Saturday 11 AM (Weekend Day)"),
    ]

    for hour, dow, desc in times:
        ctx = unified.get_time_context(hour, dow)
        demand = ctx.get("expected_demand", "N/A")
        print(f"   {desc}")
        print(f"      -> {ctx.get('label')} (Expected Demand: {demand})")


def demo_agent_interaction(unified: UnifiedIntelligenceLayer):
    """Demo 6: Show full agent interaction."""
    print_header("AI AGENT: Natural Language Interface")

    try:
        from agent import NYCTaxiAgent

        agent = NYCTaxiAgent()

        if not agent.client:
            print("\n   Azure OpenAI not configured. Skipping agent demo.")
            print("   Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY in .env")
            return

        questions = [
            "What is the total revenue by borough?",
            "Why might tips be different between boroughs?",
        ]

        for question in questions:
            print_subheader(f"User: {question}")

            response = agent.ask(question)

            # Truncate long answers for demo
            answer = response.answer
            if len(answer) > 500:
                answer = answer[:500] + "\n... [truncated for demo]"

            print(f"\nAgent: {answer}")
            print(f"\n[Tools: {', '.join(response.tools_used)}]")

    except Exception as e:
        print(f"\n   Could not initialize agent: {e}")


def interactive_mode(unified: UnifiedIntelligenceLayer):
    """Interactive Q&A mode."""
    print_header("INTERACTIVE MODE")
    print("\nAsk questions about NYC Taxi data. Type 'quit' to exit.")
    print("Examples:")
    print("  - What is the revenue by borough?")
    print("  - How do tips vary by borough?")
    print("  - Which zones are busiest?")

    try:
        from agent import NYCTaxiAgent
        agent = NYCTaxiAgent()
        use_agent = agent.client is not None
    except Exception:
        agent = None
        use_agent = False

    if not use_agent:
        print("\n(Running without AI agent - using pattern matching)")

    while True:
        print()
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not question:
            continue
        if question.lower() in ("quit", "exit", "q"):
            break

        if use_agent:
            response = agent.ask(question)
            print(f"\nAssistant: {response.answer}")
            if response.tools_used:
                print(f"\n[Tools: {', '.join(response.tools_used)}]")
        else:
            answer = unified.answer_question(question)
            if answer["answer"]:
                print(f"\nAnswer: {answer['answer']}")
            else:
                print("\nI couldn't understand that question. Try asking about revenue, tips, or zones.")


def main():
    """Run the Fabric IQ demo."""
    print()
    print("=" * 70)
    print("  MINI FABRIC IQ - Intelligent Semantic Layer Demo")
    print("  OpenMetadata + Semantic Layer + Ontology + AI Agent")
    print("=" * 70)

    # Check for interactive mode
    interactive = "--interactive" in sys.argv or "-i" in sys.argv

    # Initialize unified layer
    print("\nInitializing layers...")
    unified = UnifiedIntelligenceLayer()

    if interactive:
        interactive_mode(unified)
    else:
        # Run all demos
        demo_layer_overview(unified)
        demo_concept_understanding(unified)
        demo_question_answering(unified)
        demo_trip_classification(unified)
        demo_time_context(unified)
        demo_agent_interaction(unified)

        print_header("DEMO COMPLETE", "=")
        print("\nThis demo showed how combining 3 metadata layers enables:")
        print("  1. Data Discovery (Technical Layer - OpenMetadata)")
        print("  2. Metric Computation (Semantic Layer - boring-semantic-layer)")
        print("  3. Business Reasoning (Ontology Layer - OWL/RDF)")
        print("  4. Natural Language Interface (AI Agent - Azure OpenAI)")
        print("\nRun with --interactive for Q&A mode.")


if __name__ == "__main__":
    main()
