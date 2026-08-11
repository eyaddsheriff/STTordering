-- ═══════════════════════════════════════════════
-- INDEXES FOR PERFORMANCE (v2.2)
-- ═══════════════════════════════════════════════

-- ─── Sync Metadata ───
CREATE INDEX IF NOT EXISTS idx_sync_source ON sync_metadata(source_name);
CREATE INDEX IF NOT EXISTS idx_sync_status ON sync_metadata(sync_status);
CREATE INDEX IF NOT EXISTS idx_sync_last_at ON sync_metadata(last_sync_at DESC);

-- ─── Restaurants ───
CREATE INDEX IF NOT EXISTS idx_restaurants_external_id ON restaurants(external_id);
CREATE INDEX IF NOT EXISTS idx_restaurants_is_open ON restaurants(is_open) WHERE is_open = true;
CREATE INDEX IF NOT EXISTS idx_restaurants_not_deleted ON restaurants(is_deleted) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_restaurants_location ON restaurants USING GIST (
    point(longitude, latitude)
);
-- 🔥 NEW v2.2: synced_at index for debugging sync issues
CREATE INDEX IF NOT EXISTS idx_restaurants_synced_at ON restaurants(synced_at DESC);

-- ─── Categories ───
CREATE INDEX IF NOT EXISTS idx_categories_restaurant_id ON categories(restaurant_id);
CREATE INDEX IF NOT EXISTS idx_categories_name ON categories(name);

-- ─── Menu Items ───
CREATE INDEX IF NOT EXISTS idx_menu_items_restaurant_id ON menu_items(restaurant_id);
CREATE INDEX IF NOT EXISTS idx_menu_items_category_id ON menu_items(category_id);
CREATE INDEX IF NOT EXISTS idx_menu_items_external_id ON menu_items(external_id);
CREATE INDEX IF NOT EXISTS idx_menu_items_is_available ON menu_items(is_available) WHERE is_available = true;
CREATE INDEX IF NOT EXISTS idx_menu_items_not_deleted ON menu_items(is_deleted) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_menu_items_price ON menu_items(price);

-- Text search: for AI quick lookups (name + description)
CREATE INDEX IF NOT EXISTS idx_menu_items_name_trgm ON menu_items USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_menu_items_description_trgm ON menu_items USING GIN (description gin_trgm_ops);

-- Full-text search index (tsvector)
CREATE INDEX IF NOT EXISTS idx_menu_items_search_vector ON menu_items USING GIN (search_vector);

-- 🔥 NEW v2.2: synced_at index for debugging sync issues
CREATE INDEX IF NOT EXISTS idx_menu_items_synced_at ON menu_items(synced_at DESC);

-- ─── Menu Embeddings ───
-- HNSW index for fast vector similarity search (BGE-M3)
-- NOTE: ef_construction=64 is suitable for up to ~100k vectors.
-- For 100k+ vectors, increase to 128-200. See README for details.
CREATE INDEX IF NOT EXISTS idx_menu_embeddings_vector ON menu_embeddings 
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- ─── Customers ───
CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone);

-- ─── Customer Preferences ───
CREATE INDEX IF NOT EXISTS idx_customer_preferences_customer_id ON customer_preferences(customer_id);

-- ─── Sessions ───
CREATE INDEX IF NOT EXISTS idx_sessions_customer_id ON sessions(customer_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_sessions_started_at ON sessions(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_last_activity ON sessions(last_activity_at DESC);

-- ─── Orders ───
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_restaurant_id ON orders(restaurant_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_payment_status ON orders(payment_status);

-- ─── Order Items ───
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_menu_item_id ON order_items(menu_item_id);

-- ─── Conversation History ───
CREATE INDEX IF NOT EXISTS idx_conversation_session_id ON conversation_history(session_id);
CREATE INDEX IF NOT EXISTS idx_conversation_customer_id ON conversation_history(customer_id);
CREATE INDEX IF NOT EXISTS idx_conversation_created_at ON conversation_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversation_role ON conversation_history(role);
CREATE INDEX IF NOT EXISTS idx_conversation_intent ON conversation_history(intent);
CREATE INDEX IF NOT EXISTS idx_conversation_session_created 
    ON conversation_history(session_id, created_at DESC);

SELECT '✅ All indexes created successfully (v2.2)' AS status;
