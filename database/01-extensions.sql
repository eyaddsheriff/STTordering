-- ═══════════════════════════════════════════════
-- EXTENSIONS
-- ═══════════════════════════════════════════════
-- pgvector: Vector similarity search for AI embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- uuid-ossp: Generate UUIDs (if needed)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- pg_trgm: Fast text search (for menu item names/descriptions)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- unaccent: Normalize Arabic/English text search
CREATE EXTENSION IF NOT EXISTS unaccent;

-- btree_gin: For composite indexes with GIN
CREATE EXTENSION IF NOT EXISTS btree_gin;

SELECT '✅ All extensions installed successfully' AS status;
