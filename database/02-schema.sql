-- ═══════════════════════════════════════════════
-- SCHEMA: voice_ordering (v2.2-final)
-- Changes: ingredients→JSONB, synced_at added, confidence→DECIMAL(4,3)
-- FIX: search_vector changed from GENERATED column to trigger-based
--      (Postgres generated columns don't support subqueries)
-- FIX v2: Added missing 'calories' column to menu_items
-- ═══════════════════════════════════════════════

DROP TABLE IF EXISTS sync_metadata CASCADE;
DROP TABLE IF EXISTS conversation_history CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS sessions CASCADE;
DROP TABLE IF EXISTS customer_preferences CASCADE;
DROP TABLE IF EXISTS menu_embeddings CASCADE;
DROP TABLE IF EXISTS menu_items CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS restaurants CASCADE;

-- ═══════════════════════════════════════════════
-- 1. SYNC METADATA
-- ═══════════════════════════════════════════════
CREATE TABLE sync_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_name VARCHAR(100) NOT NULL,
    last_sync_at TIMESTAMP WITH TIME ZONE,
    sync_status VARCHAR(20) DEFAULT 'idle' 
        CHECK (sync_status IN ('idle', 'running', 'success', 'failed')),
    records_processed INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE sync_metadata IS 'تتبع حالة الـ Sync Service مع Restaurant Engine';

-- ═══════════════════════════════════════════════
-- 2. RESTAURANTS
-- ═══════════════════════════════════════════════
CREATE TABLE restaurants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    phone VARCHAR(50),
    address TEXT,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    rating DECIMAL(2, 1) CHECK (rating >= 0 AND rating <= 5),
    is_open BOOLEAN DEFAULT true,
    is_deleted BOOLEAN DEFAULT FALSE,
    synced_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON COLUMN restaurants.synced_at IS 'آخر مرة اتعمل فيها sync من Restaurant Engine (للـ debugging)';

-- ═══════════════════════════════════════════════
-- 3. CUSTOMERS
-- ═══════════════════════════════════════════════
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255),
    preferred_language VARCHAR(10) DEFAULT 'ar' CHECK (preferred_language IN ('ar', 'en', 'ar-dialect')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ═══════════════════════════════════════════════
-- 4. CATEGORIES
-- ═══════════════════════════════════════════════
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id VARCHAR(255) NOT NULL,
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    UNIQUE(external_id, restaurant_id)
);

-- ═══════════════════════════════════════════════
-- 5. MENU ITEMS 🔥
-- ═══════════════════════════════════════════════
CREATE TABLE menu_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id VARCHAR(255) NOT NULL,
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    -- 🔥 CHANGED v2.2: ingredients TEXT → JSONB for precise allergy filtering
    ingredients JSONB DEFAULT '[]',
    price DECIMAL(10, 2) NOT NULL CHECK (price >= 0),
    currency VARCHAR(3) DEFAULT 'EGP',
    image_url TEXT,
    is_available BOOLEAN DEFAULT true,
    is_deleted BOOLEAN DEFAULT FALSE,
    -- 🔥 v2.2: calories column (was missing in previous fix!)
    calories INTEGER CHECK (calories >= 0),
    -- 🔥 NEW v2.2: synced_at to track last Engine sync per item
    synced_at TIMESTAMP WITH TIME ZONE,
    -- 🔥 FIXED v2.2: Changed from GENERATED column to regular column
    -- Postgres generated columns don't support subqueries in expression
    search_vector tsvector DEFAULT ''::tsvector,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(external_id, restaurant_id)
);

COMMENT ON COLUMN menu_items.ingredients IS 'JSONB array: ["مكرونة", "أرز", "عدس", "بصل"] — سهل الـ filtering للحساسية';
COMMENT ON COLUMN menu_items.synced_at IS 'آخر مرة اتعمل فيها sync من Restaurant Engine';

