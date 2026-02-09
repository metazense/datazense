"""Transform AgentResponse → structured ChatResponse for the frontend."""

from __future__ import annotations

import re
from typing import Any

from agent import AgentResponse

from backend.api.models.schemas import (
    ChartData,
    ChatResponse,
    InsightItem,
    InsightType,
    SourceLayer,
    ToolCall,
)

# ── tool → layer mapping ────────────────────────────────────────────────────

TOOL_LAYER: dict[str, SourceLayer] = {
    # NYC Taxi tools
    "query_metrics": SourceLayer.semantic,
    "get_measure_info": SourceLayer.semantic,
    "get_context": SourceLayer.ontology,
    "explain_metric": SourceLayer.ontology,
    "classify_trip": SourceLayer.ontology,
    "get_analysis_context": SourceLayer.ontology,
    "list_tables": SourceLayer.technical,
    "get_table_schema": SourceLayer.technical,
    "get_glossary_terms": SourceLayer.technical,
    "search_metadata": SourceLayer.technical,
    # Healthcare tools
    "query_conditions": SourceLayer.semantic,
    "query_medications": SourceLayer.semantic,
    "classify_encounter": SourceLayer.ontology,
}

# ── follow-up suggestions by topic ──────────────────────────────────────────

_TAXI_SUGGESTION_MAP: dict[str, list[str]] = {
    "revenue": [
        "Why does Manhattan dominate revenue?",
        "How do tips compare across boroughs?",
        "What is the airport trip premium?",
    ],
    "tip": [
        "Why are cash tips lower?",
        "What is the credit card tipping rate?",
        "How do tips vary by borough?",
    ],
    "borough": [
        "What is total revenue by borough?",
        "Which borough has the most trips?",
        "How do trip distances compare across boroughs?",
    ],
    "airport": [
        "What is the JFK flat rate?",
        "How does airport revenue compare to street hails?",
        "What percentage of trips are airport trips?",
    ],
    "payment": [
        "Why are cash tips not recorded?",
        "What is the credit card vs cash split?",
        "How does payment type affect tip amounts?",
    ],
}

_TAXI_DEFAULT_SUGGESTIONS = [
    "What is total revenue by borough?",
    "Why are Manhattan tips higher?",
    "How do airport trips compare to regular trips?",
    "What payment methods are most common?",
]

_HEALTHCARE_SUGGESTION_MAP: dict[str, list[str]] = {
    "cost": [
        "Which encounter types are most expensive?",
        "How does cost vary by demographics?",
        "What is the out-of-pocket burden by payer?",
    ],
    "condition": [
        "What conditions drive the most cost?",
        "How common are chronic conditions?",
        "What medications are most prescribed?",
    ],
    "emergency": [
        "Why are emergency visits more frequent for some groups?",
        "How does emergency cost compare to ambulatory?",
        "What conditions cause the most ED visits?",
    ],
    "demographic": [
        "How do outcomes vary by race?",
        "What is the relationship between income and utilization?",
        "How does coverage differ by demographics?",
    ],
    "medication": [
        "What medications are most expensive?",
        "How does medication cost relate to conditions?",
        "What is the average number of dispenses?",
    ],
    "coverage": [
        "Which payers cover the most?",
        "What is the average coverage ratio?",
        "How does out-of-pocket vary by encounter type?",
    ],
}

_HEALTHCARE_DEFAULT_SUGGESTIONS = [
    "What conditions drive the most cost?",
    "How do outcomes vary by demographics?",
    "Which encounter types are most expensive?",
    "What is the relationship between income and utilization?",
]


def parse_response(agent_resp: AgentResponse, dataset: str = "nyc_taxi") -> ChatResponse:
    """Convert an AgentResponse into the structured frontend format."""
    answer = agent_resp.answer or ""
    tools = _build_tool_calls(agent_resp.tools_used)
    sources = _unique_layers(tools)
    chart = _extract_chart(agent_resp.data, answer)
    table = _clean_table(agent_resp.data)
    insights = _extract_insights(answer, agent_resp.tools_used, dataset)
    suggestions = _pick_suggestions(answer, agent_resp.question, dataset)

    return ChatResponse(
        answer=answer,
        chart=chart,
        table=table,
        insights=insights,
        sources=sources,
        tools_used=tools,
        suggestions=suggestions,
        error=agent_resp.error,
    )


# ── helpers ──────────────────────────────────────────────────────────────────

def _build_tool_calls(tools: list[str]) -> list[ToolCall]:
    seen: set[str] = set()
    out: list[ToolCall] = []
    for t in tools:
        if t in seen:
            continue
        seen.add(t)
        out.append(
            ToolCall(
                tool=t,
                layer=TOOL_LAYER.get(t, SourceLayer.technical),
                summary=t.replace("_", " ").title(),
            )
        )
    return out


def _unique_layers(tools: list[ToolCall]) -> list[SourceLayer]:
    seen: set[SourceLayer] = set()
    out: list[SourceLayer] = []
    for tc in tools:
        if tc.layer not in seen:
            seen.add(tc.layer)
            out.append(tc.layer)
    return out


