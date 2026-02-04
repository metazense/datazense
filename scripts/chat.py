#!/usr/bin/env python
"""
NYC Taxi AI Assistant - Interactive Chat

A conversational interface to explore NYC taxi data using natural language.
Powered by Azure OpenAI + Semantic Layer + Ontology.

Usage:
    python scripts/chat.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def main():
    print()
    print("=" * 60)
    print("  NYC Taxi AI Assistant")
    print("  Ask questions about taxi trips, revenue, tips, and more")
    print("=" * 60)
    print()

    # Initialize agent
    print("Initializing...")
    from agent import NYCTaxiAgent
    agent = NYCTaxiAgent()

    if not agent.client:
        print("\n[Warning] Azure OpenAI not configured - running in offline mode")
        print("For full AI capabilities, set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY in .env")

    print()
    print("Ready! Type your questions below. Type 'quit' to exit.")
    print()
    print("Example questions:")
    print("  - What is the total revenue by borough?")
    print("  - Why are tips lower in Brooklyn?")
    print("  - Which zones have the most trips?")
    print("  - How do airport trips compare to regular trips?")
    print("-" * 60)

    while True:
        try:
            print()
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not question:
            continue

        if question.lower() in ("quit", "exit", "q", "bye"):
            print("\nGoodbye!")
            break

        # Special commands
        if question.lower() == "help":
            print("\nAvailable commands:")
            print("  help     - Show this help")
            print("  summary  - Show agent capabilities")
            print("  quit     - Exit the chat")
            print("\nOr just ask any question about NYC taxi data!")
            continue

        if question.lower() == "summary":
            summary = agent.summary()
            print(f"\nAgent Status:")
            print(f"  LLM: {'Connected' if summary['llm_available'] else 'Offline'}")
            print(f"  Semantic Layer: {'Ready' if summary['semantic_layer_available'] else 'Not Available'}")
            print(f"  Ontology: {'Ready' if summary['ontology_available'] else 'Not Available'}")
            print(f"\nAvailable dimensions: {len(summary['semantic_dimensions'])}")
            print(f"Available measures: {len(summary['semantic_measures'])}")
            print(f"Ontology classes: {summary['ontology_summary'].get('classes', 0)}")
            continue

        # Ask the agent
        print()
        response = agent.ask(question)

        print(f"Assistant: {response.answer}")

        if response.tools_used:
            print(f"\n[Tools: {', '.join(response.tools_used)}]")

        if response.error:
            print(f"\n[Error: {response.error}]")


if __name__ == "__main__":
    main()
