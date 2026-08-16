import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import CartItem, Product, User
from app.schemas.cart import CartItemAdd, CartItemOut, CartItemUpdate, CartOut

router = APIRouter(prefix="/api/v1/cart", tags=["cart"])


def _build_cart_out(db: Session, user: User) -> CartOut:
    rows = db.query(CartItem).options(joinedload(CartItem.product).joinedload(Product.images)).filter(CartItem.user_id == user.id).all()
    items = [
        CartItemOut(
            product_id=row.product_id,
            title=row.product.title,
            slug=row.product.slug,
            thumbnail_url=row.product.thumbnail_url,
            unit_price_cents=row.product.price_cents,
            quantity=row.quantity,
            line_total_cents=row.product.price_cents * row.quantity,
        )
        for row in rows
    ]
    return CartOut(items=items, subtotal_cents=sum(i.line_total_cents for i in items), item_count=sum(i.quantity for i in items))


@router.get("", response_model=CartOut)
def get_cart(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _build_cart_out(db, current_user)


@router.post("/items", response_model=CartOut, status_code=status.HTTP_201_CREATED)
def add_item(payload: CartItemAdd, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    product = db.get(Product, payload.product_id)
    if product is None or not product.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")

    existing = db.query(CartItem).filter(CartItem.user_id == current_user.id, CartItem.product_id == payload.product_id).first()
    if existing:
        existing.quantity += payload.quantity
    else:
        db.add(CartItem(user_id=current_user.id, product_id=payload.product_id, quantity=payload.quantity))
    db.commit()
    return _build_cart_out(db, current_user)


@router.patch("/items/{product_id}", response_model=CartOut)
def update_item(product_id: uuid.UUID, payload: CartItemUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(CartItem).filter(CartItem.user_id == current_user.id, CartItem.product_id == product_id).first()
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not in cart")
    item.quantity = payload.quantity
    db.commit()
    return _build_cart_out(db, current_user)


@router.delete("/items/{product_id}", response_model=CartOut)
def remove_item(product_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(CartItem).filter(CartItem.user_id == current_user.id, CartItem.product_id == product_id).first()
    if item:
        db.delete(item)
        db.commit()
    return _build_cart_out(db, current_user)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def clear_cart(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(CartItem).filter(CartItem.user_id == current_user.id).delete()
    db.commit()
    return None
