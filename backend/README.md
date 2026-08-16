# Trove Marketplace — Backend (FastAPI)

REST API for the Trove Marketplace demo: auth, product catalog, cart, checkout (simulated
payment gateway — card/UPI/wallet/COD), orders, reviews. Prices are in INR.

## Setup

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # defaults already work against a local Postgres
python -m alembic upgrade head
python -m app.seed.seed --count 900
```

## Running

```bash
python -m uvicorn app.main:app --reload
```

- API base: http://localhost:8000/api/v1
- Interactive docs (Swagger): http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

**Demo login:** `demo@trove.dev` / `DemoPass123!` (has a pre-existing paid order in history).

## Payments — simulated, zero API keys needed

Checkout does **not** call any external payment processor (no Stripe/Razorpay/etc). It's a
self-contained mock gateway (`app/services/mock_payment_service.py`) supporting:

- **Card** — any Luhn-valid card number succeeds (try `4242 4242 4242 4242`). Numbers ending in
  `0002`, `0069`, or `0119` simulate a decline. Brand (Visa/Mastercard/Amex/RuPay) is detected
  from the number prefix. No raw card number/CVV is ever persisted — only brand + last 4 digits.
- **UPI** — any well-formed VPA (`name@bank`) succeeds; `fail@upi` / `decline@ybl` simulate a
  decline.
- **Wallet** — Paytm / PhonePe / Google Pay / Amazon Pay / MobiKwik, ~3% random decline rate to
  demonstrate failure handling.
- **Cash on Delivery** — always succeeds, order is created with `pending` status instead of `paid`.

Every successful payment gets a `MOCK-xxxxxxxxxxxx` reference id stored on the order
(`payment_reference` / `payment_method` columns).

## Docker

```bash
docker compose up --build
```

Brings up Postgres, runs Alembic migrations + seeds the catalog automatically
(`docker-entrypoint.sh`), and starts the API on `:8000`. See the root `docker-compose.yml`.

## What's verified (last real run, against a local PostgreSQL 17 instance)

| Flow | Result |
|---|---|
| Register → JWT issued → `/auth/me` | ✅ |
| Browse categories (16 departments, 55 subcategories) | ✅ |
| List/search/filter/sort products (900 seeded, INR pricing) | ✅ |
| Add to cart, cart totals | ✅ |
| Add shipping address (India-formatted demo data) | ✅ |
| Checkout preview (subtotal/GST/shipping/total) | ✅ |
| Checkout with card (success + simulated decline) | ✅ |
| Checkout with UPI | ✅ |
| Checkout with wallet | ✅ |
| Checkout with Cash on Delivery | ✅ |
| Order history / order detail (payment method + reference shown) | ✅ |

All exercised end-to-end via curl against a live `uvicorn` process backed by real Postgres, then
again through the actual browser UI (see web README).

## Tech

FastAPI · SQLAlchemy 2.0 · Alembic · PostgreSQL · JWT (python-jose) · passlib/bcrypt · Faker (seed data)
