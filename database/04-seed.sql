-- ═══════════════════════════════════════════════
-- SEED DATA (v2.2-fixed) — Simplified & Bulletproof
-- ═══════════════════════════════════════════════

-- ─── Sync Metadata ───
INSERT INTO sync_metadata (id, source_name, last_sync_at, sync_status, records_processed)
VALUES 
    (gen_random_uuid(), 'restaurant_engine', NOW(), 'success', 2),
    (gen_random_uuid(), 'menu_api', NOW(), 'success', 15);

-- ─── Restaurants ───
INSERT INTO restaurants (id, external_id, name, description, phone, address, latitude, longitude, rating, is_open, is_deleted, synced_at)
VALUES 
    (gen_random_uuid(), 'REST_001', 'كشري التحرير', 
     'أشهر كشري في القاهرة منذ 1958. تقليد مصري أصيل.',
     '+201012345678', 'شارع التحرير، وسط البلد، القاهرة',
     30.0444, 31.2357, 4.7, true, false, NOW()),
    (gen_random_uuid(), 'REST_002', 'مطعم البرنس',
     'مشويات وكفتة وطواجن على الطريقة المصرية الأصيلة.',
     '+201098765432', 'شارع الهرم، الجيزة',
     29.9765, 31.1313, 4.5, true, false, NOW());

-- ─── Customers ───
INSERT INTO customers (id, phone, name, preferred_language)
VALUES 
    (gen_random_uuid(), '+201111111111', 'أحمد محمد', 'ar'),
    (gen_random_uuid(), '+201122222222', 'سارة علي', 'ar-dialect'),
    (gen_random_uuid(), '+201133333333', 'John Doe', 'en');

-- ─── Categories (Restaurant 1: كشري التحرير) ───
INSERT INTO categories (id, external_id, restaurant_id, name, description)
SELECT gen_random_uuid(), 'CAT_001', r.id, 'كشري', 'أنواع الكشري المختلفة'
FROM restaurants r WHERE r.external_id = 'REST_001'
UNION ALL
SELECT gen_random_uuid(), 'CAT_002', r.id, 'طواجن', 'طواجن لحوم وفراخ'
FROM restaurants r WHERE r.external_id = 'REST_001'
UNION ALL
SELECT gen_random_uuid(), 'CAT_003', r.id, 'مشروبات', 'مشروبات ساخنة وباردة'
FROM restaurants r WHERE r.external_id = 'REST_001'
UNION ALL
SELECT gen_random_uuid(), 'CAT_004', r.id, 'حلو', 'حلويات شرقية'
FROM restaurants r WHERE r.external_id = 'REST_001';

-- ─── Categories (Restaurant 2: البرنس) ───
INSERT INTO categories (id, external_id, restaurant_id, name, description)
SELECT gen_random_uuid(), 'CAT_005', r.id, 'مشويات', 'لحوم مشوية'
FROM restaurants r WHERE r.external_id = 'REST_002'
UNION ALL
SELECT gen_random_uuid(), 'CAT_006', r.id, 'كفتة وكباب', 'كفتة وكباب مشوي'
FROM restaurants r WHERE r.external_id = 'REST_002'
UNION ALL
SELECT gen_random_uuid(), 'CAT_007', r.id, 'مقبلات', 'سلطات ومقبلات'
FROM restaurants r WHERE r.external_id = 'REST_002';

-- ─── Menu Items (كشري التحرير) ───
INSERT INTO menu_items (id, external_id, restaurant_id, category_id, name, description, ingredients, price, currency, is_available, is_deleted, calories, synced_at)
SELECT 
    gen_random_uuid(), 'ITEM_001', r.id, c.id, 'كشري صغير',
    'كشري مصري تقليدي بالمكرونة والأرز والعدس والبصل المقلي',
    '["مكرونة", "أرز", "عدس", "حمص", "بصل مقلي", "صلصة طماطم", "ثومية"]'::jsonb,
    35.00, 'EGP', true, false, 450, NOW()
FROM restaurants r, categories c
WHERE r.external_id = 'REST_001' AND c.external_id = 'CAT_001'
UNION ALL
SELECT 
    gen_random_uuid(), 'ITEM_002', r.id, c.id, 'كشري وسط',
    'كشري مصري تقليدي بالحجم المتوسط',
    '["مكرونة", "أرز", "عدس", "حمص", "بصل مقلي", "صلصة طماطم", "ثومية"]'::jsonb,
    50.00, 'EGP', true, false, 650, NOW()
FROM restaurants r, categories c
WHERE r.external_id = 'REST_001' AND c.external_id = 'CAT_001'
UNION ALL
SELECT 
    gen_random_uuid(), 'ITEM_003', r.id, c.id, 'كشري كبير',
    'كشري مصري تقليدي بالحجم الكبير للجياع',
    '["مكرونة", "أرز", "عدس", "حمص", "بصل مقلي", "صلصة طماطم", "ثومية"]'::jsonb,
    70.00, 'EGP', true, false, 900, NOW()
