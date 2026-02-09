"""
Healthcare AI Agent - Powered by Azure OpenAI + Semantic Layer + Ontology

Combines:
1. Healthcare Semantic Layer (boring-semantic-layer + PostgreSQL) - Metric computation
2. Healthcare Ontology Layer (OWL/RDF, SNOMED CT-inspired) - Business context
3. Azure OpenAI (GPT-4) - Natural language understanding

Same agentic loop pattern as NYCTaxiAgent but for healthcare data.

Usage:
    from healthcare_agent import HealthcareAgent

    agent = HealthcareAgent()
    response = agent.ask("What conditions drive the most cost?")
"""

import json
import os
from typing import Any, Dict, List

from dotenv import load_dotenv

from agent import AgentResponse  # reuse the shared dataclass

load_dotenv()


class HealthcareAgent:
    """AI Agent for healthcare data analysis using Synthea synthetic data."""

    SYSTEM_PROMPT = """You are an expert healthcare data analyst with access to a 3-layer metadata architecture:

1. **Technical Layer**: Database catalog with tables, columns, types
2. **Semantic Layer (PostgreSQL)**: Metric computation with dimensions and measures
3. **Ontology Layer (OWL/RDF, SNOMED CT-inspired)**: Business context, clinical rules, domain knowledge

## Available Models
- **encounters** (primary fact table): Healthcare visits with cost and coverage data
- **conditions**: Patient diagnoses with SNOMED CT codes
- **medications**: Prescribed medications with costs

## Available Dimensions (for query_metrics)
Encounter dimensions: encounter_class, description, reason_description
Joined patient dims: patient.gender, patient.race, patient.ethnicity, patient.county, patient.city
Joined org dims: organization.name
Joined payer dims: payer.name

## Available Measures (for query_metrics on encounters model)
- encounter_count: Number of encounters
- total_claim_cost, avg_claim_cost: Total and average billed cost
- total_payer_coverage, avg_payer_coverage: Insurance coverage amounts
- total_out_of_pocket, avg_out_of_pocket: Patient financial burden
- emergency_count, inpatient_count, ambulatory_count, wellness_count: By type

## Condition Measures (for query_conditions)
- condition_count: Number of condition records

## Medication Measures (for query_medications)
- medication_count, total_medication_cost, avg_medication_cost, avg_dispenses

## Important Business Rules
1. Out-of-pocket = total_claim_cost - payer_coverage
2. Chronic conditions (diabetes, hypertension) drive 75%+ of spending
3. Emergency visits cost 5-10x more than ambulatory for similar conditions
4. Income and race are key social determinants of health
5. Wellness encounters correlate with lower emergency utilization

## Your Approach
1. For data questions: Use query_metrics / query_conditions / query_medications
2. For "why" questions: Use get_context and explain_metric
3. For classification: Use classify_encounter with ontology rules
4. For analysis guidance: Use get_analysis_context
5. NEVER make up numbers - always query the data
6. Provide clinical and business context from the ontology

Be concise but informative. Include actual numbers when available."""

    TOOLS = [
        {
            "type": "function",
            "function": {
                "name": "query_metrics",
                "description": "Query encounter cost/volume metrics grouped by dimensions. Use this for cost analysis, utilization, and demographic breakdowns.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dimensions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Dimensions to group by: encounter_class, patient.gender, patient.race, patient.county, organization.name, payer.name"
                        },
                        "measures": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Measures: encounter_count, total_claim_cost, avg_claim_cost, total_payer_coverage, avg_payer_coverage, total_out_of_pocket, avg_out_of_pocket, emergency_count, inpatient_count, ambulatory_count, wellness_count"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum rows (default 10)"
                        }
                    },
                    "required": ["dimensions", "measures"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "query_conditions",
                "description": "Query condition (diagnosis) frequency and patterns. Use for 'what conditions' questions.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dimensions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Dimensions: description, code, patient.gender, patient.race"
                        },
                        "measures": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Measures: condition_count"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum rows (default 20)"
                        }
                    },
                    "required": ["dimensions", "measures"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "query_medications",
                "description": "Query medication cost and volume. Use for drug spending analysis.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dimensions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Dimensions: description, code, patient.gender, patient.race"
                        },
                        "measures": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Measures: medication_count, total_medication_cost, avg_medication_cost, avg_dispenses"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum rows (default 20)"
                        }
                    },
                    "required": ["dimensions", "measures"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_context",
                "description": "Get business/clinical context for a healthcare concept from the ontology.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "concept": {
                            "type": "string",
                            "description": "Concept name: Patient, Encounter, Condition, Medication, Diabetes, Hypertension, EmergencyEncounter, etc."
                        }
                    },
                    "required": ["concept"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_measure_info",
                "description": "Get detailed information about a healthcare metric.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "measure_name": {
                            "type": "string",
                            "description": "Measure name: encounter_count, total_claim_cost, avg_claim_cost, etc."
                        }
                    },
                    "required": ["measure_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "explain_metric",
                "description": "Explain why a healthcare metric has a certain value with business context.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "metric": {"type": "string", "description": "The metric name"},
                        "value": {"type": "number", "description": "The observed value"},
                        "context": {
                            "type": "object",
                            "description": "Context like encounter_class, gender, race",
                            "additionalProperties": {"type": "string"}
                        }
                    },
                    "required": ["metric", "value"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "classify_encounter",
                "description": "Classify an encounter using ontology rules (cost level, coverage gap, type).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "encounter_class": {
                            "type": "string",
                            "description": "Encounter class: emergency, inpatient, ambulatory, wellness, urgentcare"
                        },
                        "total_claim_cost": {
                            "type": "number",
                            "description": "Total billed cost"
                        },
                        "payer_coverage": {
                            "type": "number",
                            "description": "Amount covered by insurance"
                        }
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_analysis_context",
                "description": "Get relevant ontology rules and insights for a type of healthcare analysis.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "analysis_type": {
                            "type": "string",
                            "enum": ["cost", "conditions", "demographics", "coverage", "utilization", "readmission"],
                            "description": "Type of analysis"
                        }
                    },
                    "required": ["analysis_type"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "list_tables",
                "description": "List all tables in the healthcare database.",
                "parameters": {"type": "object", "properties": {}}
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_table_schema",
                "description": "Get detailed schema for a healthcare table.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "Table: patients, encounters, conditions, medications, procedures, organizations, providers, payers"
                        }
                    },
                    "required": ["table_name"]
                }
            }
        },
    ]

    def __init__(self):
        self.client = None
        self.deployment = None
        self.semantic_layer = None
        self.ontology = None

        self._init_semantic_layer()
        self._init_ontology()
        self._init_azure_openai()

    def _init_semantic_layer(self):
        try:
            from healthcare_semantic_layer import HealthcareSemanticLayer
            self.semantic_layer = HealthcareSemanticLayer()
            print("Healthcare semantic layer initialized")
        except Exception as e:
            print(f"Warning: Could not initialize healthcare semantic layer: {e}")

    def _init_ontology(self):
        try:
            from healthcare_ontology_layer import HealthcareOntologyLayer
            self.ontology = HealthcareOntologyLayer()
            print("Healthcare ontology layer initialized")
        except Exception as e:
            print(f"Warning: Could not initialize healthcare ontology: {e}")

    def _init_azure_openai(self):
        try:
            from openai import AzureOpenAI

            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            self.deployment = (
                os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
                or os.getenv("AZURE_OPENAI_DEPLOYMENT")
                or "gpt-4"
            )
            api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

            if not endpoint or not api_key:
                print("Azure OpenAI not configured - running in offline mode")
                return

            self.client = AzureOpenAI(
                azure_endpoint=endpoint,
                api_key=api_key,
                api_version=api_version,
            )
            print(f"Azure OpenAI initialized (deployment: {self.deployment})")
        except ImportError:
            print("openai package not installed - offline mode")
        except Exception as e:
            print(f"Could not initialize Azure OpenAI: {e}")

    # ── Measure definitions ──────────────────────────────────────────────
    _MEASURE_INFO = {
        "encounter_count": {
            "name": "encounter_count",
            "description": "Total number of healthcare encounters",
            "calculation": "COUNT(*)",
            "unit": "encounters",
            "business_context": "Volume indicator. Ambulatory is most common, emergency is most expensive.",
        },
        "total_claim_cost": {
            "name": "total_claim_cost",
            "description": "Sum of all billed costs",
            "calculation": "SUM(total_claim_cost)",
            "unit": "USD",
            "business_context": "Primary cost metric. Inpatient drives highest totals.",
        },
        "avg_claim_cost": {
            "name": "avg_claim_cost",
            "description": "Average cost per encounter",
            "calculation": "AVG(total_claim_cost)",
            "unit": "USD",
            "business_context": "Emergency and inpatient have highest per-encounter cost.",
        },
        "total_payer_coverage": {
            "name": "total_payer_coverage",
            "description": "Total amount covered by insurance",
            "calculation": "SUM(payer_coverage)",
            "unit": "USD",
            "business_context": "Insurance contribution. Coverage ratio = payer_coverage / total_claim_cost.",
        },
        "avg_out_of_pocket": {
            "name": "avg_out_of_pocket",
            "description": "Average patient out-of-pocket cost",
            "calculation": "AVG(total_claim_cost - payer_coverage)",
            "unit": "USD",
            "business_context": "Patient financial burden. High values indicate coverage gaps.",
        },
        "condition_count": {
            "name": "condition_count",
            "description": "Number of condition diagnosis records",
            "calculation": "COUNT(*)",
            "unit": "conditions",
            "business_context": "Frequency of diagnoses. Chronic conditions appear repeatedly.",
        },
        "medication_count": {
            "name": "medication_count",
            "description": "Number of medication prescriptions",
            "calculation": "COUNT(*)",
            "unit": "prescriptions",
            "business_context": "Prescription volume. Chronic conditions drive repeat prescriptions.",
        },
        "total_medication_cost": {
            "name": "total_medication_cost",
            "description": "Total cost of medications",
            "calculation": "SUM(total_cost)",
            "unit": "USD",
            "business_context": "Drug spending. Specialty medications drive highest costs.",
        },
    }

    # ── Fallback table schemas ───────────────────────────────────────────
    _FALLBACK_SCHEMAS = {
        "patients": {
            "name": "patients",
            "description": "Synthetic patient demographics (Synthea)",
            "columns": [
                {"name": "id", "type": "UUID", "description": "Patient ID"},
                {"name": "birth_date", "type": "DATE", "description": "Date of birth"},
                {"name": "gender", "type": "VARCHAR", "description": "M or F"},
                {"name": "race", "type": "VARCHAR", "description": "Patient race"},
                {"name": "ethnicity", "type": "VARCHAR", "description": "Patient ethnicity"},
                {"name": "city", "type": "VARCHAR", "description": "City of residence"},
                {"name": "county", "type": "VARCHAR", "description": "County of residence"},
                {"name": "income", "type": "INTEGER", "description": "Annual income"},
                {"name": "healthcare_expenses", "type": "DECIMAL", "description": "Lifetime healthcare expenses"},
                {"name": "healthcare_coverage", "type": "DECIMAL", "description": "Lifetime coverage received"},
            ],
        },
        "encounters": {
            "name": "encounters",
            "description": "Healthcare encounters (visits) - primary fact table",
            "columns": [
                {"name": "id", "type": "UUID", "description": "Encounter ID"},
                {"name": "start_time", "type": "TIMESTAMP", "description": "Encounter start"},
                {"name": "patient_id", "type": "UUID", "description": "FK to patients"},
                {"name": "encounter_class", "type": "VARCHAR", "description": "emergency, inpatient, ambulatory, wellness, urgentcare"},
                {"name": "total_claim_cost", "type": "DECIMAL", "description": "Total billed cost"},
                {"name": "payer_coverage", "type": "DECIMAL", "description": "Amount covered by insurance"},
                {"name": "description", "type": "VARCHAR", "description": "Encounter description"},
                {"name": "reason_code", "type": "VARCHAR", "description": "Reason SNOMED code"},
            ],
        },
        "conditions": {
            "name": "conditions",
            "description": "Patient diagnoses with SNOMED CT codes",
            "columns": [
                {"name": "patient_id", "type": "UUID", "description": "FK to patients"},
                {"name": "encounter_id", "type": "UUID", "description": "FK to encounters"},
                {"name": "code", "type": "VARCHAR", "description": "SNOMED CT code"},
                {"name": "description", "type": "VARCHAR", "description": "Condition description"},
                {"name": "start_date", "type": "DATE", "description": "Diagnosis date"},
                {"name": "stop_date", "type": "DATE", "description": "Resolution date (null if active)"},
            ],
        },
        "medications": {
            "name": "medications",
            "description": "Prescribed medications with costs",
            "columns": [
                {"name": "patient_id", "type": "UUID", "description": "FK to patients"},
                {"name": "encounter_id", "type": "UUID", "description": "FK to encounters"},
                {"name": "code", "type": "VARCHAR", "description": "RxNorm code"},
                {"name": "description", "type": "VARCHAR", "description": "Medication name"},
                {"name": "base_cost", "type": "DECIMAL", "description": "Per-unit cost"},
                {"name": "total_cost", "type": "DECIMAL", "description": "Total cost"},
                {"name": "dispenses", "type": "INTEGER", "description": "Number of dispenses"},
            ],
        },
        "procedures": {
            "name": "procedures",
            "description": "Medical procedures performed",
            "columns": [
                {"name": "patient_id", "type": "UUID", "description": "FK to patients"},
                {"name": "encounter_id", "type": "UUID", "description": "FK to encounters"},
                {"name": "code", "type": "VARCHAR", "description": "Procedure code"},
                {"name": "description", "type": "VARCHAR", "description": "Procedure description"},
                {"name": "base_cost", "type": "DECIMAL", "description": "Procedure cost"},
            ],
        },
        "organizations": {
            "name": "organizations",
            "description": "Healthcare organizations (hospitals, clinics)",
            "columns": [
                {"name": "id", "type": "UUID", "description": "Organization ID"},
                {"name": "name", "type": "VARCHAR", "description": "Organization name"},
                {"name": "city", "type": "VARCHAR", "description": "City"},
                {"name": "state", "type": "VARCHAR", "description": "State"},
            ],
        },
        "providers": {
            "name": "providers",
            "description": "Healthcare providers (doctors)",
            "columns": [
                {"name": "id", "type": "UUID", "description": "Provider ID"},
                {"name": "name", "type": "VARCHAR", "description": "Provider name"},
                {"name": "speciality", "type": "VARCHAR", "description": "Medical speciality"},
                {"name": "organization_id", "type": "UUID", "description": "FK to organizations"},
            ],
        },
        "payers": {
            "name": "payers",
            "description": "Insurance payers",
            "columns": [
                {"name": "id", "type": "UUID", "description": "Payer ID"},
                {"name": "name", "type": "VARCHAR", "description": "Payer name"},
                {"name": "amount_covered", "type": "DECIMAL", "description": "Total amount covered"},
                {"name": "amount_uncovered", "type": "DECIMAL", "description": "Total amount uncovered"},
            ],
        },
    }

    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool and return results."""

        if tool_name == "query_metrics":
            if self.semantic_layer is None:
                return {"error": "Semantic layer not available"}
            dimensions = arguments.get("dimensions", [])
            measures = arguments.get("measures", [])
            limit = arguments.get("limit", 10)
            return self.semantic_layer.query(
                dimensions=dimensions,
                measures=measures,
                model_name="encounters",
                order_by=[(measures[0], "desc")] if measures else None,
                limit=limit,
            )

        elif tool_name == "query_conditions":
            if self.semantic_layer is None:
                return {"error": "Semantic layer not available"}
            return self.semantic_layer.query(
                model_name="conditions",
                dimensions=arguments.get("dimensions", []),
                measures=arguments.get("measures", []),
                order_by=[(arguments["measures"][0], "desc")] if arguments.get("measures") else None,
                limit=arguments.get("limit", 20),
            )

        elif tool_name == "query_medications":
            if self.semantic_layer is None:
                return {"error": "Semantic layer not available"}
            return self.semantic_layer.query(
                model_name="medications",
                dimensions=arguments.get("dimensions", []),
                measures=arguments.get("measures", []),
                order_by=[(arguments["measures"][0], "desc")] if arguments.get("measures") else None,
                limit=arguments.get("limit", 20),
            )

        elif tool_name == "get_context":
            if self.ontology is None:
                return {"error": "Ontology not available"}
            concept = arguments.get("concept", "")
            context = self.ontology.get_concept_context(concept)
            return context if context else {"message": f"No context found for '{concept}'"}

        elif tool_name == "get_measure_info":
            name = arguments.get("measure_name", "")
            return self._MEASURE_INFO.get(name, {
                "name": name,
                "message": "Measure exists but no additional context available",
            })

        elif tool_name == "explain_metric":
            metric = arguments.get("metric", "")
            value = arguments.get("value", 0)
            ctx = arguments.get("context", {})

            info = self._MEASURE_INFO.get(metric, {})
            parts = []
            if info.get("description"):
                unit = info.get("unit", "")
                parts.append(f"{info['description']}: {value:,.2f} {unit}")
            if info.get("business_context"):
                parts.append(f"Context: {info['business_context']}")

            # Add ontology context
            if ctx.get("encounter_class") and self.ontology:
                enc_ctx = self.ontology.get_concept_context(
                    ctx["encounter_class"].title() + "Encounter"
                )
                if enc_ctx and enc_ctx.get("business_context"):
                    parts.append(f"Encounter type: {enc_ctx['business_context']}")

            return {"explanation": " | ".join(parts) if parts else f"{metric} = {value}"}

        elif tool_name == "classify_encounter":
            if self.ontology is None:
                return {"error": "Ontology not available"}
            classifications = self.ontology.classify_encounter(
                encounter_class=arguments.get("encounter_class"),
                total_claim_cost=arguments.get("total_claim_cost"),
                payer_coverage=arguments.get("payer_coverage"),
            )
            # Enrich with encounter type info
            details = []
            for c in classifications:
                for et in self.ontology.get_encounter_types():
                    if et["name"] == c:
                        details.append({
                            "type": et["label"],
                            "context": et.get("business_context", ""),
                            "cost_range": et.get("avg_cost_range", ""),
                        })
                        break
            return {"classifications": classifications, "details": details}

        elif tool_name == "get_analysis_context":
            if self.ontology is None:
                return {"error": "Ontology not available"}
            return self.ontology.get_context_for_analysis(
                arguments.get("analysis_type", "cost")
            )

        elif tool_name == "list_tables":
            return {
                "tables": [
                    {"name": "encounters", "description": "Healthcare visits (fact table)", "rows": "~30K+"},
                    {"name": "patients", "description": "Patient demographics", "rows": "~1K"},
                    {"name": "conditions", "description": "Diagnoses (SNOMED CT)", "rows": "~5-10K"},
                    {"name": "medications", "description": "Prescriptions (RxNorm)", "rows": "~10-20K"},
                    {"name": "procedures", "description": "Medical procedures", "rows": "~5-10K"},
                    {"name": "organizations", "description": "Hospitals/clinics", "rows": "~10-50"},
                    {"name": "providers", "description": "Doctors/specialists", "rows": "~50-200"},
                    {"name": "payers", "description": "Insurance companies", "rows": "~10-30"},
                ],
            }

        elif tool_name == "get_table_schema":
            table_name = arguments.get("table_name", "")
            if table_name in self._FALLBACK_SCHEMAS:
                return {**self._FALLBACK_SCHEMAS[table_name], "source": "catalog"}
            return {"error": f"Table '{table_name}' not found"}

        return {"error": f"Unknown tool: {tool_name}"}

    def _ask_offline(self, question: str) -> AgentResponse:
        """Answer using only semantic layer + ontology (no LLM)."""
        q = question.lower()

        if any(w in q for w in ["condition", "diagnos", "disease"]):
            if self.semantic_layer:
                result = self.semantic_layer.get_top_conditions(limit=10)
                data = result.get("data", [])
                parts = ["Top Conditions by Frequency:"]
                for row in data:
                    desc = row.get("description", "?")
                    count = row.get("condition_count", 0)
                    parts.append(f"- {desc}: {count:,}")
                return AgentResponse(
                    question=question, answer="\n".join(parts),
                    data=data, tools_used=["query_conditions"],
                )

        if any(w in q for w in ["cost", "expens", "spend", "claim"]):
            if self.semantic_layer:
                result = self.semantic_layer.get_cost_by_encounter_class()
                data = result.get("data", [])
                parts = ["Cost by Encounter Class:"]
                for row in data:
                    ec = row.get("encounter_class", "?")
                    count = row.get("encounter_count", 0)
                    cost = row.get("total_claim_cost", 0)
                    parts.append(f"- {ec}: {count:,} encounters, ${cost:,.2f}")
                return AgentResponse(
                    question=question, answer="\n".join(parts),
                    data=data, tools_used=["query_metrics"],
                )

        if any(w in q for w in ["medication", "drug", "prescription"]):
            if self.semantic_layer:
                result = self.semantic_layer.get_medication_costs(limit=10)
                data = result.get("data", [])
                parts = ["Top Medications by Cost:"]
                for row in data:
                    desc = row.get("description", "?")
                    cost = row.get("total_medication_cost", 0)
                    parts.append(f"- {desc}: ${cost:,.2f}")
                return AgentResponse(
                    question=question, answer="\n".join(parts),
                    data=data, tools_used=["query_medications"],
                )

        if self.ontology:
            summary = self.ontology.summarize()
            return AgentResponse(
                question=question,
                answer=f"Running in offline mode. I can answer basic questions about costs, conditions, and medications.\n\nOntology: {summary['classes']} classes, {summary['business_rules']} business rules.",
                tools_used=[],
            )

        return AgentResponse(
            question=question,
            answer="Running in offline mode with limited capabilities.",
            tools_used=[],
        )

    def ask(self, question: str, verbose: bool = False) -> AgentResponse:
        """Ask the agent a question about healthcare data."""
        if self.client is None:
            return self._ask_offline(question)

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ]
        reasoning_steps = []
        tools_used = []
        collected_data = []

        for iteration in range(5):
            if verbose:
                print(f"\n--- Iteration {iteration + 1} ---")

            try:
                response = self.client.chat.completions.create(
                    model=self.deployment,
                    messages=messages,
                    tools=self.TOOLS,
                    tool_choice="auto",
                )
            except Exception as e:
                return AgentResponse(
                    question=question,
                    answer=f"Error calling LLM: {str(e)}",
                    error=str(e),
                    tools_used=tools_used,
                )

            assistant_message = response.choices[0].message

            if not assistant_message.tool_calls:
                return AgentResponse(
                    question=question,
                    answer=assistant_message.content or "No answer generated",
                    data=collected_data if collected_data else None,
                    reasoning_steps=reasoning_steps,
                    tools_used=tools_used,
                )

            messages.append({
                "role": "assistant",
                "content": assistant_message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in assistant_message.tool_calls
                ],
            })

            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                try:
                    arguments = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    arguments = {}

                if verbose:
                    print(f"Tool: {tool_name}, Args: {json.dumps(arguments, indent=2)}")

                result = self._execute_tool(tool_name, arguments)
                tools_used.append(tool_name)
                reasoning_steps.append(f"Called {tool_name} with {arguments}")

                if tool_name in ("query_metrics", "query_conditions", "query_medications"):
                    if isinstance(result, dict) and result.get("data"):
                        collected_data.extend(result["data"])

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, default=str),
                })

        return AgentResponse(
            question=question,
            answer="Maximum iterations reached.",
            reasoning_steps=reasoning_steps,
            tools_used=tools_used,
        )

    def summary(self) -> Dict[str, Any]:
        return {
            "llm_available": self.client is not None,
            "llm_deployment": self.deployment,
            "semantic_layer_available": self.semantic_layer is not None,
            "ontology_available": self.ontology is not None,
            "available_tools": [t["function"]["name"] for t in self.TOOLS],
        }


# =============================================================================
# CLI Demo
# =============================================================================

def main():
    print("=" * 70)
    print("HEALTHCARE AI AGENT")
    print("=" * 70)

    agent = HealthcareAgent()

    summary = agent.summary()
    print(f"\nLLM Available: {summary['llm_available']}")
    print(f"Semantic Layer: {summary['semantic_layer_available']}")
    print(f"Ontology: {summary['ontology_available']}")
    print(f"Tools: {', '.join(summary['available_tools'])}")

    demo_questions = [
        "What conditions drive the most cost?",
        "How do outcomes vary by demographics?",
        "What is the cost breakdown by encounter type?",
    ]

    for question in demo_questions:
        print(f"\n>>> {question}")
        print("-" * 50)
        response = agent.ask(question, verbose=False)
        print(response.answer)
        if response.tools_used:
            print(f"\n[Tools: {', '.join(response.tools_used)}]")

    print(f"\n" + "=" * 70)
    print("HEALTHCARE AGENT DEMO COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
