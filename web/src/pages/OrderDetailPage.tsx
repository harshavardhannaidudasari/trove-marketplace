import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { ordersApi } from "../api/orders";
import type { Order } from "../api/types";
import { formatPrice } from "../api/client";
import "./orders.css";

export function OrderDetailPage() {
  const { id = "" } = useParams();
  const [order, setOrder] = useState<Order | null>(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    ordersApi.get(id).catch(() => setNotFound(true)).then((o) => o && setOrder(o));
  }, [id]);

  if (notFound) {
    return (
      <div className="empty-state">
        <h3>Order not found</h3>
        <Link to="/orders" className="btn btn-primary" style={{ marginTop: 16 }}>
          Back to orders
        </Link>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="container" style={{ padding: "60px 0" }}>
        <div className="skeleton" style={{ height: 200 }} />
      </div>
    );
  }

  return (
    <div className="container order-detail">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
        <div className="row" style={{ justifyContent: "space-between", marginBottom: 24 }}>
          <div>
            <span className="eyebrow">Order #{order.id.slice(0, 8)}</span>
            <h1 className="section-title" style={{ marginBottom: 0 }}>
              Placed {new Date(order.created_at).toLocaleDateString(undefined, { dateStyle: "long" })}
            </h1>
          </div>
          <span className="badge badge-success" style={{ fontSize: 13, padding: "8px 16px" }}>
            {order.status}
          </span>
        </div>

        <div className="order-detail-layout">
          <div className="glass order-items-card">
            {order.items.map((item) => (
              <div key={item.product_id} className="row order-item-row">
                <span>
                  {item.product_title_snapshot} × {item.quantity}
                </span>
                <span>{formatPrice(item.unit_price_cents_snapshot * item.quantity)}</span>
              </div>
            ))}
          </div>

          <div className="glass order-summary-card">
            <h3>Summary</h3>
            <div className="row cart-summary-line">
              <span>Subtotal</span>
              <span>{formatPrice(order.subtotal_cents)}</span>
            </div>
            <div className="row cart-summary-line">
              <span>Shipping</span>
              <span>{order.shipping_cents === 0 ? "Free" : formatPrice(order.shipping_cents)}</span>
            </div>
            <div className="row cart-summary-line">
              <span>Tax</span>
              <span>{formatPrice(order.tax_cents)}</span>
            </div>
            <div className="row cart-summary-line" style={{ fontWeight: 700, marginTop: 8 }}>
              <span>Total</span>
              <span>{formatPrice(order.total_cents)}</span>
            </div>

            <h3 style={{ marginTop: 24 }}>Shipping to</h3>
            <p className="order-address">
              {order.shipping_address.line1}
              {order.shipping_address.line2 ? `, ${order.shipping_address.line2}` : ""}
              <br />
              {order.shipping_address.city}, {order.shipping_address.state} {order.shipping_address.postal_code}
              <br />
              {order.shipping_address.country}
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
