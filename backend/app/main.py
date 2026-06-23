"""Agent Coach API — entrypoint.

Run with: uvicorn app.main:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import routes_admin, routes_chat, routes_flows
from app.core.config import get_settings
from app.core.db import Base, engine
from app.models import db_models  # noqa: F401 — register all ORM models for create_all

app = FastAPI(title="AgeCX AI API", version="0.1.0")

# CORS. localhost (any port) is always allowed for local dev; deployed frontend
# origins come from settings (default to the Vercel app, plus *.vercel.app
# previews when enabled). All configurable via env without code change.
_settings = get_settings()
_localhost_re = r"http://(localhost|127\.0\.0\.1)(:\d+)?"
_origin_regex = (
    rf"({_localhost_re}|https://[a-z0-9-]+\.vercel\.app)"
    if _settings.cors_allow_vercel
    else _localhost_re
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.allowed_origins(),
    allow_origin_regex=_origin_regex,
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
