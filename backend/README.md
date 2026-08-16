# Trove Marketplace — Backend (FastAPI)

REST API for the Trove Marketplace demo: auth, product catalog, cart, checkout (Stripe test mode), orders, reviews.

## Setup

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # then edit DATABASE_URL and STRIPE_SECRET_KEY
python -m alembic upgrade head
python -m app.seed.seed --count 200
```

## Running

```bash
python -m uvicorn app.main:app --reload
```

- API base: http://localhost:8000/api/v1
- Interactive docs (Swagger): http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

**Demo login:** `demo@trove.dev` / `DemoPass123!` (has a pre-existing paid order in history).

## Stripe (required for checkout to fully work)

Checkout uses **Stripe test mode** — it never touches real money, but it does need a real (free) Stripe account's test API keys:

1. Create a free account at https://dashboard.stripe.com/register (or sign in).
2. Copy your **test mode** secret key (`sk_test_...`) from https://dashboard.stripe.com/test/apikeys into `backend/.env` as `STRIPE_SECRET_KEY`.
3. Copy the matching **publishable key** (`pk_test_...`) into the web/mobile `.env` files (see their READMEs).
4. For the webhook (optional but recommended): `stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe`, then put the `whsec_...` it prints into `STRIPE_WEBHOOK_SECRET`.
5. Test card: `4242 4242 4242 4242`, any future expiry, any CVC, any postal code.

Without a real key, every other feature works normally — only `/orders/checkout/intent` and `/checkout/confirm` need it, and they fail with a clean `502` (not a crash) explaining exactly what to do if the key is missing/invalid.

## What's verified (last real run, against a real local PostgreSQL 17 instance)

| Flow | Result |
|---|---|
| Register → JWT issued → `/auth/me` | ✅ |
| Browse categories (10 top-level, ~34 subcategories) | ✅ |
| List/search/filter/sort products (200 seeded) | ✅ |
| Product detail with images | ✅ |
| Add to cart, cart totals | ✅ |
| Add shipping address | ✅ |
| Post a product review, average rating recalculated | ✅ |
| Checkout intent → reaches Stripe's real API, fails cleanly without a valid test key | ✅ |
| Order history (empty for new users, populated for seeded demo account) | ✅ |

## Real bugs found only by running this (not by review)

1. **Postgres GROUP BY error on product listing.** The `total` count query reused the same SQLAlchemy query object *after* `.order_by()` had been applied, so Postgres's strict GROUP BY rules rejected `SELECT count(...) ... ORDER BY products.sku` (the order column wasn't aggregated). `mvn`-style unit tests wouldn't have caught this without a real Postgres backend (SQLite is lenient about this and would have silently allowed it). Fixed by computing the count *before* applying any `order_by`.
2. **bcrypt/passlib version mismatch** produced a harmless-but-scary traceback on every password hash (`AttributeError: module 'bcrypt' has no attribute '__about__'`) — passlib 1.7.4's version-sniffing code doesn't understand bcrypt 4.2's new layout. Pinned `bcrypt==4.0.1` to silence it; hashing/verification were never actually broken, just noisy.
3. **SQLAlchemy 2.0.36 + Python 3.14 typing incompatibility** — `Mapped["ForwardRef"]` resolution crashed with `TypeError: descriptor '__getitem__' requires a 'typing.Union' object but received a 'tuple'` on every model with a forward-referenced relationship. Fixed by bumping to SQLAlchemy 2.0.52.
4. **psycopg[binary] 3.2.3 and pydantic-core 2.27 had no prebuilt wheels for Python 3.14**, and pydantic-core tried (and failed) to compile from source via a PyO3 version too old for 3.14. Bumped `psycopg[binary]` to 3.2.10 and `pydantic` to 2.13.4.

## Tech

FastAPI · SQLAlchemy 2.0 · Alembic · PostgreSQL · JWT (python-jose) · passlib/bcrypt · Stripe · Faker (seed data)
