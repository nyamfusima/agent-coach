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

**Prerequisites:** Docker Desktop, Python 3.10+, and Node.js 18+.

Commands are shown for both macOS/Linux and Windows (PowerShell). All paths
are relative to the project root unless noted.

### 1. Start the database

```bash
docker compose up -d
```

This starts Postgres with the `pgvector` extension on `localhost:5432`. It
keeps running in the background until you stop it with `docker compose down`.

### 2. Backend setup (first time only)

macOS / Linux:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Windows (PowerShell):

```powershell
cd backend
python -m venv .venv; .venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Then edit `.env` and fill in:

- `ANTHROPIC_API_KEY` — for the chat assistant
- `VOYAGE_API_KEY` — for embeddings (used in ingestion + chat retrieval)

### 3. Ingest the example knowledge base (first time, and after editing docs)

From `backend/` with the venv activated:

```bash
python -m app.services.ingestion
```

This reads everything under `data/knowledge/`, chunks it, embeds it, and
stores it in Postgres. Re-run this whenever knowledge docs change.

### 4. Run the backend API

From `backend/` with the venv activated:

```bash
# macOS / Linux
uvicorn app.main:app --reload
```

```powershell
# Windows (PowerShell)
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The API runs on http://localhost:8000 (interactive docs at
http://localhost:8000/docs). Leave this terminal running.

### 5. Run the frontend

In a separate terminal:

```bash
cd frontend
npm install        # first time only
npm run dev
```

Open http://localhost:5173 — pick a call type and start a session.

## Running it again (day to day)

After the one-time setup above, the app needs **three things running** at the
same time: the database, the backend API, and the frontend.

```bash
# 1. database — skip if the container is already up
docker compose up -d

# 2. backend API — in backend/, with the venv activated
uvicorn app.main:app --reload
#    Windows: .venv\Scripts\python.exe -m uvicorn app.main:app --port 8000 --reload

# 3. frontend — in a second terminal, in frontend/
npm run dev
```

## Troubleshooting

- **"Couldn't reach the API — is the backend running on :8000? (Failed to
  fetch)"** in the UI → the backend API isn't running. Start it (step 4 / day-to-day
  step 2). The frontend on :5173 talks to the API on :8000.
- **Backend fails to start with a DB connection error** → the Postgres
  container isn't up. Check with `docker compose ps` (you should see
  `agent-coach-db-1`) and start it with `docker compose up -d`.
- **Empty call-type dropdown or no chat results** → run the ingestion step and
  confirm `data/flows/` and `data/knowledge/` are populated.

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
