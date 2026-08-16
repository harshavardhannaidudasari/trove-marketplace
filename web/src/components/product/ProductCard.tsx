import { useRef, useState, type MouseEvent as ReactMouseEvent } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import type { ProductSummary } from "../../api/types";
import { formatPrice } from "../../api/client";
import { StarRating } from "../ui/StarRating";
import "./product-card.css";

export function ProductCard({ product, index = 0 }: { product: ProductSummary; index?: number }) {
  const ref = useRef<HTMLAnchorElement>(null);
  const [tilt, setTilt] = useState({ rx: 0, ry: 0 });

  function onMove(e: ReactMouseEvent<HTMLAnchorElement>) {
    const el = ref.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const px = (e.clientX - rect.left) / rect.width - 0.5;
    const py = (e.clientY - rect.top) / rect.height - 0.5;
    setTilt({ rx: py * -8, ry: px * 10 });
  }

  function onLeave() {
    setTilt({ rx: 0, ry: 0 });
  }

  const discount =
    product.compare_at_price_cents && product.compare_at_price_cents > product.price_cents
      ? Math.round((1 - product.price_cents / product.compare_at_price_cents) * 100)
      : null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-40px" }}
      transition={{ duration: 0.4, delay: Math.min(index * 0.04, 0.3) }}
    >
      <Link
        to={`/product/${product.slug}`}
        className="product-card"
        ref={ref}
        onMouseMove={onMove}
        onMouseLeave={onLeave}
        style={{ transform: `perspective(800px) rotateX(${tilt.rx}deg) rotateY(${tilt.ry}deg)` }}
      >
        <div className="product-card-media">
          {product.thumbnail_url && <img src={product.thumbnail_url} alt={product.title} loading="lazy" />}
          {discount && <span className="badge badge-danger product-card-discount">-{discount}%</span>}
        </div>
        <div className="product-card-body">
          <span className="product-card-brand">{product.brand}</span>
          <h3 className="product-card-title">{product.title}</h3>
          <div className="row gap-1">
            <StarRating value={product.avg_rating} size={13} />
            <span className="product-card-reviews">({product.review_count})</span>
          </div>
          <div className="row gap-1 product-card-price">
            <span className="price-now">{formatPrice(product.price_cents)}</span>
            {product.compare_at_price_cents && (
              <span className="price-was">{formatPrice(product.compare_at_price_cents)}</span>
            )}
          </div>
        </div>
      </Link>
    </motion.div>
  );
}
