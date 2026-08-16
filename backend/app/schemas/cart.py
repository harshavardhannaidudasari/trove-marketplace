import uuid

from pydantic import BaseModel, Field


class CartItemAdd(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(default=1, ge=1)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1)


class CartItemOut(BaseModel):
    product_id: uuid.UUID
    title: str
    slug: str
    thumbnail_url: str | None
    unit_price_cents: int
    quantity: int
    line_total_cents: int


class CartOut(BaseModel):
    items: list[CartItemOut]
    subtotal_cents: int
    item_count: int