-- ═══════════════════════════════════════════════
-- 6. MENU EMBEDDINGS
-- ═══════════════════════════════════════════════
CREATE TABLE menu_embeddings (
    menu_item_id UUID PRIMARY KEY REFERENCES menu_items(id) ON DELETE CASCADE,
    embedding VECTOR(1024),
    embedding_model VARCHAR(100) DEFAULT 'BAAI/bge-m3',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ═══════════════════════════════════════════════
-- 7. CUSTOMER PREFERENCES
-- ═══════════════════════════════════════════════
CREATE TABLE customer_preferences (
    customer_id UUID PRIMARY KEY REFERENCES customers(id) ON DELETE CASCADE,
    favorite_categories JSONB DEFAULT '[]',
    favorite_restaurants JSONB DEFAULT '[]',
    disliked_ingredients JSONB DEFAULT '[]',
    allergies JSONB DEFAULT '[]',
    average_budget DECIMAL(10, 2) CHECK (average_budget >= 0),
    notes TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ═══════════════════════════════════════════════
-- 8. SESSIONS
-- ═══════════════════════════════════════════════
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'abandoned', 'error'))
);

-- ═══════════════════════════════════════════════
-- 9. ORDERS
-- ═══════════════════════════════════════════════
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE RESTRICT,
    status VARCHAR(30) DEFAULT 'pending' CHECK (status IN (
        'pending', 'confirmed', 'preparing', 'ready', 
        'out_for_delivery', 'delivered', 'cancelled', 'failed'
    )),
    total_price DECIMAL(10, 2) NOT NULL DEFAULT 0 CHECK (total_price >= 0),
    payment_status VARCHAR(20) DEFAULT 'pending' CHECK (payment_status IN ('pending', 'paid', 'failed', 'refunded')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ═══════════════════════════════════════════════
-- 10. ORDER ITEMS
-- ═══════════════════════════════════════════════
CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    menu_item_id UUID NOT NULL REFERENCES menu_items(id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10, 2) NOT NULL CHECK (unit_price >= 0),
    special_instructions TEXT
);

-- ═══════════════════════════════════════════════
-- 11. CONVERSATION HISTORY
-- ═══════════════════════════════════════════════
-- 🔥 CHANGED v2.2: confidence DECIMAL(3,2) → DECIMAL(4,3) for higher precision
CREATE TABLE conversation_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'tool')),
    message TEXT NOT NULL,
    intent VARCHAR(100),
    confidence DECIMAL(4, 3) CHECK (confidence >= 0 AND confidence <= 1),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON COLUMN conversation_history.confidence IS 'دقة أعلى: 0.952 بدل 0.95 (DECIMAL(4,3))';

-- ═══════════════════════════════════════════════
-- AUTO-UPDATE updated_at TRIGGER
-- ═══════════════════════════════════════════════
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_restaurants_updated_at
    BEFORE UPDATE ON restaurants FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_menu_items_updated_at
    BEFORE UPDATE ON menu_items FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_orders_updated_at
    BEFORE UPDATE ON orders FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_customer_preferences_updated_at
    BEFORE UPDATE ON customer_preferences FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_sync_metadata_updated_at
    BEFORE UPDATE ON sync_metadata FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ═══════════════════════════════════════════════
-- 🔥 NEW v2.2-fixed: search_vector trigger for menu_items
-- (Replaces GENERATED column — Postgres doesn't allow subqueries there)
-- ═══════════════════════════════════════════════
CREATE OR REPLACE FUNCTION update_menu_items_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('simple', coalesce(NEW.name, '')), 'A') ||
        setweight(to_tsvector('simple', coalesce(NEW.description, '')), 'B') ||
        setweight(to_tsvector('simple', coalesce(
            array_to_string(ARRAY(SELECT jsonb_array_elements_text(NEW.ingredients)), ' '), ''
        )), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_menu_items_search_vector
    BEFORE INSERT OR UPDATE ON menu_items
    FOR EACH ROW EXECUTE FUNCTION update_menu_items_search_vector();

SELECT '✅ Schema v2.2-final created successfully' AS status;