# JanMitra AI — Architecture & Diagrams

## 1. System Architecture

```mermaid
flowchart LR
    subgraph Client["Frontend — Next.js + Tailwind + Framer Motion"]
        UI[Citizen Dashboard / Chat / Scheme Finder / Checklist / Grievance / Admin]
    end

    subgraph API["Backend — FastAPI"]
        AUTH[/auth/]
        CHAT[/chat/]
        SCH[/schemes/]
        CHK[/checklist/]
        RAT[/ration/]
        GRV[/grievance/]
        UPL[/upload/]
        ADM[/admin/]
        ANL[/analytics/]
    end

    subgraph RAG["RAG Pipeline"]
        EMB[Sentence-Transformers Embedding]
        VDB[(ChromaDB Vector Store)]
        LLM[Gemini / OpenAI / Retrieval-only fallback]
        PROMPT[Prompt Template - grounding + citation rules]
    end

    subgraph DB["SQLite"]
        USERS[(users)]
        SCHEMES[(schemes)]
        DOCS[(documents)]
        FAQ[(faqs)]
        CHATH[(chat_history)]
        FB[(feedback)]
        ANALYTICS[(analytics)]
    end

    UI -->|REST + JWT| API
    CHAT --> EMB --> VDB
    VDB --> PROMPT --> LLM --> CHAT
    CHAT --> CHATH
    SCH --> SCHEMES
    UPL --> DOCS
    UPL --> EMB
    ADM --> ANALYTICS
    ADM --> FB
    AUTH --> USERS
```

**Why this shape:** the RAG pipeline sits between the API and the vector store so
every citizen-facing endpoint (`/chat`, and indirectly `/schemes`) can be grounded
in the same knowledge base an admin curates through `/upload`. This is what makes
"never hallucinate, always cite sources" enforceable at the architecture level,
not just a prompt instruction.

## 2. Entity-Relationship Diagram

```mermaid
erDiagram
    USERS ||--o{ CHAT_HISTORY : has
    USERS ||--o{ FEEDBACK : gives
    USERS ||--o{ DOCUMENTS : uploads
    CHAT_HISTORY ||--o{ FEEDBACK : rated_by

    USERS {
        int id PK
        string name
        string email
        string hashed_password
        string role
        string state
        string preferred_language
    }
    SCHEMES {
        int id PK
        string name
        string category
        string state
        int min_age
        int max_age
        int max_income
        json required_documents
        json application_steps
    }
    DOCUMENTS {
        int id PK
        string title
        string source_type
        int chunk_count
        int uploaded_by FK
    }
    FAQS {
        int id PK
        string question
        string answer
        string category
    }
    CHAT_HISTORY {
        int id PK
        int user_id FK
        string session_id
        string role
        text message
        json sources
        float confidence
    }
    FEEDBACK {
        int id PK
        int user_id FK
        int chat_id FK
        int rating
        text comment
    }
    ANALYTICS {
        int id PK
        string event_type
        json payload
    }
```

## 3. Sequence Diagram — Chat / RAG Query

```mermaid
sequenceDiagram
    participant C as Citizen (Browser)
    participant F as Next.js Frontend
    participant A as FastAPI /chat
    participant R as Retriever (ChromaDB)
    participant L as LLM / Retrieval-only fallback
    participant D as SQLite

    C->>F: Types a question
    F->>A: POST /chat {session_id, message}
    A->>R: embed(query) -> semantic search
    R-->>A: top-k chunks + similarity scores
    A->>A: compute confidence score
    alt confidence >= threshold
        A->>L: build_prompt(context, question) -> generate
        L-->>A: grounded answer
    else confidence < threshold
        A->>A: compose retrieval-only summary (no generation)
    end
    A->>D: persist ChatHistory + AnalyticsEvent
    A-->>F: {answer, confidence, sources[], disclaimer}
    F-->>C: renders answer + ConfidenceMeter + source citations
```

## 4. Flow Diagram — Data Pipeline

```mermaid
flowchart TD
    RAW["raw/ — scraped scheme pages, policy PDFs, FAQ exports"] --> CLEAN[Clean & Normalize]
    CLEAN --> PREPARED["prepared/ — schemes.json, faqs.json"]
    PREPARED --> CHUNK[Chunk ~300 chars, 40 overlap]
    CHUNK --> EMBED[Embed via all-MiniLM-L6-v2]
    EMBED --> STORE[(ChromaDB persistent store)]
    CHUNK --> META["metadata/ingest_report.json — chunk counts, timestamps"]
    STORE --> RETRIEVE[Retriever.query at chat-time]
```

## 5. Why these architectural choices

| Decision | Reasoning |
|---|---|
| FastAPI over Django/Flask | Async-native, auto-generated OpenAPI docs at `/docs` for live demo, tight Pydantic integration for the strict explainability response schema. |
| SQLite over Postgres for MVP | Zero infra to run/demo; `DATABASE_URL` is swappable to Postgres via SQLAlchemy with no code changes. |
| ChromaDB over Pinecone/Weaviate | Embedded, on-disk, no external service or billing needed for an internship-scale deliverable; same `add/query` interface pattern as hosted vector DBs, so swapping later is low-effort. |
| Retrieval-only fallback in `llm_client.py` | The spec requires zero-hallucination and reliable demoability. Without an API key, the app still returns cited, confidence-scored answers instead of failing. |
| Confidence gating before generation | Prevents the LLM from being asked to answer questions with no supporting context — directly enforces "reject unsupported answers." |
| JWT auth | Stateless, standard, works cleanly across the Next.js frontend and mobile in future. |
| Next.js App Router + Tailwind | Server components where useful, fast iteration, and a design-token-driven Tailwind config keeps the "award-winning UI" requirement consistent across pages instead of ad hoc styling. |
