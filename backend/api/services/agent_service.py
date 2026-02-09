"""Multi-agent service: manages NYCTaxiAgent and HealthcareAgent."""

from __future__ import annotations

import asyncio
import logging
from functools import partial
from typing import Optional

from agent import NYCTaxiAgent, AgentResponse
from healthcare_agent import HealthcareAgent

logger = logging.getLogger(__name__)


class AgentService:
    """Thin async wrapper holding one agent per dataset."""

    _instance: Optional[AgentService] = None
    _agents: dict[str, NYCTaxiAgent | HealthcareAgent]

    @classmethod
    def get(cls) -> AgentService:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._agents = {}

    # ── lifecycle ────────────────────────────────────────────────────────

    def initialise(self) -> None:
        """Create both agents (blocking – call during lifespan startup)."""
        logger.info("Initialising NYCTaxiAgent …")
        try:
            self._agents["nyc_taxi"] = NYCTaxiAgent()
            logger.info("NYCTaxiAgent ready")
        except Exception:
            logger.exception("Failed to initialise NYCTaxiAgent")

        logger.info("Initialising HealthcareAgent …")
        try:
            self._agents["healthcare"] = HealthcareAgent()
            logger.info("HealthcareAgent ready")
        except Exception:
            logger.exception("Failed to initialise HealthcareAgent")

    def shutdown(self) -> None:
        self._agents.clear()
        logger.info("All agents shut down.")

    # ── public ───────────────────────────────────────────────────────────

    def ready(self, dataset: str = "nyc_taxi") -> bool:
        return dataset in self._agents

    def layers(self, dataset: str = "nyc_taxi") -> dict[str, bool]:
        agent = self._agents.get(dataset)
        if agent is None:
            return {"technical": False, "semantic": False, "ontology": False}

        if dataset == "nyc_taxi":
            return {
                "technical": agent.technical_layer is not None,
                "semantic": agent.semantic_layer is not None,
                "ontology": agent.ontology is not None,
            }
        else:
            # Healthcare agent has no technical layer (no OpenMetadata)
            return {
                "technical": False,
                "semantic": agent.semantic_layer is not None,
                "ontology": agent.ontology is not None,
            }

    async def ask(self, question: str, dataset: str = "nyc_taxi") -> AgentResponse:
        """Run the appropriate agent in a thread-pool."""
        agent = self._agents.get(dataset)
        if agent is None:
            raise RuntimeError(f"Agent not initialised for dataset: {dataset}")
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, partial(agent.ask, question)
        )
