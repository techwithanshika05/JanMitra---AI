# JanMitra Latency Table

Audit date: 31 July 2026

This table separates runtime measurements from configured limits. A timeout is
not a measured latency. The current checkout does not persist per-stage timing
metrics, so unmeasured stages are marked explicitly.

## User-facing latency

| Flow | Start event | End event | Current value | Evidence type | Status |
|---|---|---|---:|---|---|
| Voice call startup | User selects **Start speaking** | First agent audio is heard | 4.3 s | Prior live-room observation; not re-measured in this checkout | Measured previously |
| Voice answer gap | User finishes speaking | First answer audio is heard | Not available | No STT-final, RAG-complete, or first-TTS-audio timestamps are recorded | Instrumentation required |
| Text chat response | User submits message | JSON response is received | Not available | Frontend awaits the request but records no start/end timestamps | Instrumentation required |
| Curated/non-RAG chat | User submits message | Deterministic reply is returned | Not available | No route-level timer | Instrumentation required |
| RAG chat | User submits message | Grounded answer is returned | Not available | Only a 60 s deadline exists; it is not a measurement | Instrumentation required |
| Voice session creation | Start request begins | LiveKit token/session response is received | Not available | No API middleware or route timer | Instrumentation required |
| LiveKit connection | Token received | Room connected and microphone enabled | Not available | The UI records call duration only after connection; it does not record connection latency | Instrumentation required |

## Voice pipeline budget and controls

| Stage | Component | Configured value | Meaning | Measurement state |
|---|---|---:|---|---|
| Turn endpointing | LiveKit agent session | 0.3 s minimum | Earliest fixed delay used to decide that the user finished speaking | Configuration only |
| Turn endpointing | LiveKit agent session | 1.0 s maximum | Latest fixed endpointing delay before processing the completed turn | Configuration only |
| STT | Sarvam `saaras:v3`, `codemix` | Not set | Streaming speech-to-text provider latency has no local deadline or timer | Not measured |
| Voice orchestration | Curated rules -> RAG -> scheme DB -> fallback | Not set | Rules may finish locally; welfare questions can invoke retrieval and Groq | Not measured |
| RAG acceptance | Shared RAG adapter | confidence >= 0.35 | Quality threshold, not a latency target | Not applicable |
| LLM preparation | LiveKit agent session | Disabled | `preemptive_generation.enabled` is false | Configuration only |
| TTS | Sarvam `bulbul:v3`, pace `0.9` | Not set | Answer text is sent directly to TTS after validation | Not measured |
| Voice room lifetime | Voice API | 30 min | Session TTL, not response latency | Not applicable |

## Text/RAG pipeline budget and controls

| Stage | Component | Configured value | Meaning | Measurement state |
|---|---|---:|---|---|
| Chat RAG deadline | `response_router` thread future | 60 s | Maximum wait before returning `rag_timeout` | Configuration only |
| General RAG request setting | Backend settings | 12 s | Declared RAG request budget; no use was found in the active chat response path | Configuration only |
| Retriever initialization retry | Shared RAG adapter | 120 s | Cooldown after model/retriever initialization failure; not request latency | Configuration only |
| Retrieval | Multilingual embedding + Chroma | top 4 | Result-count setting, not latency | Not measured |
| Groq generation | RAG pipeline/LLM client | Provider-dependent | Network/model generation occurs when `GROQ_API_KEY` is configured | Not measured |
| Retrieval-only response | Shared RAG adapter | Provider-dependent | Used when Groq is not configured; still includes embedding and Chroma lookup | Not measured |
| Database connect | SQLAlchemy configuration | 3 s | Connection timeout, not normal query latency | Configuration only |

## Critical path

### Voice

`Start session API -> LiveKit connect -> microphone -> Sarvam STT -> 0.3-1.0 s
endpointing -> orchestrator -> optional RAG/Groq -> persistence -> Sarvam TTS ->
browser audio`

### Text chat

`Frontend fetch -> FastAPI chat route -> intent router -> optional RAG
(embedding -> Chroma retrieval -> Groq) -> persistence -> JSON response`

## Minimum instrumentation needed for a real latency dashboard

Record one correlation ID and monotonic timestamps for:

1. frontend request start and response received;
2. voice session request start, room connected, worker joined, and first audio;
3. STT final transcript;
4. endpoint decision;
5. intent routing complete;
6. embedding complete, Chroma retrieval complete, and context complete;
7. first and final LLM token;
8. TTS request start and first audio frame;
9. database persistence complete.

Report cold-start and warm-request results separately, with at least p50, p95,
p99, sample count, error rate, and timeout rate. The existing 4.3 s voice
startup observation should remain a single sample until it is reproduced.
