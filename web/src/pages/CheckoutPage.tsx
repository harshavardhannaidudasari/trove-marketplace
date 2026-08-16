import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Elements } from "@stripe/react-stripe-js";
import { usersApi, ordersApi } from "../api/orders";
import type { Address, AddressInput } from "../api/types";
import { ApiError } from "../api/types";
import { formatPrice } from "../api/client";
import { getStripe } from "../lib/stripe";
import { useAuth } from "../hooks/useAuth";
import { useCartStore } from "../store/cartStore";
import { useToast } from "../components/ui/Toast";
import { AddressForm } from "../components/checkout/AddressForm";
import { PaymentForm } from "../components/checkout/PaymentForm";
import "./checkout.css";

type Step = "loading" | "address" | "payment-error" | "payment";

export function CheckoutPage() {
  const navigate = useNavigate();
  const { push } = useToast();
  const { isAuthenticated } = useAuth();
  const { cart, fetch: fetchCart } = useCartStore();

  const [step, setStep] = useState<Step>("loading");
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [selectedAddressId, setSelectedAddressId] = useState<string | null>(null);
  const [addingAddress, setAddingAddress] = useState(false);
  const [creatingIntent, setCreatingIntent] = useState(false);
  const [paymentError, setPaymentError] = useState<string | null>(null);
  const [clientSecret, setClientSecret] = useState<string | null>(null);
  const [previewTotal, setPreviewTotal] = useState<number | null>(null);

  useEffect(() => {
    if (!isAuthenticated) return;
    usersApi.addresses().then((list) => {
      setAddresses(list);
      const preferred = list.find((a) => a.is_default) ?? list[0];
      if (preferred) setSelectedAddressId(preferred.id);
      setStep("address");
    });
  }, [isAuthenticated]);

  async function handleAddAddress(payload: AddressInput) {
    setAddingAddress(true);
    try {
      const address = await usersApi.addAddress(payload);
      setAddresses((prev) => [...prev, address]);
      setSelectedAddressId(address.id);
    } catch (e) {
      push(e instanceof Error ? e.message : "Could not save address", "error");
    } finally {
      setAddingAddress(false);
    }
  }

  async function proceedToPayment() {
    if (!selectedAddressId) return;
    setCreatingIntent(true);
    setPaymentError(null);
    try {
      const intent = await ordersApi.createIntent(selectedAddressId);
      setClientSecret(intent.client_secret);
      setPreviewTotal(intent.order_preview_total_cents);
      setStep("payment");
    } catch (e) {
      setPaymentError(e instanceof ApiError ? e.message : "Could not start checkout");
      setStep("payment-error");
    } finally {
      setCreatingIntent(false);
    }
  }

  async function handlePaid(paymentIntentId: string) {
    if (!selectedAddressId) return;
    try {
      const order = await ordersApi.confirm(paymentIntentId, selectedAddressId);
      await fetchCart();
      push("Order placed! 🎉", "success");
      navigate(`/orders/${order.id}`);
    } catch (e) {
      push(e instanceof Error ? e.message : "Could not finalize order", "error");
    }
  }

  if (!isAuthenticated) {
    return (
      <div className="empty-state">
        <h3>Sign in to check out</h3>
        <Link to="/login?next=/checkout" className="btn btn-primary" style={{ marginTop: 16 }}>
          Sign in
        </Link>
      </div>
    );
  }

  if (!cart || cart.items.length === 0) {
    return (
      <div className="empty-state">
        <h3>Your cart is empty</h3>
        <Link to="/browse" className="btn btn-primary" style={{ marginTop: 16 }}>
          Browse products
        </Link>
      </div>
    );
  }

  return (
    <div className="container checkout-page">
      <h1 className="section-title">Checkout</h1>
      <div className="checkout-layout">
        <div className="checkout-main">
          <h2 className="checkout-step-title">1. Shipping address</h2>
          {addresses.length > 0 && (
            <div className="address-list">
              {addresses.map((a) => (
                <label key={a.id} className={`address-option glass ${selectedAddressId === a.id ? "selected" : ""}`}>
                  <input
                    type="radio"
                    name="address"
                    checked={selectedAddressId === a.id}
                    onChange={() => {
                      setSelectedAddressId(a.id);
                      setStep("address");
                      setClientSecret(null);
                    }}
                  />
                  <span>
                    {a.line1}
                    {a.line2 ? `, ${a.line2}` : ""}
                    <br />
                    {a.city}, {a.state} {a.postal_code}, {a.country}
                  </span>
                </label>
              ))}
            </div>
          )}

          {addresses.length === 0 && <AddressForm onSubmit={handleAddAddress} submitting={addingAddress} />}

          {addresses.length > 0 && step === "address" && (
            <button className="btn btn-primary" disabled={!selectedAddressId || creatingIntent} onClick={proceedToPayment} style={{ marginTop: 16 }}>
              {creatingIntent ? <span className="spinner" /> : "Continue to payment"}
            </button>
          )}

          {step === "payment-error" && (
            <div className="glass payment-error-panel">
              <h3>Payment service unavailable</h3>
              <p>{paymentError}</p>
              <button className="btn btn-outline" style={{ marginTop: 14 }} onClick={proceedToPayment}>
                Try again
              </button>
            </div>
          )}

          {step === "payment" && clientSecret && (
            <div style={{ marginTop: 24 }}>
              <h2 className="checkout-step-title">2. Payment</h2>
              <Elements stripe={getStripe()} options={{ clientSecret, appearance: { theme: "night", labels: "floating" } }}>
                <PaymentForm total={formatPrice(previewTotal ?? 0)} onPaid={handlePaid} />
              </Elements>
            </div>
          )}
        </div>

        <div className="cart-summary glass checkout-summary">
          <h3>Order summary</h3>
          {cart.items.map((item) => (
            <div key={item.product_id} className="row checkout-summary-line">
              <span>
                {item.title} × {item.quantity}
              </span>
              <span>{formatPrice(item.line_total_cents)}</span>
            </div>
          ))}
          <div className="row cart-summary-line" style={{ marginTop: 12, fontWeight: 700 }}>
            <span>Subtotal</span>
            <span>{formatPrice(cart.subtotal_cents)}</span>
          </div>
          <p className="cart-summary-note">Tax and shipping are calculated by the server at checkout.</p>
        </div>
      </div>
    </div>
  );
}