FROM restaurants r, categories c
WHERE r.external_id = 'REST_001' AND c.external_id = 'CAT_001'
UNION ALL
SELECT 
    gen_random_uuid(), 'ITEM_004', r.id, c.id, 'كشري سوبريم',
    'كشري فاخر مع كرسبي فراخ إضافية',
    '["مكرونة", "أرز", "عدس", "حمص", "بصل مقلي", "صلصة طماطم", "ثومية", "كرسبي فراخ"]'::jsonb,
    95.00, 'EGP', true, false, 1200, NOW()
FROM restaurants r, categories c
WHERE r.external_id = 'REST_001' AND c.external_id = 'CAT_001'
UNION ALL
SELECT 
    gen_random_uuid(), 'ITEM_005', r.id, c.id, 'طاجن لحمة',
    'لحمة ضاني مع بطاطس في صلصة طماطم غنية',
    '["لحمة ضاني", "بطاطس", "طماطم", "بصل", "ثوم", "بهارات مشكلة"]'::jsonb,
    85.00, 'EGP', true, false, 550, NOW()
FROM restaurants r, categories c
WHERE r.external_id = 'REST_001' AND c.external_id = 'CAT_002'
UNION ALL
SELECT 
    gen_random_uuid(), 'ITEM_006', r.id, c.id, 'طاجن فراخ',
    'فراخ مشوية مع خضار في صلصة كريمة',
    '["فراخ", "فلفل ألوان", "بصل", "كريمة", "جبنة موزاريلا"]'::jsonb,
    75.00, 'EGP', true, false, 480, NOW()
FROM restaurants r, categories c
WHERE r.external_id = 'REST_001' AND c.external_id = 'CAT_002'
UNION ALL
SELECT 
    gen_random_uuid(), 'ITEM_007', r.id, c.id, 'عصير قصب',
    'عصير قصب سكر طبيعي مباشر',
    '["قصب سكر"]'::jsonb,
    15.00, 'EGP', true, false, 120, NOW()
FROM restaurants r, categories c
WHERE r.external_id = 'REST_001' AND c.external_id = 'CAT_003'
UNION ALL
SELECT 
    gen_random_uuid(), 'ITEM_008', r.id, c.id, 'شاي بالنعناع',
    'شاي أحمر مصري بالنعناع الطازج',
    '["شاي", "نعناع طازج", "سكر"]'::jsonb,
    10.00, 'EGP', true, false, 30, NOW()
FROM restaurants r, categories c
WHERE r.external_id = 'REST_001' AND c.external_id = 'CAT_003'
UNION ALL
SELECT 
    gen_random_uuid(), 'ITEM_009', r.id, c.id, 'أرز باللبن',
    'أرز باللبن مع قرفة ومكسرات',
    '["أرز", "لبن", "سكر", "قرفة", "مكسرات"]'::jsonb,
    25.00, 'EGP', true, false, 280, NOW()
FROM restaurants r, categories c
WHERE r.external_id = 'REST_001' AND c.external_id = 'CAT_004';

-- ─── Menu Items (مطعم البرنس) ───
INSERT INTO menu_items (id, external_id, restaurant_id, category_id, name, description, ingredients, price, currency, is_available, is_deleted, calories, synced_at)
SELECT 
    gen_random_uuid(), 'ITEM_010', r.id, c.id, 'ريش ضاني مشوي',
    'ريش ضاني مشوية على الفحم مع بهارات خاصة',
    '["ريش ضاني", "بهارات مشكلة", "ملح", "فلفل أسود"]'::jsonb,
    180.00, 'EGP', true, false, 800, NOW()
FROM restaurants r, categories c
WHERE r.external_id = 'REST_002' AND c.external_id = 'CAT_005'
UNION ALL
SELECT 
    gen_random_uuid(), 'ITEM_011', r.id, c.id, 'فراخ مشوية',
    'فراخ مشوية على الفحم مع بهارات خاصة',
    '["فراخ", "بهارات مشكلة", "ملح", "ليمون"]'::jsonb,
    120.00, 'EGP', true, false, 600, NOW()
FROM restaurants r, categories c
WHERE r.external_id = 'REST_002' AND c.external_id = 'CAT_005'
UNION ALL
SELECT 
    gen_random_uuid(), 'ITEM_012', r.id, c.id, 'كفتة مشوية',
    'كفتة لحمة مشوية على الفحم',
    '["لحمة مفرومة", "بصل", "بقدونس", "بهارات"]'::jsonb,
    140.00, 'EGP', true, false, 700, NOW()
FROM restaurants r, categories c
WHERE r.external_id = 'REST_002' AND c.external_id = 'CAT_006'
UNION ALL
SELECT 
    gen_random_uuid(), 'ITEM_013', r.id, c.id, 'كباب مشوي',
    'كباب لحمة مشوي على الفحم',
    '["لحمة مفرومة", "دهن", "بهارات"]'::jsonb,
    150.00, 'EGP', true, false, 750, NOW()
