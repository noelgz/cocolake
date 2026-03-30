from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator

from common import repository
from common.db import close_pool, run_migrations
from common.source_plugins import SUPPORTED_SOURCE_TYPES, validate_source_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting API — running migrations...")
    await run_migrations()
    yield
    await close_pool()


app = FastAPI(
    title="Cocolake API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/health")
async def health():
    return {"status": "ok"}


# Digest endpoints
@app.get("/api/digests/latest")
async def get_latest_digest():
    digest = await repository.get_latest_digest()
    if not digest:
        raise HTTPException(404, "No digests available")
    return digest


@app.get("/api/digests/dates")
async def get_available_dates():
    dates = await repository.get_available_dates()
    return {"dates": dates}


@app.get("/api/digests/{date}")
async def get_digest_by_date(date: str):
    digest = await repository.get_digest_by_date(date)
    if not digest:
        raise HTTPException(404, f"No digest for {date}")
    return digest


# Source endpoints
class SourceCreate(BaseModel):
    name: str
    source_type: str = Field(
        description=f"Supported types: {', '.join(SUPPORTED_SOURCE_TYPES)}"
    )
    config: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def normalize_config(self):
        self.source_type = self.source_type.strip()
        self.config = validate_source_config(self.source_type, self.config)
        return self


class SourceToggle(BaseModel):
    enabled: bool


@app.get("/api/sources")
async def list_sources(enabled_only: bool = Query(False)):
    return await repository.load_sources(enabled_only=enabled_only)


@app.post("/api/sources", status_code=201)
async def create_source(body: SourceCreate):
    try:
        return await repository.add_source(body.name, body.source_type, body.config)
    except Exception as exc:
        raise HTTPException(400, str(exc))


@app.patch("/api/sources/{source_id}")
async def toggle_source(source_id: int, body: SourceToggle):
    source = await repository.toggle_source(source_id, body.enabled)
    if not source:
        raise HTTPException(404, f"Source {source_id} not found")
    return source
