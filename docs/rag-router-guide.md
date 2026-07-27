# JanMitra RAG and Router Guide

This guide explains the purpose of the FastAPI router files, the files inside
`backend/app/rag`, and the difference between that folder and Manya's completed
RAG system.

## 1. hariom `backend/app/rag` folder

This folder belongs to the FastAPI application layer. It mainly contains chat
utilities and compatibility files. It is **not the primary RAG pipeline**.

| File | What it does |
|---|---|
| `backend/app/rag/__init__.py` | Marks `app.rag` as an importable Python package. It contains no retrieval or response-generation logic. |
| `backend/app/rag/curated_faq.py` | Returns a predefined structured answer for a few exact, common questions such as ration-card application. These answers bypass semantic retrieval. |
| `backend/app/rag/ingest.py` | Converts the original scheme and FAQ data into chunks. It forwards those chunks through the compatibility retriever to Manya's configured embedding and ChromaDB system. |
| `backend/app/rag/language.py` | Detects Devanagari text and decides whether the response should be English or Hindi. It does not search the vector database. |
| `backend/app/rag/llm_client.py` | Preserves the older answer-formatting and provider helper interface for compatibility and tests. Normal knowledge queries are routed through `integration/rag_adapter.py`. |
| `backend/app/rag/prompts.py` | Contains the older prompt helper used by the compatibility LLM client. Manya's full pipeline uses `backend/rag/prompt_builder.py` instead. |
| `backend/app/rag/retriever.py` | A compatibility proxy for old imports such as `app.rag.retriever`. It delegates retrieval and ingestion to `integration/rag_adapter.py`; it does not run a separate retriever or ChromaDB. |
| `backend/app/rag/intent_router.py` | Handles high-confidence common conversational intents directly, then uses the project's configured Groq client and recent chat context to classify every unmatched message. Keywords are fallback signals, not the primary decision. |
| `backend/app/rag/response_router.py` | Provides the shared pre-RAG response flow used by both chat APIs. It sends only PDS/welfare questions to Manya's RAG adapter. |

## 2. Your `backend/app/routers` folder

Routers receive HTTP requests, validate input, call the appropriate service,
and return data to the Next.js frontend.

| File | What it does |
|---|---|
| `backend/app/routers/__init__.py` | Marks the routers directory as a Python package. Router registration itself happens in `backend/app/main.py`. |
| `backend/app/routers/auth.py` | Implements registration and login endpoints, password verification, and access-token responses. |
| `backend/app/routers/chat.py` | Provides the original `/chat` endpoint and legacy session history. Knowledge questions are passed to `rag_adapter.answer(...)`. |
| `backend/app/routers/chat_history.py` | Provides persistent sessions, messages, guest ownership/migration, pagination, and feedback under `/api/chat`. It also sends normal knowledge questions to the RAG adapter. |
| `backend/app/routers/schemes.py` | Lists schemes and performs rule-based scheme matching from citizen details. It does not use RAG. |
| `backend/app/routers/checklist.py` | Generates document and process checklists for supported services. It uses database records and deterministic logic rather than RAG. |
| `backend/app/routers/ration.py` | Returns predefined ration-service procedures such as new cards, address updates, and member changes. |
| `backend/app/routers/grievance.py` | Routes grievance categories to departments and returns steps and escalation paths. |
| `backend/app/routers/upload.py` | Accepts authorized document uploads, chunks their text, and indexes the chunks through Manya's embedding/vector-store path. |
| `backend/app/routers/admin.py` | Provides administrative summaries and knowledge-gap information. |
| `backend/app/routers/analytics.py` | Provides usage, confidence, and query analytics from stored application events. |

## 3. Manya's RAG system

Manya's RAG is distributed across several top-level backend folders. Together
they form the complete retrieval and answer-generation pipeline.

| File or folder | What it does |
|---|---|
| `backend/rag/rag_pipeline.py` | Orchestrates query processing, retrieval, context building, prompt creation, LLM generation, sources, and the final `RAGResponse`. |
| `backend/rag/prompt_builder.py` | Creates the grounded system and user prompts from the retrieved government-document context. |
| `backend/retrieval/query_processor.py` | Normalizes the question, detects its language/type, and prepares the semantic retrieval query. |
| `backend/retrieval/retriever.py` | Embeds the query, searches ChromaDB, filters weak/duplicate results, and returns ranked chunks. |
| `backend/retrieval/context_builder.py` | Converts retrieved chunks into bounded LLM context and citation-ready source information. |
| `backend/embeddings/embedding_service.py` | Loads the multilingual embedding model and creates document or query vectors. |
| `backend/vectorstore/chroma_store.py` | Opens the persistent Chroma collection, searches it, and upserts new embedded chunks without resetting the database. |
| `backend/llm/llm_client.py` | Sends Manya's grounded prompt to Groq and returns the generated answer. |
| `backend/preprocessing/` | Extracts, cleans, normalizes, analyzes, and chunks source documents before embedding and ingestion. |
| `backend/safety/response_validator.py` | Contains response-safety and validation support for generated output. |

