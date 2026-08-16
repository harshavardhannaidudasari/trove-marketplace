from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Order, OrderStatus
from app.services import stripe_service

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


@router.post("/stripe", status_code=status.HTTP_204_NO_CONTENT)
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe_service.construct_webhook_event(payload, sig_header)
    except Exception:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid webhook signature")

    if event["type"] == "payment_intent.succeeded":
        intent_id = event["data"]["object"]["id"]
        order = db.query(Order).filter(Order.stripe_payment_intent_id == intent_id).first()
        if order and order.status != OrderStatus.paid:
            order.status = OrderStatus.paid
            db.commit()

    return None
