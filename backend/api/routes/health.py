from __future__ import annotations

from fastapi import APIRouter, Query

from backend.api.models.schemas import (
    CapabilitiesResponse,
    Capability,
    Dataset,
    HealthStatus,
)
from backend.api.services.agent_service import AgentService

router = APIRouter()


@router.get("/health", response_model=HealthStatus)
async def health(dataset: Dataset = Query(Dataset.nyc_taxi)) -> HealthStatus:
    svc = AgentService.get()
    ds = dataset.value
    layers = svc.layers(ds)
    is_ready = svc.ready(ds)
    all_up = all(layers.values())
    return HealthStatus(
        status="ok" if is_ready and all_up else "degraded" if is_ready else "error",
        agent_ready=is_ready,
        layers=layers,
    )


# ── Per-dataset capabilities ─────────────────────────────────────────────

_TAXI_CAPABILITIES = CapabilitiesResponse(
    capabilities=[
        Capability(
            name="Revenue Analysis",
            description="Query and compare revenue across boroughs, zones, and time periods",
            example="What is total revenue by borough?",
        ),
        Capability(
            name="Tip Analysis",
            description="Understand tipping patterns and the factors that influence them",
            example="Why are Manhattan tips higher than other boroughs?",
        ),
        Capability(
            name="Trip Classification",
            description="Classify trips using ontology rules (airport, commute, long-distance)",
            example="How do airport trips compare to regular trips?",
        ),
        Capability(
            name="Business Context",
            description="Get domain knowledge and business rules from the ontology",
            example="What payment methods are most common and why?",
        ),
    ],
    starter_questions=[
        "What is total revenue by borough?",
        "Why are Manhattan tips higher than other boroughs?",
        "How do airport trips compare to regular trips?",
        "What payment methods are most common and why?",
    ],
)

_HEALTHCARE_CAPABILITIES = CapabilitiesResponse(
    capabilities=[
        Capability(
            name="Cost Analysis",
            description="Analyze healthcare costs by encounter type, demographics, and payer",
            example="Which encounter types are most expensive?",
        ),
        Capability(
            name="Condition Analysis",
            description="Understand condition frequency and their cost impact",
            example="What conditions drive the most cost?",
        ),
        Capability(
            name="Demographic Insights",
            description="Explore how outcomes and costs vary by patient demographics",
            example="How do outcomes vary by demographics?",
        ),
        Capability(
            name="Coverage Analysis",
            description="Analyze insurance coverage gaps and patient financial burden",
            example="What is the out-of-pocket burden by payer?",
        ),
    ],
    starter_questions=[
        "What conditions drive the most cost?",
        "How do outcomes vary by demographics?",
        "Why are emergency visits more frequent for certain groups?",
        "What is the relationship between income and healthcare utilization?",
    ],
)


@router.get("/capabilities", response_model=CapabilitiesResponse)
async def capabilities(dataset: Dataset = Query(Dataset.nyc_taxi)) -> CapabilitiesResponse:
    if dataset == Dataset.healthcare:
        return _HEALTHCARE_CAPABILITIES
    return _TAXI_CAPABILITIES
