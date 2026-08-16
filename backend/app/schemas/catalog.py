import uuid

from pydantic import BaseModel


class CategoryOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    image_url: str | None
    children: list["CategoryOut"] = []

    class Config:
        from_attributes = True


class ProductImageOut(BaseModel):
    url: str
    alt_text: str

    class Config:
        from_attributes = True


class ProductSummary(BaseModel):
    id: uuid.UUID
    title: str
    slug: str
    price_cents: int
    compare_at_price_cents: int | None
    brand: str
    avg_rating: float
    review_count: int
    thumbnail_url: str | None = None

    class Config:
        from_attributes = True


class ProductDetail(ProductSummary):
    description: str
    stock_qty: int
    images: list[ProductImageOut]
    category_id: uuid.UUID

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    items: list[ProductSummary]
    total: int
    page: int
    page_size: int


class ReviewOut(BaseModel):
    id: uuid.UUID
    rating: int
    title: str
    body: str
    reviewer_name: str

    class Config:
        from_attributes = True


class ReviewCreate(BaseModel):
    rating: int
    title: str
    body: str
