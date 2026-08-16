import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.models.order import OrderStatus
from app.schemas.address import AddressOut

PaymentMethodType = Literal["card", "upi", "wallet", "cod"]


class CardPayload(BaseModel):
    number: str = Field(min_length=12, max_length=19)
    expiry_month: int = Field(ge=1, le=12)
    expiry_year: int = Field(ge=2024, le=2100)
    cvv: str = Field(min_length=3, max_length=4)
    name_on_card: str = Field(min_length=1, max_length=120)


class UpiPayload(BaseModel):
    vpa: str = Field(min_length=3, max_length=120)


class WalletPayload(BaseModel):
    provider: str = Field(min_length=2, max_length=40)


class CheckoutRequest(BaseModel):
    shipping_address_id: uuid.UUID
    method: PaymentMethodType
    card: CardPayload | None = None
    upi: UpiPayload | None = None
    wallet: WalletPayload | None = None

    @model_validator(mode="after")
    def check_payload_matches_method(self) -> "CheckoutRequest":
        if self.method == "card" and self.card is None:
            raise ValueError("card details are required for method=card")
        if self.method == "upi" and self.upi is None:
            raise ValueError("upi details are required for method=upi")
        if self.method == "wallet" and self.wallet is None:
            raise ValueError("wallet details are required for method=wallet")
        return self


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
    payment_method: str | None
    payment_reference: str | None
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
