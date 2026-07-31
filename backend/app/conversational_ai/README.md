# JanMitra Conversational AI

Additive LiveKit + Sarvam voice support for the existing JanMitra backend.
The module never owns scheme or RAG knowledge: adapters reuse the existing
`Scheme` table, checklist/grievance services, and `integration.rag_adapter`.

## Runtime flow

Browser -> LiveKit room -> Sarvam Saaras v3 STT -> LiveKit agent/Sarvam LLM
-> JanMitra tools/RAG -> evidence policy -> Bulbul v3 TTS -> browser.

Hindi is the default. English and Hinglish are supported. RAG is checked
before the existing scheme table. If neither has reliable evidence, the
agent gives an official-resource referral instead of guessing.

## Configure

Copy `.env.example` values into `.env`. Secrets stay server-side. The regular
FastAPI application can run without voice keys; `/api/voice/health` then
reports degraded mode and session creation returns 503.

Install:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Start the API:

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --port 8001
```

Start the independent LiveKit worker:

```powershell
.\venv\Scripts\python.exe -m app.conversational_ai.agent.worker start
```

## API

- `POST /api/voice/sessions` creates an owned session and server token.
- `GET /api/voice/sessions` lists current guest/user history.
- `GET /api/voice/sessions/{id}` returns the structured transcript.
- `POST /api/voice/sessions/{id}/end` closes a call.
- `GET /api/voice/health` reports database, LiveKit, Sarvam, and model config.

Guest calls use the signed `janmitra_guest` cookie. Existing login/register
claim logic transactionally moves their voice sessions to the authenticated
user while preserving the original guest ID for audit.

Raw audio is not stored. Structured sessions, turns, sources, events, and
tool calls use the active relational database (PostgreSQL primary, SQLite
fallback). ChromaDB remains retrieval-only.

The join token contains an explicit dispatch for `VOICE_AGENT_NAME`; therefore
the separately running named worker joins the room as soon as the browser
connects.