## 4. Integration file

| File | What it does |
|---|---|
| `backend/integration/rag_adapter.py` | Connects the FastAPI routers to Manya's RAG classes, initializes them lazily, selects the configured Chroma path/model, handles failures, and converts results into the existing frontend response fields. |

The adapter exists because Manya's `RAGResponse` and the original frontend
response format are different. It translates between them without copying or
rewriting Manya's pipeline.

## 5. Difference between your RAG folder and Manya's RAG

| Area | `backend/app/rag` | Manya's top-level RAG system |
|---|---|---|
| Main purpose | FastAPI compatibility, language handling, curated FAQs, small talk, and older imports. | Complete document retrieval and generated-answer pipeline. |
| Query processing | Only detects response language or special chat intents. | Normalizes and expands the question for semantic retrieval. |
| Embeddings | Does not own an active embedding model. | Uses `EmbeddingService` with the multilingual model. |
| Vector search | Compatibility proxy only. | Searches the configured persistent Chroma collection. |
| Context building | No full context-building stage. | Builds bounded, citation-ready context for the LLM. |
| Prompt used by normal RAG | Older compatibility prompt exists but is not the primary prompt. | Uses `backend/rag/prompt_builder.py`. |
| Final generated RAG answer | Does not own the primary generated-answer pipeline. | `backend/rag/rag_pipeline.py` creates the full `RAGResponse` when Groq is configured. |
| Why it remains | Prevents existing FastAPI features and imports from breaking. | It is the primary knowledge-answering implementation. |

## 6. Which system processes a user query?

The answer depends on the type of message:

| User message | Processing path | Who creates the response? |
|---|---|---|
| Common conversation | Router -> `app/rag/response_router.py` -> `intent_router.py` | The rule-based intent handler responds directly; no RAG is used. |
| Any message not matched by a high-confidence conversation rule | Router -> response router -> context-aware project Groq classifier | Groq decides whether there is a new PDS/welfare question, conversation, or out-of-scope request. |
| Out-of-scope request | Router -> response router -> intent router | The assistant politely explains its PDS/welfare scope without Chroma sources, a confidence meter, or a government-data disclaimer. |
| Exact supported curated FAQ | History router -> `app/rag/curated_faq.py` | The curated FAQ utility responds directly; no vector retrieval is used. |
| PDS/welfare knowledge question with `GROQ_API_KEY` configured | Router -> response router -> intent router -> `integration/rag_adapter.py` -> Manya `RAGPipeline` -> Manya retriever/Chroma -> Manya prompt/LLM | **Manya's complete RAG pipeline generates the `RAGResponse`**, and the adapter converts it for the existing frontend. |
| Normal knowledge question without `GROQ_API_KEY` | Router -> adapter -> Manya retriever/embedding/Chroma | Manya's system retrieves the evidence, while the adapter creates a controlled retrieval-only answer in the existing frontend format. |
| Embedding model, ChromaDB, or retrieval failure | Router -> adapter error handling | The adapter returns a controlled “temporarily unavailable” response instead of crashing the API. |

Therefore, a normal citizen knowledge query **is processed using Manya's
retrieval system**. When Groq is configured, Manya's complete
`backend/rag/rag_pipeline.py` also generates the final RAG answer. Without a
Groq key, Manya's retriever still finds the source chunks, but the integration
adapter formats a retrieval-only response.

## 7. Active request flow

```text
Next.js chat
    -> FastAPI /chat or /api/chat router
    -> small-talk or curated-FAQ check
    -> integration/rag_adapter.py
    -> Manya QueryProcessor
    -> Manya MultilingualRetriever
    -> Manya EmbeddingService
    -> Manya ChromaStore
    -> Manya ContextBuilder and PromptBuilder
    -> Manya Groq LLMClient (when GROQ_API_KEY is configured)
    -> adapter converts output to the existing frontend contract
    -> Next.js displays answer, confidence, sources, and disclaimer
```

The active Chroma directory is `backend/data/vector_db/chroma`, and the older
The obsolete `backend/chroma_store` database has been removed. Normal chat
retrieval and ingestion use `backend/data/vector_db/chroma` exclusively.
