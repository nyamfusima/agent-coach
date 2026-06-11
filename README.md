# Agent Coach

An internal "AI coach" for call center agents. While on a live call, the
agent sees:

1. **Step-by-step call guide** — the current step in the process flow for
   this call type, with branching based on what the agent finds (e.g.
   "identity verified?", "is this a refund or just a question?").
2. **Process Q&A chat** — a RAG-grounded chatbot the agent can ask anything
   about policy or "what do I say if the customer says X", answering from
   your actual process documentation in plain, conversational language.

This is the MVP scope: no call audio/telephony integration yet — it's a
standalone web app the agent keeps open during the call.

## Project structure

```
agent-coach/
├── backend/            FastAPI app
│   ├── app/
│   │   ├── api/        HTTP routes (flows, chat)
│   │   ├── services/   flow engine, RAG, ingestion pipeline
│   │   ├── models/      DB models + API schemas
│   │   └── core/        config, DB setup
│   └── requirements.txt
├── frontend/           React (Vite) app
│   └── src/
│       └── components/ ProcessSelector, FlowPanel, ChatPanel
├── data/
│   ├── flows/           one JSON file per call type/process (the flow graph)
│   └── knowledge/        <process_id>/*.md — source docs for the RAG chatbot
└── docker-compose.yml   local Postgres + pgvector
```

## How the flow & knowledge base fit together

- Each **process** (call type, e.g. "Billing Query") has:
  - a flow definition: `data/flows/<process_id>.json` — steps, instructions,
    and branching options
  - a knowledge folder: `data/knowledge/<process_id>/*.md` — policy docs,
    FAQs, scripts for that process
- The flow JSON drives the step-by-step checklist UI.
- The knowledge docs are chunked + embedded and used by the chat assistant,
  scoped to the process the agent selected.

A working example is included for `billing_query`.

## Getting started

### 1. Start the database

```bash
docker compose up -d
```

This starts Postgres with the `pgvector` extension on `localhost:5432`.

### 2. Backend setup

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and fill in:

- `ANTHROPIC_API_KEY` — for the chat assistant
- `VOYAGE_API_KEY` — for embeddings (used in ingestion + chat retrieval)

### 3. Ingest the example knowledge base

```bash
python -m app.services.ingestion
```

This reads everything under `data/knowledge/`, chunks it, embeds it, and
stores it in Postgres. Re-run this whenever knowledge docs change.

### 4. Run the backend

```bash
uvicorn app.main:app --reload
```

API docs available at http://localhost:8000/docs

### 5. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — pick a call type and start a session.

## Adding a new process (call type)

1. **Flow**: create `data/flows/<process_id>.json` following the structure
   of `billing_query.json` — a `start_step_id`, and a list of `steps`. Each
   step either has a single `next_step_id` (linear) or a list of `options`
   (branching), or `is_end: true`.
2. **Knowledge**: create `data/knowledge/<process_id>/` and add `.md` files
   with the policy/process info agents will need to ask about.
3. Re-run the ingestion script. The new process will automatically appear in
   the call-type dropdown.

## Roadmap (next phases)

- **Phase 2**: LLM-assisted adaptivity — the chat assistant suggests jumping
  to a different step based on what the agent describes, instead of only
  manual branching.
- **Phase 3**: live call integration (audio capture, real-time
  transcription, tone/sentiment signals) — see project notes for the
  Amazon Connect-based architecture under consideration.
- Analytics on chat questions asked vs. knowledge base coverage, to find
  documentation gaps.
- Auth / agent accounts, per-agent session history.