def _extract_chart(
    data: list[dict[str, Any]] | None,
    answer: str,
) -> ChartData | None:
    """Build a bar chart if the data has exactly one label + one numeric column."""
    if not data or len(data) < 2:
        return None

    keys = list(data[0].keys())
    if len(keys) < 2:
        return None

    # Heuristic: first string column = label, first numeric column = value
    label_col: str | None = None
    value_col: str | None = None
    for k in keys:
        sample = data[0][k]
        if label_col is None and isinstance(sample, str):
            label_col = k
        if value_col is None and isinstance(sample, (int, float)):
            value_col = k
    if not label_col or not value_col:
        return None

    labels = [str(row.get(label_col, "")) for row in data]
    values = [float(row.get(value_col, 0)) for row in data]
    title = _humanise(value_col) + " by " + _humanise(label_col)

    return ChartData(
        type="bar",
        title=title,
        labels=labels,
        values=values,
        metric_label=_humanise(value_col),
    )


def _clean_table(data: list[dict[str, Any]] | None) -> list[dict[str, Any]] | None:
    if not data:
        return None
    return data


def _humanise(col: str) -> str:
    return col.replace("_", " ").title()


# ── insight extraction ───────────────────────────────────────────────────────

_TAXI_INSIGHT_PATTERNS: list[tuple[re.Pattern[str], InsightType, SourceLayer]] = [
    (re.compile(r"(?i)\bcash tips?\b.*\bnot recorded\b"), InsightType.warning, SourceLayer.ontology),
    (re.compile(r"(?i)\bflat rate\b"), InsightType.rule, SourceLayer.ontology),
    (re.compile(r"(?i)\b(dominat|highest|most)\b"), InsightType.insight, SourceLayer.semantic),
    (re.compile(r"(?i)\bontology\b"), InsightType.context, SourceLayer.ontology),
    (re.compile(r"(?i)\bbusiness rule\b"), InsightType.rule, SourceLayer.ontology),
    (re.compile(r"(?i)\bcredit card\b.*\btip\b"), InsightType.context, SourceLayer.semantic),
    (re.compile(r"(?i)\bairport\b.*\bpremium\b"), InsightType.insight, SourceLayer.ontology),
]

_HEALTHCARE_INSIGHT_PATTERNS: list[tuple[re.Pattern[str], InsightType, SourceLayer]] = [
    (re.compile(r"(?i)\bchronic\b.*\bcost\b"), InsightType.rule, SourceLayer.ontology),
    (re.compile(r"(?i)\bout.of.pocket\b"), InsightType.warning, SourceLayer.ontology),
    (re.compile(r"(?i)\b(emergency|ED)\b.*\b(overuse|frequent|high)\b"), InsightType.warning, SourceLayer.ontology),
    (re.compile(r"(?i)\bpreventive\b"), InsightType.insight, SourceLayer.ontology),
    (re.compile(r"(?i)\bdisparit"), InsightType.context, SourceLayer.ontology),
    (re.compile(r"(?i)\b(highest|most common|drives?)\b"), InsightType.insight, SourceLayer.semantic),
    (re.compile(r"(?i)\bcoverage\b.*\bgap\b"), InsightType.warning, SourceLayer.ontology),
    (re.compile(r"(?i)\breadmission\b"), InsightType.rule, SourceLayer.ontology),
]


def _extract_insights(answer: str, tools: list[str], dataset: str = "nyc_taxi") -> list[InsightItem]:
    patterns = _HEALTHCARE_INSIGHT_PATTERNS if dataset == "healthcare" else _TAXI_INSIGHT_PATTERNS
    insights: list[InsightItem] = []
    seen_texts: set[str] = set()

    for pat, itype, src in patterns:
        m = pat.search(answer)
        if m:
            sentence = _sentence_around(answer, m.start())
            if sentence and sentence not in seen_texts:
                seen_texts.add(sentence)
                insights.append(InsightItem(type=itype, text=sentence, source=src))

    # Generic ontology insight if ontology tools used but no ontology insight found
    ontology_tools = {"get_context", "explain_metric", "classify_trip", "classify_encounter", "get_analysis_context"}
    if ontology_tools & set(tools) and not any(i.source == SourceLayer.ontology for i in insights):
        insights.append(
            InsightItem(
                type=InsightType.context,
                text="Business context from domain ontology was used to enrich this answer.",
                source=SourceLayer.ontology,
            )
        )

    return insights


def _sentence_around(text: str, pos: int) -> str:
    """Return the sentence that contains *pos*."""
    start = pos
    while start > 0 and text[start - 1] not in ".!?\n":
        start -= 1
    end = pos
    while end < len(text) and text[end] not in ".!?\n":
        end += 1
    sentence = text[start:end].strip().strip("•-–— ")
    if len(sentence) > 200:
        sentence = sentence[:197] + "…"
    return sentence


# ── suggestion picker ────────────────────────────────────────────────────────

def _pick_suggestions(answer: str, question: str, dataset: str = "nyc_taxi") -> list[str]:
    combined = (answer + " " + question).lower()

    if dataset == "healthcare":
        for keyword, suggestions in _HEALTHCARE_SUGGESTION_MAP.items():
            if keyword in combined:
                return [s for s in suggestions if s.lower() != question.lower()][:3]
        return _HEALTHCARE_DEFAULT_SUGGESTIONS[:3]
    else:
        for keyword, suggestions in _TAXI_SUGGESTION_MAP.items():
            if keyword in combined:
                return [s for s in suggestions if s.lower() != question.lower()][:3]
        return _TAXI_DEFAULT_SUGGESTIONS[:3]
