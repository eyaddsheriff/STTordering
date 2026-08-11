"""Initial schema v2.2

Revision ID: 001_initial_v22
Revises: 
Create Date: 2026-08-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_v22'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gin")

    # sync_metadata
    op.create_table('sync_metadata',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('source_name', sa.String(length=100), nullable=False),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sync_status', sa.String(length=20), server_default='idle', nullable=True),
        sa.Column('records_processed', sa.Integer(), server_default='0', nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # restaurants
    op.create_table('restaurants',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('external_id', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('latitude', sa.DECIMAL(10, 8), nullable=True),
        sa.Column('longitude', sa.DECIMAL(11, 8), nullable=True),
        sa.Column('rating', sa.DECIMAL(2, 1), nullable=True),
        sa.Column('is_open', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('external_id')
    )

    # customers
    op.create_table('customers',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('phone', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('preferred_language', sa.String(length=10), server_default='ar', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('phone')
    )

    # categories
    op.create_table('categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('external_id', sa.String(length=255), nullable=False),
        sa.Column('restaurant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('external_id', 'restaurant_id')
    )

    # menu_items
    op.create_table('menu_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('external_id', sa.String(length=255), nullable=False),
        sa.Column('restaurant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('ingredients', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=True),
        sa.Column('price', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('currency', sa.String(length=3), server_default='EGP', nullable=True),
        sa.Column('image_url', sa.Text(), nullable=True),
        sa.Column('is_available', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('calories', sa.Integer(), nullable=True),
        sa.Column('synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('search_vector', postgresql.TSVECTOR(), server_default="''::tsvector", nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('external_id', 'restaurant_id')
    )

    # menu_embeddings
    op.create_table('menu_embeddings',
        sa.Column('menu_item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('embedding', sa.NullType(), nullable=True),
        sa.Column('embedding_model', sa.String(length=100), server_default='BAAI/bge-m3', nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['menu_item_id'], ['menu_items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('menu_item_id')
    )

    # customer_preferences
    op.create_table('customer_preferences',
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('favorite_categories', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=True),
        sa.Column('favorite_restaurants', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=True),
        sa.Column('disliked_ingredients', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=True),
        sa.Column('allergies', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=True),
        sa.Column('average_budget', sa.DECIMAL(10, 2), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('customer_id')
    )

    # sessions
    op.create_table('sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='active', nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # orders
    op.create_table('orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('restaurant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(length=30), server_default='pending', nullable=True),
        sa.Column('total_price', sa.DECIMAL(10, 2), server_default='0', nullable=False),
        sa.Column('payment_status', sa.String(length=20), server_default='pending', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )

    # order_items
    op.create_table('order_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('menu_item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('special_instructions', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['menu_item_id'], ['menu_items.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # conversation_history
    op.create_table('conversation_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('intent', sa.String(length=100), nullable=True),
        sa.Column('confidence', sa.DECIMAL(4, 3), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Indexes
    op.create_index('idx_sync_source', 'sync_metadata', ['source_name'], unique=False)
    op.create_index('idx_sync_status', 'sync_metadata', ['sync_status'], unique=False)
    op.create_index('idx_sync_last_at', 'sync_metadata', ['last_sync_at'], unique=False)
    op.create_index('idx_restaurants_external_id', 'restaurants', ['external_id'], unique=False)
    op.create_index('idx_restaurants_is_open', 'restaurants', ['is_open'], unique=False, postgresql_where=sa.text('is_open = true'))
    op.create_index('idx_restaurants_not_deleted', 'restaurants', ['is_deleted'], unique=False, postgresql_where=sa.text('is_deleted = false'))
    op.create_index('idx_restaurants_location', 'restaurants', [sa.text('point(longitude, latitude)')], unique=False, postgresql_using='gist')
    op.create_index('idx_restaurants_synced_at', 'restaurants', ['synced_at'], unique=False)
    op.create_index('idx_categories_restaurant_id', 'categories', ['restaurant_id'], unique=False)
    op.create_index('idx_categories_name', 'categories', ['name'], unique=False)
    op.create_index('idx_menu_items_restaurant_id', 'menu_items', ['restaurant_id'], unique=False)
    op.create_index('idx_menu_items_category_id', 'menu_items', ['category_id'], unique=False)
    op.create_index('idx_menu_items_external_id', 'menu_items', ['external_id'], unique=False)
    op.create_index('idx_menu_items_is_available', 'menu_items', ['is_available'], unique=False, postgresql_where=sa.text('is_available = true'))
    op.create_index('idx_menu_items_not_deleted', 'menu_items', ['is_deleted'], unique=False, postgresql_where=sa.text('is_deleted = false'))
    op.create_index('idx_menu_items_price', 'menu_items', ['price'], unique=False)
    op.create_index('idx_menu_items_name_trgm', 'menu_items', ['name'], unique=False, postgresql_using='gin', postgresql_ops={'name': 'gin_trgm_ops'})
    op.create_index('idx_menu_items_description_trgm', 'menu_items', ['description'], unique=False, postgresql_using='gin', postgresql_ops={'description': 'gin_trgm_ops'})
    op.create_index('idx_menu_items_search_vector', 'menu_items', ['search_vector'], unique=False, postgresql_using='gin')
    op.create_index('idx_menu_items_synced_at', 'menu_items', ['synced_at'], unique=False)
    op.create_index('idx_menu_embeddings_vector', 'menu_embeddings', ['embedding'], unique=False, postgresql_using='hnsw')
    op.create_index('idx_customers_phone', 'customers', ['phone'], unique=False)
    op.create_index('idx_customer_preferences_customer_id', 'customer_preferences', ['customer_id'], unique=False)
    op.create_index('idx_sessions_customer_id', 'sessions', ['customer_id'], unique=False)
    op.create_index('idx_sessions_status', 'sessions', ['status'], unique=False, postgresql_where=sa.text("status = 'active'"))
    op.create_index('idx_sessions_started_at', 'sessions', ['started_at'], unique=False)
    op.create_index('idx_sessions_last_activity', 'sessions', ['last_activity_at'], unique=False)
    op.create_index('idx_orders_customer_id', 'orders', ['customer_id'], unique=False)
    op.create_index('idx_orders_restaurant_id', 'orders', ['restaurant_id'], unique=False)
    op.create_index('idx_orders_status', 'orders', ['status'], unique=False)
    op.create_index('idx_orders_created_at', 'orders', ['created_at'], unique=False)
    op.create_index('idx_orders_payment_status', 'orders', ['payment_status'], unique=False)
    op.create_index('idx_order_items_order_id', 'order_items', ['order_id'], unique=False)
    op.create_index('idx_order_items_menu_item_id', 'order_items', ['menu_item_id'], unique=False)
    op.create_index('idx_conversation_session_id', 'conversation_history', ['session_id'], unique=False)
    op.create_index('idx_conversation_customer_id', 'conversation_history', ['customer_id'], unique=False)
    op.create_index('idx_conversation_created_at', 'conversation_history', ['created_at'], unique=False)
    op.create_index('idx_conversation_role', 'conversation_history', ['role'], unique=False)
    op.create_index('idx_conversation_intent', 'conversation_history', ['intent'], unique=False)
    op.create_index('idx_conversation_session_created', 'conversation_history', ['session_id', 'created_at'], unique=False)

    # Triggers
    op.execute("CREATE OR REPLACE FUNCTION update_updated_at_column() RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = NOW(); RETURN NEW; END; $$ LANGUAGE plpgsql")
    op.execute('CREATE TRIGGER update_restaurants_updated_at BEFORE UPDATE ON restaurants FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()')
    op.execute('CREATE TRIGGER update_menu_items_updated_at BEFORE UPDATE ON menu_items FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()')
    op.execute('CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()')
    op.execute('CREATE TRIGGER update_customer_preferences_updated_at BEFORE UPDATE ON customer_preferences FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()')
    op.execute('CREATE TRIGGER update_sync_metadata_updated_at BEFORE UPDATE ON sync_metadata FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()')

    op.execute("CREATE OR REPLACE FUNCTION update_menu_items_search_vector() RETURNS TRIGGER AS $$ BEGIN NEW.search_vector := setweight(to_tsvector('simple', coalesce(NEW.name, '')), 'A') || setweight(to_tsvector('simple', coalesce(NEW.description, '')), 'B') || setweight(to_tsvector('simple', coalesce(array_to_string(ARRAY(SELECT jsonb_array_elements_text(NEW.ingredients)), ' '), '')), 'C'); RETURN NEW; END; $$ LANGUAGE plpgsql")
    op.execute('CREATE TRIGGER trigger_update_menu_items_search_vector BEFORE INSERT OR UPDATE ON menu_items FOR EACH ROW EXECUTE FUNCTION update_menu_items_search_vector()')


def downgrade() -> None:
    op.execute('DROP TRIGGER IF EXISTS trigger_update_menu_items_search_vector ON menu_items')
    op.execute('DROP FUNCTION IF EXISTS update_menu_items_search_vector()')
    op.execute('DROP TRIGGER IF EXISTS update_sync_metadata_updated_at ON sync_metadata')
    op.execute('DROP TRIGGER IF EXISTS update_customer_preferences_updated_at ON customer_preferences')
    op.execute('DROP TRIGGER IF EXISTS update_orders_updated_at ON orders')
    op.execute('DROP TRIGGER IF EXISTS update_menu_items_updated_at ON menu_items')
    op.execute('DROP TRIGGER IF EXISTS update_restaurants_updated_at ON restaurants')
    op.execute('DROP FUNCTION IF EXISTS update_updated_at_column()')

    op.drop_table('conversation_history')
    op.drop_table('order_items')
    op.drop_table('orders')
    op.drop_table('sessions')
    op.drop_table('customer_preferences')
    op.drop_table('menu_embeddings')
    op.drop_table('menu_items')
    op.drop_table('categories')
    op.drop_table('customers')
    op.drop_table('restaurants')
    op.drop_table('sync_metadata')
