import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.order import OrderStatus
from app.schemas.address import AddressOut


class CheckoutIntentRequest(BaseModel):
    shipping_address_id: uuid.UUID


class CheckoutIntentResponse(BaseModel):
    client_secret: str
    order_preview_total_cents: int


class CheckoutConfirmRequest(BaseModel):
    payment_intent_id: str
    shipping_address_id: uuid.UUID


class OrderItemOut(BaseModel):
    product_id: uuid.UUID
    product_title_snapshot: str
    unit_price_cents_snapshot: int
    quantity: int

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: uuid.UUID
    status: OrderStatus
    subtotal_cents: int
    tax_cents: int
    shipping_cents: int
    total_cents: int
    created_at: datetime
    shipping_address: AddressOut
    items: list[OrderItemOut]

    class Config:
        from_attributes = True


class OrderSummary(BaseModel):
    id: uuid.UUID
    status: OrderStatus
    total_cents: int
    created_at: datetime
    item_count: int

    class Config:
        from_attributes = True
