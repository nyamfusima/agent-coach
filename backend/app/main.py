"""Agent Coach API — entrypoint.

Run with: uvicorn app.main:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import routes_chat, routes_flows
from app.core.db import Base, engine

app = FastAPI(title="Agent Coach API", version="0.1.0")

# Allow the local Vite dev server to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    # pgvector must be enabled before create_all() builds the VECTOR column.
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(routes_flows.router, prefix="/api")
app.include_router(routes_chat.router, prefix="/api")
