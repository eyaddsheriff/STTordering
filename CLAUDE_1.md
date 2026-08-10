# AI Voice Ordering Agent — Claude Code Context

## TL;DR
AI-powered voice ordering assistant for a restaurant website. Customers place orders over a live voice
call; the system understands natural-language speech (Arabic — MSA, colloquial, and various dialects —
and English), searches the restaurant's menu intelligently, handles mid-call order changes, and confirms
the order against real, live data from the Restaurant Engine before it's placed.
Stack: FastAPI + LangGraph (multi-agent orchestration) + DeepSeek V3 (primary LLM, Gemini/GPT as backup)
+ PostgreSQL/pgvector (BGE-M3 embeddings) + Redis + Faster Whisper (STT) + OpenAI TTS/Piper (TTS) +
WebSocket/Socket.IO voice gateway.
**Status: Proposal/spec locked. POC in progress covering the full planned stack.**

---

## Phase Roadmap — Read This First

```
Phase 0  ✅ CONFIRMED     Spec locked. Architecture, design decisions, and tech stack finalized in proposal doc.
Phase 1  🔄 IN PROGRESS   Core AI Engine: LangGraph + DeepSeek agent, intent classification, order context mgmt.
Phase 2  🔄 IN PROGRESS   Data & Search Layer: structured DB lookup done against sample data; Restaurant Engine link, Sync Service, pgvector semantic search still pending.
Phase 3  ⬜ NOT STARTED   Voice Ordering Pipeline: WebSocket Voice Gateway, STT/TTS streaming, Chat → Voice Assistant.
Phase 4  ⬜ NOT STARTED   Order Management & Integration: Live Confirmation, Order Service ↔ Restaurant Engine API, order/customer history.
Phase 5  ⬜ NOT STARTED   Optimization & Testing: intent accuracy, search quality, response latency, load testing, MVP hardening.
```

**Do NOT build the Voice Pipeline (Phase 3) until the Core AI Engine (Phase 1) reliably handles conversation + intent.**
**Do NOT wire Live Confirmation (Phase 4) until the local Search Layer (Phase 2) is stable — search and confirmation are intentionally decoupled (see Design Decisions).**

---

## Project Overview

The AI Voice Ordering Agent receives customer orders over a voice call, understands the request in
natural language, searches the restaurant's data, suggests suitable choices, then executes the order
only after verifying real data from the **Restaurant Engine**.

Supports:
- Arabic (MSA, colloquial, and multiple dialects)
- English
- Long conversations with mid-call order edits
- Smart in-menu search with safe order confirmation
- Scalability to large customer volumes

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

### 4.2 Backend Layer
**Choice:** FastAPI — full async support, very high performance, integrates easily with LLMs,
WebSockets, and databases.

### 4.3 AI Orchestration Layer
**Choice:** LangGraph — manages the conversation workflow (state management, multi-step agents, memory,
conditional routing).

### 4.4 LLM Layer
- **Primary:** DeepSeek V3 API — the system's main "brain" (low cost, strong performance, supports tool
  calling, excellent for long dialogues).
- **Backup models:** Gemini Flash (high speed) and GPT models (for cases needing stronger reasoning and
  accuracy).

### 4.5 Speech Layer
- **STT:** Faster Whisper (audio → text)
- **TTS:** OpenAI TTS / Piper (text → audio)

### 4.6 Search Layer & Database
**Choice:** PostgreSQL + pgvector with the BGE-M3 embedding model (supports Arabic, English, and long
text).
**Why:** combines structured data (prices, categories) with semantic data (food descriptions and order
meaning).

### 4.7 Sync Service
Keeps the local search replica up to date via Webhook (on price/product changes) or Polling as a
fallback.

### 4.8 Order Management & Memory System
- **Redis:** temporary order state and session memory (current call, current order).
- **PostgreSQL:** order history and customer memory/preferences (e.g., "Ahmed likes spicy food").

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

| Component       | Technology              | Reason                                  |
|------------------|--------------------------|------------------------------------------|
| Backend          | FastAPI                  | High performance + AI-friendly           |
| Communication    | WebSocket / Socket.IO    | Real-time voice streaming                |
| LLM              | DeepSeek V3              | Cost + performance balance               |
| Orchestration    | LangGraph                | Agent workflow management                |
| Search DB        | PostgreSQL + pgvector    | Hybrid structured/vector search          |
| Embedding        | BGE-M3                   | Arabic + English semantic search         |
| Cache            | Redis                    | Fast session state                       |
| Memory           | PostgreSQL               | Customer history                         |
| Sync             | Webhook / Polling        | Data synchronization                     |
| STT              | Faster Whisper           | Speech recognition                       |
| TTS              | OpenAI TTS                | Voice generation                         |

---

## Planned Deliverables by Phase

### Phase 1 — Core AI Engine (in progress)
```
[ ] LLM Agent built with LangGraph + DeepSeek
[ ] Conversation understanding tested end-to-end
[ ] Intent classification implemented
[ ] Order context management across turns
```

### Phase 2 — Data & Search Layer
```
[ ] Restaurant Engine connection established
[ ] Sync Service built (Webhook primary, Polling fallback)
[x] PostgreSQL provisioned locally, structured menu data loaded (sample dataset, see note below)
[x] Structured DB lookup: menu_repository.py wraps get_item_by_name / check_availability /
    get_price / search_items, wired into the LangGraph agent's validate_order_items node.
    Orders are now validated against real (sample) menu data - no hallucinated items/prices.
[ ] pgvector extension + BGE-M3 embeddings loaded
[ ] Semantic search within the menu implemented and tested
```

**Note — structured lookup vs. semantic search (do not conflate):** the checked items above are a
plain-SQL structured lookup with `difflib`-based fuzzy string matching (ILIKE substring + closeness
ranking), *not* the pgvector/BGE-M3 semantic search this phase ultimately calls for. It cannot bridge
things true embeddings would (e.g. transliterated "Kishari" vs Arabic "كشري", or "something spicy"
style intent queries) — see the placeholder comment at the top of `app/repositories/menu_repository.py`
for exactly what to rip out when embeddings land.

**Known gap — schema source:** the current schema (`app/db/models.py`) was reverse-engineered from
`04-seed.sql`, an AI-generated sample dataset with no accompanying migration/schema files. It has
**no `has_variant`/variant concept** - every `menu_items` row has a plain, always-populated `price`.
If the real Restaurant Engine's menu model uses per-item variants (sizes, options) with a nullable
top-level price, this schema will need revisiting before Phase 4 integration.

### Phase 3 — Voice Ordering Pipeline
```
[ ] Voice Gateway set up over WebSocket
[ ] STT/TTS streaming integrated
[ ] System converted from Chat to Voice Assistant
```

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
