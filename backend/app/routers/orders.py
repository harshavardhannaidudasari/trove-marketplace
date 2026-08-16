import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import Address, CartItem, Order, OrderItem, OrderStatus, User
from app.schemas.order import CheckoutRequest, OrderOut, OrderSummary
from app.services import mock_payment_service

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])

FREE_SHIPPING_THRESHOLD_CENTS = 50000
FLAT_SHIPPING_CENTS = 4900
TAX_RATE = 0.18  # GST


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


@router.get("/checkout/preview")
def checkout_preview(shipping_address_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    address = db.get(Address, shipping_address_id)
    if address is None or address.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Shipping address not found")
    _, subtotal = _cart_subtotal(db, current_user.id)
    tax, shipping, total = _compute_totals(subtotal)
    return {"subtotal_cents": subtotal, "tax_cents": tax, "shipping_cents": shipping, "total_cents": total}


@router.post("/checkout", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def checkout(payload: CheckoutRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    address = db.get(Address, payload.shipping_address_id)
    if address is None or address.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Shipping address not found")

    cart_items, subtotal = _cart_subtotal(db, current_user.id)
    tax, shipping, total = _compute_totals(subtotal)

    if payload.method == "card":
        c = payload.card
        result = mock_payment_service.process_card_payment(c.number, c.expiry_month, c.expiry_year, c.cvv, c.name_on_card)
    elif payload.method == "upi":
        result = mock_payment_service.process_upi_payment(payload.upi.vpa)
    elif payload.method == "wallet":
        result = mock_payment_service.process_wallet_payment(payload.wallet.provider)
    else:
        result = mock_payment_service.process_cod()

    if not result.success:
        raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, result.failure_reason or "Payment failed")

    order_status = OrderStatus.pending if payload.method == "cod" else OrderStatus.paid
    order = Order(
        user_id=current_user.id,
        status=order_status,
        subtotal_cents=subtotal,
        tax_cents=tax,
        shipping_cents=shipping,
        total_cents=total,
        shipping_address_id=address.id,
        payment_method=result.method_label,
        payment_reference=result.reference,
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
