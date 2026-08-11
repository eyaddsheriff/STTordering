# AI Voice Ordering Agent — Claude Code Context

## TL;DR
AI-powered voice ordering assistant for a restaurant website. Customers place orders over a live voice
call; the system understands natural-language speech (Arabic — MSA, colloquial, and various dialects —
and English), searches the restaurant's menu intelligently, handles mid-call order changes, and confirms
the order against real, live data from the Restaurant Engine before it's placed.
Stack: FastAPI + LangGraph (multi-agent orchestration) + DeepSeek V3 (primary LLM, Gemini/GPT as backup)
+ PostgreSQL/pgvector (BGE-M3 embeddings) + Redis + Faster Whisper (STT) + OpenAI TTS/Piper (TTS) +
WebSocket/Socket.IO voice gateway.
**Status: Proposal/spec locked. POC in progress. Phase 1 functionally working end-to-end (text + voice,
English + Egyptian Arabic) against local stand-in providers, with Redis session memory. Phase 2
semantic search working (pgvector + BGE-M3) against sample data; Restaurant Engine link and Sync
Service still open. Phases 3-5 not started.**

**The menu data is still the AI-generated sample set** (15 items, 2 fictional restaurants) from
`database/04-seed.sql`. Every price and item the agent quotes today is invented. Replacing it with a
real menu export is the top unblocked task - see "What's needed from the restaurant side" below.

---

## Phase Roadmap — Read This First

```
Phase 0  ✅ CONFIRMED     Spec locked. Architecture, design decisions, and tech stack finalized in proposal doc.
Phase 1  🔄 IN PROGRESS   Core AI Engine: LangGraph + LLM agent, intent classification, order context mgmt, Redis session memory. Functionally working (see checklist) - remaining gap is the real DeepSeek V3 API (currently Ollama local stand-in).
Phase 2  🔄 IN PROGRESS   Data & Search Layer: pgvector + BGE-M3 semantic search working against sample data; Restaurant Engine link and Sync Service still pending, and the menu data itself is still the sample seed, not a real menu.
Phase 3  ⬜ NOT STARTED   Voice Ordering Pipeline: WebSocket Voice Gateway, STT/TTS streaming, Chat → Voice Assistant. (A synchronous REST voice pipeline exists as a POC/test harness - see note below.)
Phase 4  ⬜ NOT STARTED   Order Management & Integration: Live Confirmation, Order Service ↔ Restaurant Engine API, order/customer history.
Phase 5  ⬜ NOT STARTED   Optimization & Testing: intent accuracy, search quality, response latency, load testing, MVP hardening.
```

**Do NOT build the Voice Pipeline (Phase 3) until the Core AI Engine (Phase 1) reliably handles conversation + intent.**
**Do NOT wire Live Confirmation (Phase 4) until the local Search Layer (Phase 2) is stable — search and confirmation are intentionally decoupled (see Design Decisions).**

**Note on Phase 3 vs. current POC:** `POST /api/voice-order` (audio in) + `POST /api/speak` (text in,
audio out) already exist as plain REST endpoints, and `scripts/voice_test.py` drives them from a real
mic/speakers for manual testing. This is a request/response POC, not the planned WebSocket streaming
gateway - useful for validating the agent end-to-end, but Phase 3 (real-time streaming, no round-trip
per turn) is still open work.

---

## Project Overview

The AI Voice Ordering Agent receives customer orders over a voice call, understands the request in
natural language, searches the restaurant's data, suggests suitable choices, then executes the order
only after verifying real data from the **Restaurant Engine**.

Supports:
- Arabic (MSA, colloquial, and multiple dialects — Egyptian dialect is the current focus/tested target)
- English
- Long conversations with mid-call order edits
- Smart in-menu search with safe order confirmation
- Scalability to large customer volumes

### Arabic / Egyptian dialect support (current state)
- **STT**: `STT_LANGUAGE=ar` pins faster-whisper's language (Whisper has one "ar" code covering MSA +
  all dialects — there's no separate Egyptian-specific code to select).
- **LLM prompts** (`app/agent/prompts.py`): every prompt explicitly handles Arabic/dialect input and
  instructs the model to reply in the *same* language/dialect the customer used, in natural spoken
  Egyptian Arabic ("تمام", "حاضر") rather than formal MSA.
