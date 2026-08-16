# Trove Marketplace — Web (React + TypeScript + Vite)

The marketplace frontend: browse/search/filter/sort 200+ products, product detail with reviews,
cart, Stripe checkout, order history — all against the FastAPI backend in `../backend`. Dark,
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
address and a paid order already in history.

## Stripe

Checkout needs a **publishable** key (`pk_test_...`) in `web/.env` as
`VITE_STRIPE_PUBLISHABLE_KEY`, matching the **secret** key the backend has in `backend/.env` (same
Stripe account, test mode). Without it, checkout fails with a clear on-screen message rather than
a crash — the frontend surfaces the backend's own `502` explanation verbatim (see backend README).
Test card: `4242 4242 4242 4242`, any future expiry, any CVC.

## Architecture

- **`api/`** — typed fetch client (`client.ts`, auto-attaches the bearer token, retries once via
  refresh token on a 401) plus one module per backend router (`auth`, `catalog`, `cart`, `orders`).
  `types.ts` mirrors the backend's Pydantic schemas field-for-field (prices are cents, as integers,
  matching the API).
- **`store/`** — two small Zustand stores: `authStore` (tokens persisted to `localStorage`, user
  profile) and `cartStore` (server-backed cart — this API has no guest cart, so "add to cart" while
  signed out prompts sign-in rather than faking local state that would diverge from the backend).
- **`components/layout`** — `Navbar`, `Footer`, `AnimatedBackground` (the ambient blob/spotlight
  backdrop, pure CSS transforms, no canvas/WebGL dependency).
- **`components/product`**, **`components/checkout`**, **`components/ui`** — presentational pieces
  (`ProductCard` with cursor-tracked 3D tilt, `StarRating`, glass `Toast` notifications, address
  and Stripe `PaymentElement` forms).
- **`pages/`** — one per route: Home, Browse (category/search/filter/sort/pagination via URL
  params), Product detail, Cart, Checkout, Login/Register, Orders, Order detail.

## What's verified

| Check | Result |
|---|---|
| `tsc -b` (typecheck, whole project) | ✅ clean |
| `npm run build` (production bundle) | ✅ builds, 482 modules, no errors |
| `npm run lint` (oxlint) | ✅ only one harmless Fast-Refresh warning (Toast.tsx exporting both a component and a hook) |
| Every API call the frontend makes, exercised directly against the live backend via curl with the exact request shape the client sends | ✅ — CORS preflight from `localhost:5173` allowed; form-urlencoded login; `/auth/me`; `/cart` get/add/clear; `/orders` list; `/users/me/addresses`; checkout intent's real `502` when Stripe isn't configured |
| **Real browser walkthrough** (Chrome, driven live against the running backend) | ✅ — home page (hero, category tiles, trending/new grids, all animations settle correctly), browse (sidebar categories, price/sort filters, pagination), product detail (gallery, add-to-cart), sign-out add-to-cart → toast + redirect to `/login?next=...` → sign-in → redirected back → add-to-cart succeeds with animated cart badge, cart page (qty stepper, remove), checkout (address auto-selected → "Payment service unavailable" panel renders the backend's exact `502` message, since no Stripe key is configured in this dev env), order history (shows the seeded demo order), order detail (items/subtotal/tax/shipping/total, shipping address) |

**Not yet verified:** the full Stripe Elements payment form itself (needs a real
`pk_test_...`/`sk_test_...` key pair, which this dev environment doesn't have configured) and
responsive layout at narrow/mobile viewport widths.

## Tech

React 19 · TypeScript · Vite · React Router · Zustand · Framer Motion · Stripe Elements
