from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import Category, Product, Review, User
from app.schemas.catalog import ProductDetail, ProductListResponse, ProductSummary, ReviewCreate, ReviewOut

router = APIRouter(prefix="/api/v1/products", tags=["products"])


@router.get("", response_model=ProductListResponse)
def list_products(
    category: str | None = Query(default=None, description="Category slug"),
    q: str | None = Query(default=None, description="Search text"),
    min_price: float | None = Query(default=None),
    max_price: float | None = Query(default=None),
    sort: str = Query(default="newest", pattern="^(price_asc|price_desc|rating|newest)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=24, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Product).options(joinedload(Product.images)).filter(Product.is_active.is_(True))

    if category:
        cat = db.query(Category).filter(Category.slug == category).first()
        if cat is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Category not found")
        category_ids = [cat.id] + [child.id for child in cat.children]
        query = query.filter(Product.category_id.in_(category_ids))

    if q:
        like = f"%{q}%"
        query = query.filter(Product.title.ilike(like) | Product.description.ilike(like) | Product.brand.ilike(like))

    if min_price is not None:
        query = query.filter(Product.price_cents >= int(min_price * 100))
    if max_price is not None:
        query = query.filter(Product.price_cents <= int(max_price * 100))

    total = query.with_entities(func.count(Product.id)).scalar() or 0

    if sort == "price_asc":
        query = query.order_by(Product.price_cents.asc())
    elif sort == "price_desc":
        query = query.order_by(Product.price_cents.desc())
    elif sort == "rating":
        query = query.order_by(Product.avg_rating.desc())
    else:
        query = query.order_by(Product.sku.desc())

    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return ProductListResponse(
        items=[ProductSummary.model_validate(p) for p in items], total=total, page=page, page_size=page_size
    )


@router.get("/{slug}", response_model=ProductDetail)
def get_product(slug: str, db: Session = Depends(get_db)):
    product = db.query(Product).options(joinedload(Product.images)).filter(Product.slug == slug).first()
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    return product


@router.get("/{slug}/reviews", response_model=list[ReviewOut])
def get_reviews(slug: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.slug == slug).first()
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    reviews = db.query(Review).options(joinedload(Review.user)).filter(Review.product_id == product.id).order_by(Review.created_at.desc()).all()
    return [ReviewOut(id=r.id, rating=r.rating, title=r.title, body=r.body, reviewer_name=r.user.full_name) for r in reviews]


@router.post("/{slug}/reviews", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def add_review(slug: str, payload: ReviewCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.slug == slug).first()
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    if not (1 <= payload.rating <= 5):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Rating must be between 1 and 5")

    existing = db.query(Review).filter(Review.product_id == product.id, Review.user_id == current_user.id).first()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "You already reviewed this product")

    review = Review(product_id=product.id, user_id=current_user.id, **payload.model_dump())
    db.add(review)
    db.flush()

    agg = db.query(func.avg(Review.rating), func.count(Review.id)).filter(Review.product_id == product.id).one()
    product.avg_rating = round(float(agg[0] or 0), 1)
    product.review_count = agg[1] or 0

    db.commit()
    db.refresh(review)
    return ReviewOut(id=review.id, rating=review.rating, title=review.title, body=review.body, reviewer_name=current_user.full_name)
