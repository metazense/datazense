from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from backend.api.models.schemas import ChatRequest, ChatResponse
from backend.api.services.agent_service import AgentService
from backend.api.services.response_parser import parse_response

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    service = AgentService.get()
    dataset = request.dataset.value

    if not service.ready(dataset):
        raise HTTPException(status_code=503, detail=f"Agent not ready for dataset: {dataset}")

    # Single-turn: send only the last user message
    last_user_msg = None
    for msg in reversed(request.messages):
        if msg.role == "user":
            last_user_msg = msg.content
            break

    if not last_user_msg:
        raise HTTPException(status_code=400, detail="No user message found")

    try:
        agent_resp = await service.ask(last_user_msg, dataset=dataset)
        return parse_response(agent_resp, dataset=dataset)
    except Exception:
        logger.exception("Agent error")
        raise HTTPException(status_code=500, detail="Agent processing error")
