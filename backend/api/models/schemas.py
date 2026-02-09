from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Dataset enum ────────────────────────────────────────────────────────────

class Dataset(str, Enum):
    nyc_taxi = "nyc_taxi"
    healthcare = "healthcare"


# ── Request models ──────────────────────────────────────────────────────────

class ChatMessageRole(str, Enum):
    user = "user"
    assistant = "assistant"


class ChatMessage(BaseModel):
    role: ChatMessageRole
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., min_length=1)
    dataset: Dataset = Dataset.nyc_taxi


# ── Response models ─────────────────────────────────────────────────────────

class SourceLayer(str, Enum):
    technical = "technical"
    semantic = "semantic"
    ontology = "ontology"


class InsightType(str, Enum):
    warning = "WARNING"
    context = "CONTEXT"
    rule = "RULE"
    insight = "INSIGHT"


class InsightItem(BaseModel):
    type: InsightType
    text: str
    source: SourceLayer


class ChartData(BaseModel):
    type: str = "bar"  # bar | table
    title: str = ""
    labels: list[str] = Field(default_factory=list)
    values: list[float] = Field(default_factory=list)
    metric_label: str = ""


class ToolCall(BaseModel):
    tool: str
    layer: SourceLayer
    summary: str = ""


class ChatResponse(BaseModel):
    answer: str
    chart: Optional[ChartData] = None
    table: Optional[list[dict[str, Any]]] = None
    insights: list[InsightItem] = Field(default_factory=list)
    sources: list[SourceLayer] = Field(default_factory=list)
    tools_used: list[ToolCall] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    error: Optional[str] = None


# ── Health / capabilities ───────────────────────────────────────────────────

class HealthStatus(BaseModel):
    status: str  # "ok" | "degraded" | "error"
    agent_ready: bool
    layers: dict[str, bool] = Field(default_factory=dict)


class Capability(BaseModel):
    name: str
    description: str
    example: str


class CapabilitiesResponse(BaseModel):
    capabilities: list[Capability]
    starter_questions: list[str]
