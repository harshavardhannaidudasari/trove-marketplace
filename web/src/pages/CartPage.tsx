import { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useCartStore } from "../store/cartStore";
import { useAuth } from "../hooks/useAuth";
import { formatPrice } from "../api/client";
import { useToast } from "../components/ui/Toast";
import "./cart.css";

export function CartPage() {
  const navigate = useNavigate();
  const { push } = useToast();
  const { isAuthenticated } = useAuth();
  const { cart, loading, fetch, updateItem, removeItem } = useCartStore();

  useEffect(() => {
    if (isAuthenticated) fetch();
  }, [isAuthenticated, fetch]);

  if (!isAuthenticated) {
    return (
      <div className="empty-state">
        <h3>Sign in to view your cart</h3>
        <p style={{ marginBottom: 20 }}>Your cart is tied to your account.</p>
        <Link to="/login?next=/cart" className="btn btn-primary">
          Sign in
        </Link>
      </div>
    );
  }

  if (loading && !cart) {
    return (
      <div className="container" style={{ padding: "60px 0" }}>
        <div className="skeleton" style={{ height: 90, marginBottom: 14 }} />
        <div className="skeleton" style={{ height: 90, marginBottom: 14 }} />
      </div>
    );
  }

  if (!cart || cart.items.length === 0) {
    return (
      <div className="empty-state">
        <h3>Your cart is empty</h3>
        <p style={{ marginBottom: 20 }}>Find something you'll love.</p>
        <Link to="/browse" className="btn btn-primary">
          Browse products
        </Link>
      </div>
    );
  }

  async function handleUpdate(productId: string, quantity: number) {
    try {
      await updateItem(productId, quantity);
    } catch (e) {
      push(e instanceof Error ? e.message : "Could not update quantity", "error");
    }
  }

  async function handleRemove(productId: string, title: string) {
    await removeItem(productId);
    push(`Removed ${title}`, "info");
  }

  return (
    <div className="container cart-page">
      <h1 className="section-title">Your cart</h1>
      <div className="cart-layout">
        <div className="cart-items">
          {cart.items.map((item) => (
            <motion.div
              key={item.product_id}
              layout
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="cart-item glass"
            >
              <Link to={`/product/${item.slug}`} className="cart-item-media">
                {item.thumbnail_url && <img src={item.thumbnail_url} alt={item.title} />}
              </Link>
              <div className="cart-item-info">
                <Link to={`/product/${item.slug}`} className="cart-item-title">
                  {item.title}
                </Link>
                <span className="cart-item-unit">{formatPrice(item.unit_price_cents)} each</span>
              </div>
              <div className="qty-stepper">
                <button onClick={() => handleUpdate(item.product_id, Math.max(1, item.quantity - 1))}>−</button>
                <span>{item.quantity}</span>
                <button onClick={() => handleUpdate(item.product_id, item.quantity + 1)}>+</button>
              </div>
              <span className="cart-item-total">{formatPrice(item.line_total_cents)}</span>
              <button className="icon-btn" onClick={() => handleRemove(item.product_id, item.title)} aria-label="Remove">
                ✕
              </button>
            </motion.div>
          ))}
        </div>

        <div className="cart-summary glass">
          <h3>Order summary</h3>
          <div className="row cart-summary-line">
            <span>Subtotal ({cart.item_count} items)</span>
            <span>{formatPrice(cart.subtotal_cents)}</span>
          </div>
          <p className="cart-summary-note">Shipping and tax calculated at checkout.</p>
          <button className="btn btn-primary btn-block" onClick={() => navigate("/checkout")}>
            Checkout
          </button>
        </div>
      </div>
    </div>
  );
}
