"""Simulated payment gateway.

No external processor, no real money movement, no network calls. Accepts
card / UPI / wallet payloads, applies simple test-mode rules (Luhn check,
magic decline values) and returns a mock reference id. This is what makes
checkout work with zero API keys.
"""

import random
import re
import uuid
from dataclasses import dataclass

CARD_BRAND_PREFIXES = [
    ("Rupay", re.compile(r"^6")),
    ("Amex", re.compile(r"^3[47]")),
    ("Mastercard", re.compile(r"^5[1-5]")),
    ("Visa", re.compile(r"^4")),
]

# Card numbers ending in these digits always decline, for demoing failure states.
DECLINE_SUFFIXES = {"0002", "0069", "0119"}
UPI_DECLINE_HANDLES = {"fail@upi", "decline@ybl"}


@dataclass
class PaymentResult:
    success: bool
    reference: str
    method_label: str
    failure_reason: str | None = None


def _luhn_valid(number: str) -> bool:
    digits = [int(d) for d in number]
    checksum = 0
    parity = len(digits) % 2
    for i, digit in enumerate(digits):
        if i % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return checksum % 10 == 0


def _card_brand(number: str) -> str:
    for brand, pattern in CARD_BRAND_PREFIXES:
        if pattern.match(number):
            return brand
    return "Card"


def _new_reference() -> str:
    return f"MOCK-{uuid.uuid4().hex[:14].upper()}"


def process_card_payment(number: str, expiry_month: int, expiry_year: int, cvv: str, name_on_card: str) -> PaymentResult:
    digits = re.sub(r"\D", "", number)
    brand = _card_brand(digits)

    if len(digits) < 13 or len(digits) > 19 or not _luhn_valid(digits):
        return PaymentResult(False, "", brand, "Card number is invalid")
    if not (2 <= len(cvv) <= 4):
        return PaymentResult(False, "", brand, "CVV is invalid")
    if digits[-4:] in DECLINE_SUFFIXES:
        return PaymentResult(False, "", brand, "Card was declined by issuing bank")

    last4 = digits[-4:]
    return PaymentResult(True, _new_reference(), f"{brand} •••• {last4}")


def process_upi_payment(vpa: str) -> PaymentResult:
    if not re.match(r"^[\w.\-]{2,}@[a-zA-Z]{2,}$", vpa):
        return PaymentResult(False, "", "UPI", "UPI ID is invalid")
    if vpa.lower() in UPI_DECLINE_HANDLES:
        return PaymentResult(False, "", "UPI", "Payment declined - insufficient balance")
    return PaymentResult(True, _new_reference(), f"UPI ({vpa})")


WALLET_PROVIDERS = {"paytm", "phonepe", "gpay", "amazonpay", "mobikwik"}
WALLET_LABELS = {
    "paytm": "Paytm Wallet",
    "phonepe": "PhonePe",
    "gpay": "Google Pay",
    "amazonpay": "Amazon Pay Balance",
    "mobikwik": "MobiKwik",
}


def process_wallet_payment(provider: str) -> PaymentResult:
    provider = provider.lower()
    if provider not in WALLET_PROVIDERS:
        return PaymentResult(False, "", "Wallet", "Unsupported wallet provider")
    # Small deliberate random-failure rate so the flow demonstrably handles declines too.
    if random.random() < 0.03:
        return PaymentResult(False, "", WALLET_LABELS[provider], "Wallet balance too low")
    return PaymentResult(True, _new_reference(), WALLET_LABELS[provider])


def process_cod() -> PaymentResult:
    return PaymentResult(True, _new_reference(), "Cash on Delivery")
