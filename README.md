# 🎙️ Voice Ordering System — Data Layer (v2.2)

> Docker Environment + PostgreSQL + pgvector + Redis  
> v2.2: Review #2 Applied — JSONB ingredients, synced_at, confidence precision

---

## 📁 Project Structure

```
Voice_Bot_Assistant/
├── docker-compose.yml          # Docker orchestration (4 services)
├── .env.example               # Environment variables template
├── .env                       # Active environment config
├── README.md                  # This file
└── database/
    ├── 00-init.sql            # Master init script
    ├── extensions.sql         # PostgreSQL extensions
    ├── schema.sql             # 11 tables + triggers + constraints
    ├── indexes.sql            # 39 performance indexes
    ├── seed.sql               # Demo data (JSONB ingredients)
    └── migrations/            # Reserved for Alembic
```

---

## 🚀 Quick Start

```bash
cp .env.example .env
docker compose up -d
```

Verify:
```bash
docker exec voice-postgres pg_isready -U voice_user -d voice_ordering
docker exec voice-redis redis-cli -a redis_pass_2026 ping
```

pgAdmin: http://localhost:5050 (admin@voice.com / admin123)

---

## 🗄️ Database Schema (11 Tables)

| # | Table | Purpose | Key Features |
|---|-------|---------|-------------|
| 1 | `sync_metadata` | Track sync with Engine | `sync_status`, `records_processed` |
| 2 | `restaurants` | Restaurant profiles | `is_deleted`, `synced_at` |
| 3 | `customers` | Customer profiles | Phone-based login |
| 4 | `categories` | Menu categories | Per-restaurant (Engine IDs) |
| 5 | `menu_items` | Menu items (core) | **JSONB ingredients**, `synced_at`, `search_vector` |
| 6 | `menu_embeddings` | AI vectors | `VECTOR(1024)` BGE-M3 |
| 7 | `customer_preferences` | Preferences | JSONB arrays |
| 8 | `sessions` | Voice call sessions | `last_activity_at` |
| 9 | `orders` | Orders | Workflow status |
| 10 | `order_items` | Order line items | Snapshot pricing |
| 11 | `conversation_history` | AI logs | `intent`, `confidence DECIMAL(4,3)` |

---

## 🔥 What's New in v2.2 (Review #2)

### 1. ingredients → JSONB (Critical for AI)
**Before (TEXT):**
```sql
ingredients TEXT -- 'مكرونة، أرز، عدس، حمص، بصل مقلي'
-- AI struggles to filter: "مش عايز ثوم" → WHERE ingredients LIKE '%ثوم%' 
-- Problem: "بصل مقلي" contains "بصل" but "بصل نيء" is different
```

**After (JSONB):**
```sql
ingredients JSONB DEFAULT '[]' -- ["مكرونة", "أرز", "عدس", "حمص", "بصل مقلي"]
-- AI filters precisely: WHERE ingredients @> '["ثوم"]'
-- Or: WHERE ingredients ? 'بصل مقلي'
```

**Why it matters:** Customer says "مش عايز ثوم" → AI excludes items where `ingredients @> '["ثوم"]'` exactly. No false matches from partial strings.

### 2. synced_at (Debugging)
```sql
-- Per-item sync tracking
SELECT name, price, synced_at, updated_at 
FROM menu_items 
WHERE external_id = 'ITEM_002';

-- If price differs from Engine:
-- synced_at = '2026-08-06 09:00' (last Engine sync)
-- updated_at = '2026-08-06 12:00' (manual edit?)
```

### 3. confidence → DECIMAL(4,3)
**Before:** `DECIMAL(3,2)` → max `9.99`, but `1.00` = 3 digits (works)  
**After:** `DECIMAL(4,3)` → `0.952` instead of `0.95` (higher precision)

---

## 🔌 Connection Strings

```
PostgreSQL: postgresql://voice_user:voice_pass_2026@localhost:5432/voice_ordering
Redis:      redis://:redis_pass_2026@localhost:6379/0
pgAdmin:    http://localhost:5050
```

---

## 🧪 Test Queries

```sql
-- 1. pgvector check
SELECT extname FROM pg_extension WHERE extname = 'vector';

-- 2. JSONB ingredients filter (AI allergy check)
SELECT name, ingredients 
FROM menu_items 
WHERE ingredients @> '["ثوم"]' AND is_deleted = FALSE;

-- 3. Full-text search
SELECT name, price 
FROM menu_items 
WHERE search_vector @@ plainto_tsquery('simple', 'كشري') 
  AND is_deleted = FALSE;

-- 4. Sync status
SELECT source_name, sync_status, records_processed, last_sync_at 
FROM sync_metadata;

-- 5. Customer preferences + allergy check
SELECT c.name, cp.disliked_ingredients, cp.allergies
FROM customers c
JOIN customer_preferences cp ON c.id = cp.customer_id
WHERE c.phone = '+201111111111';
```

---

## ⚠️ HNSW Index Parameters

```sql
-- Current (suitable for ~10k-100k vectors):
CREATE INDEX idx_menu_embeddings_vector ON menu_embeddings 
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- For 100k+ vectors, increase:
-- WITH (m = 16, ef_construction = 128);  -- or 200
```

---

## 🧹 Reset

```bash
docker compose down -v    # Delete all data
docker compose up -d      # Recreate from scratch
```

---

## ⏭️ Next Steps

1. **SQLAlchemy Models** — Python classes for FastAPI
2. **Alembic Migrations** — Database change management
3. **Sync Service** — Webhook/Polling with Restaurant Engine
4. **Sync Queue** (Phase 2) — Redis list or `sync_queue` table for event buffering
