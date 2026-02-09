"""FastAPI application – multi-dataset agents (NYC Taxi + Healthcare)."""

from __future__ import annotations

import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ── Make src/ importable (same trick as scripts/chat.py) ────────────────────
_project_root = Path(__file__).resolve().parents[2]  # backend/api/main.py → project root
_src_dir = _project_root / "src"
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# Set working directory so .env and semantic_model.yml are found
os.chdir(str(_project_root))

from backend.api.routes import chat, health  # noqa: E402
from backend.api.services.agent_service import AgentService  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise all agents once at startup."""
    logger.info("Starting up – initialising agents …")
    AgentService.get().initialise()
    logger.info("Agents ready.")
    yield
    AgentService.get().shutdown()
    logger.info("Shut down complete.")


app = FastAPI(
    title="DataZense API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(health.router, prefix="/api", tags=["health"])
