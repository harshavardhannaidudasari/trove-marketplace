# Trove Marketplace — Web (React + TypeScript + Vite)

The marketplace frontend: browse/search/filter/sort 900+ products across 16 departments, product
detail with reviews, cart, checkout with a simulated Card/UPI/Wallet/COD payment gateway, order
history — all against the FastAPI backend in `../backend`. INR pricing throughout. Dark,
glassmorphic, motion-driven UI (Framer Motion page/element transitions, an ambient animated
gradient backdrop, tilt-on-hover product cards) built to feel like a real, modern storefront.

## Setup

```bash
cd web
npm install
cp .env.example .env   # defaults already point at http://localhost:8000/api/v1
npm run dev
```

Requires the backend running (`../backend`, see its README) — this app talks to it directly, no
mocked data.

- App: http://localhost:5173

**Demo login:** `demo@trove.dev` / `DemoPass123!` (pre-filled on the login page) — has a saved
India address and a paid order already in history.

## Payments

Checkout (`components/checkout/PaymentForm.tsx`) is a tabbed Card / UPI / Wallet / Cash on
Delivery form talking directly to the backend's simulated payment gateway — no external payment
SDK, no publishable/secret key pair required. Test card `4242 4242 4242 4242` (any future expiry,
any CVV) always succeeds; a number ending in `0002` simulates a decline; UPI id `fail@upi`
simulates a decline. See the backend README for the full simulation rules.

## Docker

```bash
docker compose up --build   # from repo root
```

Builds this app with Vite and serves the static bundle via nginx on `:8081` (see `Dockerfile` /
`nginx.conf`).

## Architecture

- **`api/`** — typed fetch client (`client.ts`, auto-attaches the bearer token, retries once via
  refresh token on a 401, formats prices as INR) plus one module per backend router (`auth`,
  `catalog`, `cart`, `orders`). `types.ts` mirrors the backend's Pydantic schemas field-for-field.
- **`store/`** — two small Zustand stores: `authStore` (tokens persisted to `localStorage`, user
  profile) and `cartStore` (server-backed cart — this API has no guest cart, so "add to cart" while
  signed out prompts sign-in rather than faking local state that would diverge from the backend).
- **`components/layout`** — `Navbar`, `Footer`, `AnimatedBackground` (the ambient blob/spotlight
  backdrop, pure CSS transforms, no canvas/WebGL dependency).
- **`components/product`**, **`components/checkout`**, **`components/ui`** — presentational pieces
  (`ProductCard` with cursor-tracked 3D tilt, `StarRating`, glass `Toast` notifications, address
  form, tabbed `PaymentForm`).
- **`pages/`** — one per route: Home, Browse (category/search/filter/sort/pagination via URL
  params), Product detail, Cart, Checkout, Login/Register, Orders, Order detail.

## What's verified

| Check | Result |
|---|---|
| `tsc -b` (typecheck, whole project) | ✅ clean |
| Full golden path in a real Chrome browser against the live backend | ✅ — sign in with demo account, browse 900-product catalog with category sidebar, open a product, add to cart, checkout (address → card payment tab → pay), order confirmation page shows payment method + mock reference, order appears in order history |
| Card / UPI / wallet / COD checkout, including simulated declines | ✅ — exercised via curl against the live API and via the card tab in-browser |

## Tech

React 19 · TypeScript · Vite · React Router · Zustand · Framer Motion
