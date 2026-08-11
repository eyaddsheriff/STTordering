# ═══════════════════════════════════════════════
# models/__init__.py — SQLAlchemy Models Package
# ═══════════════════════════════════════════════

from app.db.base import Base

# ⚠️ مهم: menu_embedding قبل menu_item عشان SQLAlchemy يلاقي الـ class
from app.models.restaurant import Restaurant
from app.models.category import Category
from app.models.menu_embedding import MenuEmbedding      # ← قبل menu_item
from app.models.menu_item import MenuItem                 # ← بعد menu_embedding
from app.models.customer import Customer
from app.models.customer_preference import CustomerPreference
from app.models.session import Session
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.conversation import Conversation
from app.models.sync_metadata import SyncMetadata

__all__ = [
    "Base",
    "Restaurant",
    "Category",
    "MenuItem",
    "MenuEmbedding",
    "Customer",
    "CustomerPreference",
    "Session",
    "Order",
    "OrderItem",
    "Conversation",
    "SyncMetadata",
]