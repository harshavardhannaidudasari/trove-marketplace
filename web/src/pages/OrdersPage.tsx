import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ordersApi } from "../api/orders";
import type { OrderSummary } from "../api/types";
import { formatPrice } from "../api/client";
import { useAuth } from "../hooks/useAuth";
import "./orders.css";

const STATUS_LABEL: Record<string, string> = {
  pending: "Pending",
  paid: "Paid",
  shipped: "Shipped",
  delivered: "Delivered",
  cancelled: "Cancelled",
};

export function OrdersPage() {
  const { isAuthenticated } = useAuth();
  const [orders, setOrders] = useState<OrderSummary[] | null>(null);

  useEffect(() => {
    if (isAuthenticated) ordersApi.list().then(setOrders);
  }, [isAuthenticated]);

  if (!isAuthenticated) {
    return (
      <div className="empty-state">
        <h3>Sign in to view your orders</h3>
        <Link to="/login?next=/orders" className="btn btn-primary" style={{ marginTop: 16 }}>
          Sign in
        </Link>
      </div>
    );
  }

  if (orders === null) {
    return (
      <div className="container" style={{ padding: "60px 0" }}>
        <div className="skeleton" style={{ height: 70, marginBottom: 12 }} />
        <div className="skeleton" style={{ height: 70 }} />
      </div>
    );
  }

  if (orders.length === 0) {
    return (
      <div className="empty-state">
        <h3>No orders yet</h3>
        <Link to="/browse" className="btn btn-primary" style={{ marginTop: 16 }}>
          Start shopping
        </Link>
      </div>
    );
  }

  return (
    <div className="container orders-page">
      <h1 className="section-title">Order history</h1>
      <div className="orders-list">
        {orders.map((o) => (
          <Link key={o.id} to={`/orders/${o.id}`} className="order-row glass">
            <div>
              <span className="order-row-id">#{o.id.slice(0, 8)}</span>
              <span className="order-row-date">{new Date(o.created_at).toLocaleDateString(undefined, { dateStyle: "medium" })}</span>
            </div>
            <span className="badge badge-success">{STATUS_LABEL[o.status] ?? o.status}</span>
            <span>{o.item_count} items</span>
            <strong>{formatPrice(o.total_cents)}</strong>
          </Link>
        ))}
      </div>
    </div>
  );
}
