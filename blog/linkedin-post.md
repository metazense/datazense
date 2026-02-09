# LinkedIn Post: Beyond Semantic Layers

---

**Version 1: The Hook (Recommended)**

---

Your semantic layer can tell you Manhattan generates $44M in taxi revenue.

It can't tell you *why*.

I've been thinking about this gap for months. Semantic layers (dbt Metrics, Cube, Looker) solve the "single source of truth" problem brilliantly. Everyone calculates revenue the same way. No more debates.

But ask "Why is Manhattan revenue 5x higher than Brooklyn?" and you get... silence.

The calculation layer has no concept of:
→ Business districts vs residential zones
→ Tourist behavior vs local commuters
→ The fact that cash tips aren't recorded (!)

So I built something different: a 3-layer architecture that answers "what," "how," AND "why."

**The Three Layers:**

1. Technical Layer (OpenMetadata) → What data exists
2. Semantic Layer (Ibis + PostgreSQL) → How to compute metrics
3. Ontology Layer (OWL/RDF) → Why patterns exist

The result? An AI agent that doesn't just compute—it explains:

```
User: "Why are tips lower in Brooklyn vs Manhattan?"

Agent: Brooklyn tips average $2.10 vs Manhattan's $3.45.

Several factors:
1. Cash tips aren't recorded. Brooklyn has 42% cash vs 30% in Manhattan.
2. Manhattan has more tourists/business travelers who tip higher.
3. Brooklyn is residential—routine local trips, not expense accounts.

Important: Lower recorded tips ≠ lower actual tips.
```

This isn't RAG over documentation. It's structured domain knowledge that AI can reason with.

Prukalpa Sankar put it perfectly: "Meaning isn't the same as measurement."

Semantic layers excel at measurement. Ontologies provide meaning.

The code is open source. Link in comments.

What do you think—is this the missing piece for AI-native analytics?

---

**Version 2: Shorter/Punchier**

---

Semantic layers answer "what" and "how."

They can't answer "why."

Ask your semantic layer: "What is revenue by borough?"
→ Manhattan $44M, Brooklyn $8M ✓

Ask: "Why is Manhattan 5x higher?"
→ ...silence

The calculation layer has no concept of business districts, tourist zones, or why cash tips aren't recorded.

So I combined three layers:
• Semantic Layer → computes metrics
• Ontology Layer → explains patterns
• AI Agent → reasons with both

Now when you ask "Why are tips lower in Brooklyn?", you get:

"Brooklyn tips are $2.10 vs Manhattan's $3.45. But cash tips aren't recorded in the data—Brooklyn has 42% cash payments vs 30% in Manhattan. Lower recorded tips ≠ lower actual tips."

That's domain knowledge, not just data.

Built with: PostgreSQL, boring-semantic-layer, OWL/RDF, Azure OpenAI
Dataset: 2.76M NYC taxi trips

Open source: [link in comments]

Inspired by @Simon Späti's semantic layer tutorial and @Prukalpa Sankar's work on ontologies.

---

**Version 3: Question-Led (High Engagement)**

---

Can your data stack answer "why"?

I asked our semantic layer: "Why are tips lower in Brooklyn than Manhattan?"

Response: [error - no such capability]

Semantic layers compute metrics brilliantly. But they encode *calculations*, not *understanding*.

They don't know that:
→ Cash tips aren't recorded (Brooklyn has more cash payments)
→ Manhattan has business districts with expense-account travelers
→ Tourist zones have different tipping patterns than residential

So I added a second layer: a domain ontology.

Not a knowledge graph. Not RAG. A formal OWL/RDF model encoding:
• 55 business concepts (trip types, zone types, time contexts)
• 10 inference rules (when tips are missing, why patterns exist)
• Business context an AI agent can query

Now the same question gets:

"Brooklyn tips average $2.10 vs Manhattan's $3.45. This reflects payment mix (cash tips unrecorded), demographics (tourists tip more), and zone type (business districts vs residential). Lower recorded tips ≠ lower actual tips."

Data + context = insight.

Measurement + meaning = understanding.

Code: github.com/metazense/intelligent-semantic-layer

Is this the future of AI-native analytics? Or am I overcomplicating things?

---

**Hashtags (pick 5-7):**

#DataEngineering #SemanticLayer #Analytics #AI #LLM #DataArchitecture #Ontology #MetadataManagement #dbt #DataScience #MachineLearning

---

**Image suggestion:**

Create a simple diagram showing:
```
Traditional:  Question → Semantic Layer → Numbers
                                          (no explanation)

New Approach: Question → AI Agent → Semantic Layer → Numbers
                              ↓
                         Ontology → Explanation
```

---

**Posting tips:**

1. Post Version 1 or 3 (longer posts with substance perform well)
2. Add the GitHub link as first comment (not in post body)
3. Tag Simon Späti and Prukalpa Sankar if you want their attention
4. Best times: Tuesday-Thursday, 8-10 AM your audience's timezone
5. Engage with comments in first hour
