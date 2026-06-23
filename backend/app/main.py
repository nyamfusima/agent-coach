"""Agent Coach API — entrypoint.

Run with: uvicorn app.main:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import routes_admin, routes_chat, routes_flows
from app.core.db import Base, engine
from app.models import db_models  # noqa: F401 — register all ORM models for create_all

app = FastAPI(title="AgeCX AI API", version="0.1.0")

# Allow the local Vite dev server to call the API, whether it's opened via
# localhost or 127.0.0.1 and regardless of the dev-server port.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Idempotent column additions for DBs created before these columns existed.
# (No Alembic yet; create_all only creates missing tables, not new columns.)
_COLUMN_MIGRATIONS = [
    "ALTER TABLE call_sessions ADD COLUMN IF NOT EXISTS agent_name VARCHAR",
    "ALTER TABLE call_sessions ADD COLUMN IF NOT EXISTS team_name VARCHAR",
    "ALTER TABLE call_sessions ADD COLUMN IF NOT EXISTS ended_at TIMESTAMPTZ",
]


@app.on_event("startup")
def on_startup():
    # pgvector must be enabled before create_all() builds the VECTOR column.
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        for stmt in _COLUMN_MIGRATIONS:
            conn.execute(text(stmt))


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(routes_flows.router, prefix="/api")
app.include_router(routes_chat.router, prefix="/api")
app.include_router(routes_admin.router, prefix="/api")