FROM restaurants r, categories c
WHERE r.external_id = 'REST_002' AND c.external_id = 'CAT_006'
UNION ALL
SELECT 
    gen_random_uuid(), 'ITEM_014', r.id, c.id, 'تبولة',
    'سلطة تبولة بالبقدونس والطماطم والبرغل',
    '["بقدونس", "طماطم", "برغل", "بصل", "ليمون", "زيت زيتون"]'::jsonb,
    35.00, 'EGP', true, false, 150, NOW()
FROM restaurants r, categories c
WHERE r.external_id = 'REST_002' AND c.external_id = 'CAT_007'
UNION ALL
SELECT 
    gen_random_uuid(), 'ITEM_015', r.id, c.id, 'حمص',
    'حمص بالطحينة مع زيت زيتون',
    '["حمص", "طحينة", "ليمون", "ثوم", "زيت زيتون"]'::jsonb,
    30.00, 'EGP', true, false, 200, NOW()
FROM restaurants r, categories c
WHERE r.external_id = 'REST_002' AND c.external_id = 'CAT_007';
-- ─── Customer Preferences ───
INSERT INTO customer_preferences (customer_id, favorite_categories, favorite_restaurants, disliked_ingredients, allergies, average_budget, notes)
SELECT 
    c.id, 
    '["كشري", "طواجن"]'::jsonb, 
    '[]'::jsonb, 
    '["بصل نيء"]'::jsonb, 
    '[]'::jsonb, 
    100.00, 
    'يحب الأكل الحار، يفضل التوصيل السريع'
FROM customers c WHERE c.phone = '+201111111111'
UNION ALL
SELECT 
    c.id, 
    '["مشويات"]'::jsonb, 
    '[]'::jsonb, 
    '["ثوم"]'::jsonb, 
    '["فول سوداني"]'::jsonb, 
    200.00, 
    'تفضل الأكل الصحي، لا تحب الدهون'
FROM customers c WHERE c.phone = '+201122222222';

-- ─── Sessions ───
INSERT INTO sessions (id, customer_id, status)
SELECT gen_random_uuid(), c.id, 'active'
FROM customers c WHERE c.phone = '+201111111111';

-- ─── Orders ───
INSERT INTO orders (id, customer_id, restaurant_id, status, total_price, payment_status)
SELECT gen_random_uuid(), c.id, r.id, 'delivered', 135.00, 'paid'
FROM customers c, restaurants r
WHERE c.phone = '+201111111111' AND r.external_id = 'REST_001';

-- ─── Order Items ───
INSERT INTO order_items (id, order_id, menu_item_id, quantity, unit_price)
SELECT 
    gen_random_uuid(),
    o.id,
    mi.id,
    1,
    mi.price
FROM orders o
CROSS JOIN menu_items mi
WHERE mi.external_id = 'ITEM_002'
LIMIT 1;

INSERT INTO order_items (id, order_id, menu_item_id, quantity, unit_price)
SELECT 
    gen_random_uuid(),
    o.id,
    mi.id,
    1,
    mi.price
FROM orders o
CROSS JOIN menu_items mi
WHERE mi.external_id = 'ITEM_005'
LIMIT 1;

-- ─── Conversation History ───
INSERT INTO conversation_history (id, customer_id, session_id, role, message, intent, confidence)
SELECT 
    gen_random_uuid(), 
    c.id, 
    s.id, 
    'user', 
    'عايز آكل كشري', 
    'search_menu', 
    0.952
FROM customers c, sessions s
WHERE c.phone = '+201111111111' AND s.status = 'active'
LIMIT 1;

INSERT INTO conversation_history (id, customer_id, session_id, role, message, intent, confidence)
SELECT 
    gen_random_uuid(), 
    c.id, 
    s.id, 
    'assistant', 
    'عندنا كشري صغير بـ 35 جنيه، وسط بـ 50، كبير بـ 70، وسوبريم بـ 95. إيه اللي تحبه؟', 
    'recommend_items', 
    0.921
FROM customers c, sessions s
WHERE c.phone = '+201111111111' AND s.status = 'active'
LIMIT 1;

INSERT INTO conversation_history (id, customer_id, session_id, role, message, intent, confidence)
SELECT 
    gen_random_uuid(), 
    c.id, 
    s.id, 
    'user', 
    'كشري وسط يا باشا', 
    'add_to_order', 
    0.987
FROM customers c, sessions s
WHERE c.phone = '+201111111111' AND s.status = 'active'
LIMIT 1;

INSERT INTO conversation_history (id, customer_id, session_id, role, message, intent, confidence)
SELECT 
    gen_random_uuid(), 
    c.id, 
    s.id, 
    'assistant', 
    'تمام! ضفت كشري وسط للطلب. عايز حاجة تانية؟', 
    'confirm_partial', 
    0.905
FROM customers c, sessions s
WHERE c.phone = '+201111111111' AND s.status = 'active'
LIMIT 1;

SELECT '✅ Seed data inserted successfully (v2.2-fixed)' AS status;