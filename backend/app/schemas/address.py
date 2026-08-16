import uuid

from pydantic import BaseModel, Field


class AddressCreate(BaseModel):
    line1: str = Field(min_length=1, max_length=255)
    line2: str | None = None
    city: str = Field(min_length=1, max_length=120)
    state: str = Field(min_length=1, max_length=120)
    postal_code: str = Field(min_length=1, max_length=20)
    country: str = Field(default="IN", min_length=2, max_length=2)
    is_default: bool = False


class AddressOut(AddressCreate):
    id: uuid.UUID

    class Config:
        from_attributes = True
