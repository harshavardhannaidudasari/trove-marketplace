import stripe

from app.core.config import settings

stripe.api_key = settings.stripe_secret_key


def create_payment_intent(amount_cents: int, currency: str, order_id: str) -> stripe.PaymentIntent:
    return stripe.PaymentIntent.create(
        amount=amount_cents,
        currency=currency,
        metadata={"order_id": order_id},
        automatic_payment_methods={"enabled": True},
    )


def retrieve_payment_intent(payment_intent_id: str) -> stripe.PaymentIntent:
    return stripe.PaymentIntent.retrieve(payment_intent_id)


def construct_webhook_event(payload: bytes, sig_header: str) -> stripe.Event:
    return stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
