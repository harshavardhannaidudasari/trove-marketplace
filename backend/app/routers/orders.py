import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import Address, CartItem, Order, OrderItem, OrderStatus, Product, User
from app.schemas.order import (
    CheckoutConfirmRequest,
    CheckoutIntentRequest,
    CheckoutIntentResponse,
    OrderOut,
    OrderSummary,
)
from app.services import stripe_service

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])

FREE_SHIPPING_THRESHOLD_CENTS = 5000
FLAT_SHIPPING_CENTS = 599
TAX_RATE = 0.08


def _compute_totals(subtotal_cents: int) -> tuple[int, int, int]:
    shipping = 0 if subtotal_cents >= FREE_SHIPPING_THRESHOLD_CENTS else FLAT_SHIPPING_CENTS
    tax = round(subtotal_cents * TAX_RATE)
    total = subtotal_cents + shipping + tax
    return tax, shipping, total


def _cart_subtotal(db: Session, user_id: uuid.UUID) -> tuple[list[CartItem], int]:
    items = db.query(CartItem).options(joinedload(CartItem.product)).filter(CartItem.user_id == user_id).all()
    if not items:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cart is empty")
    for item in items:
        if item.quantity > item.product.stock_qty:
            raise HTTPException(status.HTTP_409_CONFLICT, f"Not enough stock for {item.product.title}")
    subtotal = sum(item.product.price_cents * item.quantity for item in items)
    return items, subtotal


@router.post("/checkout/intent", response_model=CheckoutIntentResponse)
def create_checkout_intent(payload: CheckoutIntentRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    address = db.get(Address, payload.shipping_address_id)
    if address is None or address.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Shipping address not found")

    _, subtotal = _cart_subtotal(db, current_user.id)
    _, _, total = _compute_totals(subtotal)

    intent = stripe_service.create_payment_intent(total, "usd", order_id=str(uuid.uuid4()))
    return CheckoutIntentResponse(client_secret=intent.client_secret, order_preview_total_cents=total)


@router.post("/checkout/confirm", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def confirm_checkout(payload: CheckoutConfirmRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    address = db.get(Address, payload.shipping_address_id)
    if address is None or address.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Shipping address not found")

    intent = stripe_service.retrieve_payment_intent(payload.payment_intent_id)
    if intent.status not in ("succeeded", "processing"):
        raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, f"Payment not completed (status: {intent.status})")

    cart_items, subtotal = _cart_subtotal(db, current_user.id)
    tax, shipping, total = _compute_totals(subtotal)

    order = Order(
        user_id=current_user.id,
        status=OrderStatus.paid if intent.status == "succeeded" else OrderStatus.pending,
        subtotal_cents=subtotal,
        tax_cents=tax,
        shipping_cents=shipping,
        total_cents=total,
        shipping_address_id=address.id,
        stripe_payment_intent_id=intent.id,
    )
    db.add(order)
    db.flush()

    for item in cart_items:
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                product_title_snapshot=item.product.title,
                unit_price_cents_snapshot=item.product.price_cents,
                quantity=item.quantity,
            )
        )
        item.product.stock_qty -= item.quantity
        db.delete(item)

    db.commit()
    db.refresh(order)
    return order


@router.get("", response_model=list[OrderSummary])
def list_orders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    orders = db.query(Order).options(joinedload(Order.items)).filter(Order.user_id == current_user.id).order_by(Order.created_at.desc()).all()
    return [
        OrderSummary(id=o.id, status=o.status, total_cents=o.total_cents, created_at=o.created_at, item_count=sum(i.quantity for i in o.items))
        for o in orders
    ]


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = (
        db.query(Order)
        .options(joinedload(Order.items), joinedload(Order.shipping_address))
        .filter(Order.id == order_id)
        .first()
    )
    if order is None or order.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    return order
