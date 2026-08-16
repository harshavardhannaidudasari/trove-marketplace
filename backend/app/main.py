import stripe
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.routers import auth, cart, categories, orders, products, users, webhooks

app = FastAPI(title="Trove Marketplace API", version="1.0.0")


@app.exception_handler(stripe.error.AuthenticationError)
async def stripe_auth_error_handler(request: Request, exc: stripe.error.AuthenticationError):
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={
            "detail": "Payment service is not configured. Set a real Stripe test secret key "
            "(sk_test_...) in backend/.env as STRIPE_SECRET_KEY, then restart the server."
        },
    )


@app.exception_handler(stripe.error.StripeError)
async def stripe_error_handler(request: Request, exc: stripe.error.StripeError):
    return JSONResponse(status_code=status.HTTP_502_BAD_GATEWAY, content={"detail": f"Payment service error: {exc.user_message or str(exc)}"})

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(webhooks.router)


@app.get("/api/v1/health", tags=["health"])
def health():
    return {"status": "ok"}
