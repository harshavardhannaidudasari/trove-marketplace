import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { usersApi, ordersApi } from "../api/orders";
import type { Address, AddressInput, CheckoutPreview, CheckoutRequest } from "../api/types";
import { ApiError } from "../api/types";
import { formatPrice } from "../api/client";
import { useAuth } from "../hooks/useAuth";
import { useCartStore } from "../store/cartStore";
import { useToast } from "../components/ui/Toast";
import { AddressForm } from "../components/checkout/AddressForm";
import { PaymentForm } from "../components/checkout/PaymentForm";
import "./checkout.css";

type Step = "loading" | "address" | "payment";

export function CheckoutPage() {
  const navigate = useNavigate();
  const { push } = useToast();
  const { isAuthenticated } = useAuth();
  const { cart, fetch: fetchCart } = useCartStore();

  const [step, setStep] = useState<Step>("loading");
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [selectedAddressId, setSelectedAddressId] = useState<string | null>(null);
  const [addingAddress, setAddingAddress] = useState(false);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [preview, setPreview] = useState<CheckoutPreview | null>(null);

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
    setLoadingPreview(true);
    try {
      const p = await ordersApi.preview(selectedAddressId);
      setPreview(p);
      setStep("payment");
    } catch (e) {
      push(e instanceof ApiError ? e.message : "Could not start checkout", "error");
    } finally {
      setLoadingPreview(false);
    }
  }

  async function handlePay(payment: Omit<CheckoutRequest, "shipping_address_id">) {
    if (!selectedAddressId) return;
    const order = await ordersApi.checkout({ shipping_address_id: selectedAddressId, ...payment });
    await fetchCart();
    push(payment.method === "cod" ? "Order placed! Pay on delivery." : "Payment successful — order placed! 🎉", "success");
    navigate(`/orders/${order.id}`);
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
                      setPreview(null);
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
            <button className="btn btn-primary" disabled={!selectedAddressId || loadingPreview} onClick={proceedToPayment} style={{ marginTop: 16 }}>
              {loadingPreview ? <span className="spinner" /> : "Continue to payment"}
            </button>
          )}

          {step === "payment" && preview && (
            <div style={{ marginTop: 24 }}>
              <h2 className="checkout-step-title">2. Payment</h2>
              <PaymentForm total={formatPrice(preview.total_cents)} onSubmit={handlePay} />
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
          <div className="row cart-summary-line" style={{ marginTop: 12 }}>
            <span>Subtotal</span>
            <span>{formatPrice(cart.subtotal_cents)}</span>
          </div>
          {preview ? (
            <>
              <div className="row cart-summary-line">
                <span>GST (18%)</span>
                <span>{formatPrice(preview.tax_cents)}</span>
              </div>
              <div className="row cart-summary-line">
                <span>Shipping</span>
                <span>{preview.shipping_cents === 0 ? "FREE" : formatPrice(preview.shipping_cents)}</span>
              </div>
              <div className="row cart-summary-line" style={{ marginTop: 8, fontWeight: 700 }}>
                <span>Total</span>
                <span>{formatPrice(preview.total_cents)}</span>
              </div>
            </>
          ) : (
            <p className="cart-summary-note">Tax and shipping are calculated at the next step.</p>
          )}
        </div>
      </div>
    </div>
  );
}
