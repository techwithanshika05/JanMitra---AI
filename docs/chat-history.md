# Persistent chat history, FAQ presentation, and feedback

The original `/chat` endpoint and legacy `chat_history`/`feedback` tables remain
unchanged. The additive API is mounted at `/api/chat`.

## Setup

```powershell
cd backend
python -m pip install -r requirements.txt
python migrations/001_add_conversation_history.py
uvicorn app.main:app --reload
```

For local frontend development:

```powershell
cd frontend
npm install
npm run dev
```

Use `COOKIE_SECURE=true` in production HTTPS deployments. The guest identity is
a signed, HttpOnly, SameSite=Lax cookie. Frontend requests use credentials mode,
and signed-in ownership is derived from the verified bearer token.

## API

- `POST/GET /api/chat/sessions`
- `GET/PATCH/DELETE /api/chat/sessions/{session_id}`
- `POST/GET /api/chat/sessions/{session_id}/messages`
- `POST /api/chat/migrate-guest`
- `POST/GET/DELETE /api/chat/messages/{message_id}/feedback`

Message creation requires a unique `client_message_id`. Repeating it returns the
already-created response rather than duplicating the message.

## PostgreSQL

No model uses SQLite-specific SQL. Install Psycopg and set the environment:

```powershell
python -m pip install "psycopg[binary]"
$env:DATABASE_URL="postgresql+psycopg://username:password@host:5432/database_name"
python migrations/001_add_conversation_history.py
```

Keep credentials in environment variables or a secret manager, never in source.

## Tests

```powershell
cd backend
python -m pytest -q

cd ..\frontend
npm run test
npm run build
```