- **TTS**: `TTS_PROVIDER=edge` (Microsoft Edge TTS via the `edge-tts` package) is now the default —
  free, and has genuine native-accent Arabic dialect voices (`ar-EG-SalmaNeural`/`ar-EG-ShakirNeural`
  for Egyptian, plus 14 other dialects: SA/JO/AE/MA/LB/...). Verified via STT round-trip that it
  pronounces Egyptian-specific words (e.g. "كشري") correctly, unlike the Piper Jordanian voice which
  mangled them. **Caveat**: works by calling Microsoft's cloud through an unofficial/reverse-engineered
  integration (piggybacks on Edge browser's read-aloud feature, not a published/licensed API) - fine
  for dev/testing, but revisit before depending on it in production (swap to OpenAI TTS or Azure's
  official Speech API, same `.env`-driven swap as every other provider here). Piper
  (`ar_JO-kareem-medium`, fully local/offline, Jordanian accent) remains available via
  `TTS_PROVIDER=piper` if an offline/no-internet requirement ever matters more than accent accuracy.

---

## Main Design Decisions

### Hybrid Data Access Strategy — "Sync for Search / Live for Confirmation"

Separates the repeated searches that happen *during* a call from the *final* order confirmation, to get
the best performance and stability out of each.

During a call, the customer runs many repeated searches ("I want something with meat," "what's the
cheapest?," "compare these two items"). Hitting the Restaurant Engine on every search causes latency and
load.

- **🔍 Search Phase** → query a **local replica**: `PostgreSQL + pgvector`. Fast, low load, more stable.
- **✅ Confirmation Phase** → call the Restaurant Engine **directly**: `Order Service → Restaurant Engine API`,
  to verify current price, product availability, and restaurant open/closed status.

---

## High-Level Architecture

```
Customer
   │
Voice Interface
   │
WebSocket / Socket.IO
   │
FastAPI
   │
LangGraph Agent
   │
DeepSeek V3
   │
   ┌─────────────────────┴─────────────────────┐
Search Service                            Order Service
   │                                            │
PostgreSQL + pgvector                    Restaurant Engine API
   ▲                                            ▲
   │                                            │
Sync Service ◄────────────────────────────────┘
   ▲
   │
Webhook / Polling
```

---

## System Components (Detail)

### 4.1 Voice Gateway Layer
Receives customer audio, sends it to STT, receives the generated audio from TTS, and manages the
real-time connection.
**Choice:** WebSocket / Socket.IO — easier to implement than WebRTC, a good fit for the MVP, performs
well with FastAPI.
**Current state:** not built. `POST /api/voice-order` + `POST /api/speak` are a REST stand-in (see Phase
3 note above).

### 4.2 Backend Layer
**Choice:** FastAPI — full async support, very high performance, integrates easily with LLMs,
WebSockets, and databases.

### 4.3 AI Orchestration Layer
**Choice:** LangGraph — manages the conversation workflow (state management, multi-step agents, memory,
conditional routing).
**Current state:** built (`app/agent/graph.py`). Graph: `classify_and_extract` (merged intent
classification + item extraction into one LLM call - see latency note below) → `validate_order_items` →
conditionally `generate_reply` or `confirm_order`. Conversation and order state persist in Redis
across turns of the same call (section 4.8). The agent itself is still stateless per-invocation — it
re-derives the order from the conversation each turn rather than mutating stored state — and there's
no memory *across* calls (that's the PostgreSQL half of 4.8, not built).

### 4.4 LLM Layer
- **Primary:** DeepSeek V3 API — the system's main "brain" (low cost, strong performance, supports tool
  calling, excellent for long dialogues).
- **Backup models:** Gemini Flash (high speed) and GPT models (for cases needing stronger reasoning and
  accuracy).
- **Current state:** running against local **Ollama** (`qwen2.5:7b`) as a free stand-in — swappable via
  `LLM_PROVIDER=ollama|deepseek` in `.env` (both are OpenAI-compatible APIs, same client code either
  way). No real DeepSeek API key plugged in yet.

### 4.5 Speech Layer
- **STT:** Faster Whisper (audio → text). Current config: `medium` model on GPU (`WHISPER_DEVICE=cuda`,
  `WHISPER_COMPUTE_TYPE=int8` — Pascal-generation GPUs like the GTX 10-series don't support
  `float16`/`int8_float16` efficiently, use plain `int8`). GPU inference needs `nvidia-cublas-cu12` +
  `nvidia-cudnn-cu12` (see `requirements-gpu.txt` — kept separate from `requirements.txt` since they're
  ~1.3GB and GPU-specific); Windows doesn't auto-discover their DLLs, so `app/services/stt.py` adds
  their directory to `PATH` at import time when `WHISPER_DEVICE=cuda`.
- **TTS:** OpenAI TTS / Piper (text → audio). Current default: **Edge TTS** (`TTS_PROVIDER=edge`, free,
  native Egyptian Arabic voice) — swappable to `piper` (local/offline, Jordanian accent) or `openai`
  (paid) via `.env`. See Arabic dialect note above.

### 4.6 Search Layer & Database
**Choice:** PostgreSQL + pgvector with the BGE-M3 embedding model (supports Arabic, English, and long
text).
**Why:** combines structured data (prices, categories) with semantic data (food descriptions and order
meaning).
**Current state:** built and tested against the sample menu — BGE-M3 embeddings in `menu_embeddings`,
HNSW-indexed, queried by cosine distance, with lexical matching retained as a cross-check. See the
two-threshold section under Phase 2 before changing any of it.

### 4.7 Sync Service
Keeps the local search replica up to date via Webhook (on price/product changes) or Polling as a
fallback.
**Current state:** not built.

### 4.8 Order Management & Memory System
- **Redis:** temporary order state and session memory (current call, current order).
- **PostgreSQL:** order history and customer memory/preferences (e.g., "Ahmed likes spicy food").
**Current state:** Redis half is built (`app/services/session_store.py` — conversation + order state
per `session_id`, 30-min TTL). The PostgreSQL half is not: `sessions`/`orders`/`order_items`/
`conversation_history`/`customer_preferences` tables exist and are seeded, but nothing in the app
reads or writes them — only `menu_items`/`categories`/`restaurants` are queried. So nothing survives
a Redis expiry or restart, and there's no cross-call customer memory yet.

---

## Live Confirmation Flow

```
Customer ──► DeepSeek ──► LangGraph ──► Order Service ──► Restaurant Engine API
                                                                    │
Customer ◄── Confirm ◄── Save History ◄── Create Order ◄── Check Price & Availability ◄┘
```

---

## Final Complete Workflow

1. **Customer speaks.**
2. **Voice Gateway** receives audio over WebSocket.
3. **STT** converts speech to text.
4. **LangGraph** manages the workflow and conversation context.
5. **DeepSeek** understands customer intent and drafts a response.
6. **Search Agent** searches the local database.
7. **Recommendation Engine** ranks and filters results.
8. **DeepSeek** generates the final response.
9. **TTS** converts the response to voice.
10. **Customer selects an item** & **Order Service** validates it live against the Restaurant Engine.
11. **Restaurant Engine** creates the order & memory is updated.

---

## Final Technology Stack

| Component       | Technology              | Reason                                  | Current stand-in |
|------------------|--------------------------|------------------------------------------|-------------------|
| Backend          | FastAPI                  | High performance + AI-friendly           | ✅ as planned |
| Communication    | WebSocket / Socket.IO    | Real-time voice streaming                | ⬜ REST POC only |
| LLM              | DeepSeek V3              | Cost + performance balance               | Ollama (`qwen2.5:7b`), local, free |
| Orchestration    | LangGraph                | Agent workflow management                | ✅ as planned |
| Search DB        | PostgreSQL + pgvector    | Hybrid structured/vector search          | ✅ as planned (sample menu data) |
| Embedding        | BGE-M3                   | Arabic + English semantic search         | ✅ as planned (served via Ollama) |
| Cache            | Redis                    | Fast session state                       | ✅ session memory; order history still PostgreSQL-only |
| Memory           | PostgreSQL               | Customer history                         | ⬜ schema exists, unused |
| Sync             | Webhook / Polling        | Data synchronization                     | ⬜ not built |
| STT              | Faster Whisper           | Speech recognition                       | ✅ as planned (medium, GPU) |
| TTS              | OpenAI TTS                | Voice generation                         | Edge TTS, free, native Egyptian voice (unofficial API - see above); Piper available as fully-offline fallback |

---

## Planned Deliverables by Phase

### Phase 1 — Core AI Engine (functionally working, see gaps)
```
[x] LLM Agent built with LangGraph + DeepSeek (Ollama stand-in - see 4.4)
[x] Conversation understanding tested end-to-end (text + real mic/speaker voice, English + Egyptian Arabic)
[x] Intent classification implemented (ORDER / MODIFY_ORDER / QUESTION / CONFIRM / CHITCHAT)
[x] Order context management across turns (Redis-backed session store, see below)
```

**Session memory (Redis).** `POST /api/voice-order` takes a `session_id` (minted server-side on the
first turn and echoed back) instead of requiring the client to resend the whole transcript every
turn. Conversation history and last-known order state live in Redis under that id with a 30-minute
TTL (`SESSION_TTL_SECONDS`), so idle calls expire instead of accumulating forever. Run Redis with:
`docker run -d --name sttordering-redis -p 6379:6379 --restart unless-stopped redis:7-alpine`.
Verified end-to-end: a second turn sending only the session id still remembers and confirms the
order from the first.

**Known issues found & fixed (worth knowing before touching `app/agent/nodes.py` again):**
- The local LLM (qwen2.5:7b via Ollama) would non-deterministically drop items from structured
  extraction output at default sampling temperature (~50-80% failure rate on identical repeated
  inputs) - fixed with `temperature=0` on the classification/extraction calls.
- It would also sometimes double-encode JSON (a string containing JSON instead of the object itself),
  occasionally malformed enough to fail parsing entirely and silently drop the whole order - fixed by
  switching extraction to `response_format={"type": "json_object"}` (OpenAI-compatible JSON mode,
  supported by both Ollama and the real DeepSeek API) plus a defensive unwrap of any remaining
  string-wrapped objects.
- Conversational reply text (not extraction) would occasionally mix stray Latin/Thai-script fragments
  into Arabic output at default temperature - fixed with a low but non-zero `temperature=0.3` on the
  reply/confirmation calls (some variation is fine there, unlike the structured-extraction calls).
- Size/variant words (e.g. "كبير" = large) were sometimes extracted into `notes` instead of `name`
  (e.g. name="كشري", notes="كبير"). Since this sample menu has no variant system - small/medium/
  large/supreme koshari are 4 separate `menu_items` rows, not one item with a size selector - matching
  on `name` alone silently resolved to the wrong SKU regardless of the size actually asked for. Fixed
  in `validate_order_items` by searching on the combined `name + notes` text first, falling back to
  `name` alone only if that finds nothing.
- Arabic replies would occasionally leak literal English words (e.g. "المENU") - traced to the model
  echoing English words from our own system prompt (`MENU_CONTEXT_TEMPLATE` says "Menu..." in English)
  instead of translating them. Fixed with an explicit "no Latin script at all when replying in Arabic"
  rule added to `REPLY_SYSTEM_PROMPT` and the confirm templates. Verified clean across 10 repeated runs.
- **Serious one**: `menu_repository`'s `difflib` fuzzy-match fallback threshold (0.4) was dangerously
  loose for Arabic - completely unrelated phrases like "آيس كريم فراولة" (strawberry ice cream, not on
  the menu) scored 0.435 against "كشري وسط" purely from incidental shared letters (Arabic's smaller
  alphabet makes character-level overlap common between unrelated words) and were silently accepted as
  a match. The customer would be told their item was added when it had actually been silently swapped
  for something else - a real correctness bug, not just an annoyance. Raised the threshold to 0.6
  (tested: rejects unrelated phrases up to ~0.44, still tolerates real typos down to ~0.80, e.g.
  "كسري وسط" -> "كشري وسط"). Added a regression test (`test_unrelated_arabic_phrase_does_not_false_match`)
  since the existing test suite didn't catch this - it tested "سوشي" which happened to score exactly
  0.400, right at the old boundary, while "آيس كريم فراولة" at 0.435 slipped through undetected.
- The spoken confirmation named items the customer never ordered - after the agent *offered* mint
  tea and the customer ignored it, confirming produced "koshari and mint tea". `order_items` stayed
  correct, so this was invisible to the API and to the tests, but on a voice call the spoken
  sentence is the entire customer experience. Fixed by making `CONFIRM_REPLY_TEMPLATE` state that
  the item list is exhaustive and that previously-offered-but-unaccepted items must not appear
  (0/6 leaks after, reproduced before the fix).
- **Takeaway for future LLM-structured-output work:** always pin `temperature=0` + use JSON mode for
  anything meant to be parsed programmatically; never trust that a "name" field alone captures
  everything needed to identify a specific SKU without also checking adjacent free-text fields; never
  trust a fuzzy-match threshold without testing it against genuinely unrelated inputs, not just
  plausible near-misses.

**Latency (measured, not guessed):** full turn was ~20s end-to-end - `classify_intent` (~4s) +
`extract_order_items` (~5s) + `validate_order_items` (~0.1s, DB is not the bottleneck) +
`generate_reply`/`confirm_order` (~7s), on top of STT (~3s) and TTS (~2-4s). Root cause: `nvidia-smi`
+ `ollama ps` showed qwen2.5:7b running **23% CPU / 77% GPU split** - it doesn't fully fit this GPU's
8GB VRAM alongside everything else, and the CPU-offloaded layers dominate latency (GPU utilization
stayed near-idle during generation). Two fixes applied:
- Merged `classify_intent` + `extract_order_items` into one node, `classify_and_extract`
  (`CLASSIFY_AND_EXTRACT_PROMPT`) - same model, same info, one round trip instead of two. Cut full-turn
  latency to ~9-12s in repeated testing (down from ~20s), no correctness regression across 8+ manual
  test phrases plus the full test suite.
- Enabled `vad_filter=True` on faster-whisper's `transcribe()` call - trims silence/room-noise padding
  that real mic input always has (synthetic test clips don't), improving both STT speed and accuracy.
- **Not fixed / still slow when it happens:** occasionally saw a single outlier run take ~38s with
  garbled Chinese-script output and a leaked system prompt in the reply - looked like model
  degradation under momentary memory pressure, not reproducible on retry (3/3 clean afterward). If this
  becomes frequent, the real fix is a model that fully fits in VRAM (100% GPU offload) rather than more
  prompt engineering - e.g. a smaller model for the cheap classify+extract step, reserving qwen2.5:7b
  (or the real DeepSeek V3 API once available - no local VRAM constraint at all) for reply generation
  where quality/dialect fluency matters most.

### Phase 2 — Data & Search Layer
```
[ ] Restaurant Engine connection established
[ ] Sync Service built (Webhook primary, Polling fallback)
[x] PostgreSQL provisioned locally, structured menu data loaded (sample dataset, see note below)
[x] Structured DB lookup: menu_repository.py wraps get_item_by_name / check_availability /
    get_price / search_items, wired into the LangGraph agent's validate_order_items node.
    Orders are now validated against real (sample) menu data - no hallucinated items/prices.
[x] Tests added (tests/) covering menu_repository.py: exact match, fuzzy match, not-found, unavailable.
[x] pgvector extension installed (locally, Windows binary - see note below) and real schema applied
[x] BGE-M3 embeddings generated/loaded into menu_embeddings (scripts/generate_embeddings.py)
[x] Semantic search within the menu implemented and tested (tests/test_semantic_search.py)
[ ] Real menu data (still the AI-generated sample seed - see top of file)
```

### Semantic search: why there are two thresholds, not one

The single most important thing to understand before touching `menu_repository.py`.

**A single distance cutoff cannot work.** Measured against the seeded menu (cosine distance,
0 = identical):

| query | nearest item | distance | on the menu? |
|---|---|---|---|
| `كشري كبير` | كشري كبير | 0.366 | yes |
| `كسري وسط` (typo) | كشري وسط | 0.375 | yes |
| **`سمك مشوي`** (grilled fish) | كباب مشوي | **0.489** | **NO** |
| `koshary large` | كشري كبير | 0.483 | yes |
| `koshari` | كشري سوبريم | 0.616 | yes |

An off-menu item (0.489) sits *closer* than a real match (0.616), so any single threshold either
rejects genuine orders or accepts off-menu ones. This isn't a tuning failure - embeddings measure
**relatedness**, and grilled fish genuinely is related to grilled kebab. Ordering needs **identity**,
which is a different question.

So identity and suggestion are split:
- `get_item_by_name` = **identity** (the order-validation gate). Strict: `_SEMANTIC_IDENTITY_DISTANCE`
  = 0.40. A false positive here charges the customer for a dish they never asked for.
- `search_items` = **suggestions** (what the agent offers/mentions). Wide: `_SEMANTIC_SUGGEST_DISTANCE`
  = 0.65. Nothing here is ever silently added to an order, so a loose match is harmless - it just
  lets the agent say "we don't have X, but we have Y" instead of a bare "no".

**Lexical and semantic must agree.** Writing the semantic tests exposed a *pre-existing* bug in the
difflib path: `سمك مشوي` (not on the menu) scores **0.7059** against `كباب مشوي` - well past the 0.6
bar - purely because both end in `مشوي`, so a customer asking for grilled fish would have been sold
grilled kebab at 150 EGP. Raising the difflib threshold was not viable: it would have to fit between
0.7059 and a real typo at 0.8750. Instead `get_item_by_name` now requires both signals to agree
before accepting a character-overlap match, since they fail in different ways - embeddings correctly
place that query at 0.489, outside the identity band, and veto it. The old test suite missed this
because it never tested a query sharing a word with a real item.

**This is the second bug of exactly this shape** (after the 0.4-threshold ice-cream false positive).
The pattern to remember: *any* matching threshold must be tested against inputs that are related to
menu items but are not them - not just plausible typos and obviously-unrelated words.

**Fallback.** With `menu_embeddings` empty, `_semantic_search` returns None and everything degrades
to the pre-pgvector difflib behaviour (including the `سمك مشوي` false positive - it needs embeddings
to catch). A fresh checkout works without running `generate_embeddings.py`, just less safely.

**Schema source (resolved):** a coworker pushed `origin/feature/database-backend`, which includes the
real, authoritative `database/01-extensions.sql` through `04-seed.sql` (properly designed: CHECK
constraints, triggers, GIN/HNSW indexes, full-text search via `tsvector`) - this replaced our earlier
reverse-engineered schema in `app/db/models.py`. It **confirms** `menu_items` genuinely has no
`has_variant`/variant concept (`price` is a plain `NOT NULL DECIMAL`), so the earlier flagged gap
wasn't a gap after all - our guess matched.

That branch also includes:
- A **`menu_embeddings` table** (`VECTOR(1024)`, HNSW-indexed, `BAAI/bge-m3` default) - now applied to
  our local DB. **Still schema-only**: no embedding generation/population code exists anywhere (its own
  model docstring in the coworker's branch says `"🔒 Placeholder for Phase 5 — no generation logic
  yet."`). `search_text` there uses Postgres full-text search (`tsvector`/`ts_rank_cd`), not vector
  similarity - so there's no working semantic search to plug in yet, just the DB shell ready for it.
- A **complete separate `backend/` FastAPI service** (own models/repositories/schemas/services,
  Alembic migrations, docker-compose) - a much bigger, more structured implementation of similar
  concerns to our `app/`. **Deliberately not integrated** - decided to take only the `database/` schema
  files for now and keep our existing agent architecture as-is, rather than re-architecting to call
  into that service (which would be the more "correct" match to the original proposal's separate
  Search/Order Service split, but is a real re-architecture, not a drop-in). Revisit this decision once
  ready to build the real Restaurant Engine / Order Service integration (Phase 4).

**Embeddings run through Ollama, not sentence-transformers.** `ollama pull bge-m3` (1024-dim, same
model the schema names). The first implementation loaded `sentence-transformers` in-process, which
held ~2.2GB resident and starved Ollama of the memory it needed for its own runner - the LLM died
mid-request with `GGML_ASSERT(ctx->mem_buffer != NULL) failed`, an out-of-memory failure, on a 16GB
machine also running Whisper, Docker and VS Code. Moving the model into Ollama (which already owns
model lifecycle - loads on demand, shares the GPU, unloads when idle) removed the contention instead
of shifting it, dropped `torch` from the API process entirely, and as a side effect raised
qwen2.5:7b's GPU offload from 77% to **93%**. Verified the quantized Ollama vectors match the
sentence-transformers ones to within 0.001 cosine distance, so the tuned thresholds carry over.
Measured agent turn afterwards: ~5.6-6.5s steady state (excludes STT/TTS; first call pays a one-off
model load, which `app/main.py` warms at startup).

**pgvector install note:** not available via `CREATE EXTENSION` by default on a stock Windows Postgres
16 install - required manually placing a precompiled binary (`andreiramani/pgvector_pgsql_windows`,
v0.8.6, matches our PG 16.3) into the Postgres program directory, which needs admin rights (a normal
Claude Code session can't do this - had to hand the user exact commands to run in an elevated
PowerShell). If setting this up on a fresh machine again, expect the same manual step.

### Phase 3 — Voice Ordering Pipeline
```
[ ] Voice Gateway set up over WebSocket
[ ] STT/TTS streaming integrated
[ ] System converted from Chat to Voice Assistant
```
(A synchronous REST POC of the full voice loop already exists — see the Phase 3 note near the top.)

### Phase 4 — Order Management & Integration
```
[ ] Live Confirmation flow implemented
[ ] Order Service linked to Restaurant Engine API
[ ] Order history + customer data persisted
[ ] Full end-to-end system test
```

### Phase 5 — Optimization & Testing
```
[ ] Intent/order-understanding accuracy evaluated
[ ] Search quality evaluated
[ ] Response latency measured and tuned
[ ] Load/stress testing
[ ] MVP-ready build prepared
```

---

## What's needed from the restaurant side (blocks real progress)

Everything below is blocked on access/decisions, not on engineering effort.

**1. Restaurant Engine API access** — blocks the Sync Service (Phase 2) and *all* of Phase 4. Ask
the dev team for: base URL (staging **and** production), a working bearer token for staging, API
docs/OpenAPI spec, the four endpoints that matter (fetch menu, check price+availability, create
order, order status) with sample payloads, whether **webhooks** on menu/price change are supported
(decides webhook vs. polling, and the polling interval + rate limits if not), whether order creation
accepts an **idempotency key** (prevents duplicate orders when a call drops mid-confirm), and a test
restaurant account on staging so testing never creates real orders.

**2. A real menu export** (CSV/JSON/Excel from the admin panel) — unblocks meaningful testing today,
without waiting on the API. Needs stable item IDs (to place real orders later), an availability
flag, and descriptions/ingredients — the embeddings index that text, so intent queries like
"something spicy" only work if it exists. A manual export is a snapshot; it won't track price
changes, which is what the Sync Service eventually solves.

**3. A DeepSeek API key** — fixes latency and dialect quality at once, and is already wired
(`LLM_PROVIDER=deepseek`). qwen2.5:7b only fits this 8GB GPU at ~93% offload; DeepSeek removes the
VRAM constraint entirely.

**4. Two decisions.** (a) *Production TTS*: Edge TTS is free but an unofficial API - Azure Speech is
the same voices officially licensed, OpenAI TTS and ElevenLabs are alternatives, Piper is the
offline fallback. Genuinely colloquial Egyptian needs voice cloning, which requires a recorded
sample **plus rights to use that person's voice**. (b) *Where this deploys*: Whisper wants a GPU;
that also decides whether local STT is viable at all.

**5. Business rules the agent will hit on day one** (not in the proposal): delivery vs. pickup, fees
and zones, minimum order value, payment method, what to say when the restaurant is closed, whether
there's a human to hand off to, and whether a phone number is required to place an order.

**6. For Phase 5 evaluation**: 20-30 real customer phrasings, ideally call transcripts. Current test
phrases are invented, which risks tuning for imagined customers rather than actual ones.

---

## Future Enhancements (Do NOT Build Now)

| Enhancement                        | Notes                                                                                   |
|-------------------------------------|-------------------------------------------------------------------------------------------|
| Phone call integration              | Accept orders from a real phone number via Twilio / SIP / Telecom Gateway.               |
| Personalized recommendations        | Suggest dishes based on order history and preferences.                                    |
| Advanced customer memory            | Extend memory to cover preferences, ingredient allergies, and purchasing habits.          |
| Dialect normalization               | Layer to normalize various Arabic dialects into a form the LLM understands more reliably. |
| Human handoff                       | Transfer the call to a human agent on low system confidence or complex requests.          |
| Live dashboard & sentiment analysis | Dashboard for monitoring calls, system performance, quality metrics, and sentiment.       |
| Multi-agent architecture            | Split into specialized agents (Conversation, Search, Order, Recommendation).              |
| Payment integration                 | Add electronic payment during or after the conversation.                                  |

---

## Source
Converted from `AI_Voice_Ordering_System_Proposal_noted_v3.pdf` (original Arabic technical proposal).
