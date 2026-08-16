import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { catalogApi } from "../api/catalog";
import type { ProductDetail, Review } from "../api/types";
import { formatPrice } from "../api/client";
import { ApiError } from "../api/types";
import { StarRating } from "../components/ui/StarRating";
import { ReviewForm, ReviewList } from "../components/product/Reviews";
import { useCartStore } from "../store/cartStore";
import { useAuth } from "../hooks/useAuth";
import { useToast } from "../components/ui/Toast";
import "./product-detail.css";

export function ProductPage() {
  const { slug = "" } = useParams();
  const navigate = useNavigate();
  const { push } = useToast();
  const { isAuthenticated } = useAuth();
  const addItem = useCartStore((s) => s.addItem);

  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [activeImage, setActiveImage] = useState(0);
  const [qty, setQty] = useState(1);
  const [adding, setAdding] = useState(false);
  const [submittingReview, setSubmittingReview] = useState(false);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    setProduct(null);
    setActiveImage(0);
    setQty(1);
    catalogApi
      .product(slug)
      .then(setProduct)
      .catch((e) => {
        if (e instanceof ApiError && e.status === 404) setNotFound(true);
      });
    catalogApi.reviews(slug).then(setReviews);
  }, [slug]);

  async function handleAddToCart() {
    if (!isAuthenticated) {
      push("Sign in to add items to your cart", "info");
      navigate(`/login?next=/product/${slug}`);
      return;
    }
    if (!product) return;
    setAdding(true);
    try {
      await addItem(product.id, qty);
      push(`Added ${qty} × ${product.title} to cart`, "success");
    } catch (e) {
      push(e instanceof Error ? e.message : "Could not add to cart", "error");
    } finally {
      setAdding(false);
    }
  }

  async function handleReview(rating: number, title: string, body: string) {
    setSubmittingReview(true);
    try {
      const review = await catalogApi.addReview(slug, { rating, title, body });
      setReviews((prev) => [review, ...prev]);
      push("Thanks for your review!", "success");
      setProduct((p) => p && { ...p, review_count: p.review_count + 1 });
    } catch (e) {
      push(e instanceof Error ? e.message : "Could not submit review", "error");
    } finally {
      setSubmittingReview(false);
    }
  }

  if (notFound) {
    return (
      <div className="empty-state">
        <h3>Product not found</h3>
        <p>It may have been removed or the link is incorrect.</p>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="container product-detail">
        <div className="product-detail-layout">
          <div className="skeleton" style={{ aspectRatio: "1/1", borderRadius: "var(--radius-lg)" }} />
          <div className="stack gap-2">
            <div className="skeleton" style={{ height: 32, width: "70%" }} />
            <div className="skeleton" style={{ height: 20, width: "40%" }} />
            <div className="skeleton" style={{ height: 120 }} />
          </div>
        </div>
      </div>
    );
  }

  const images = product.images.length > 0 ? product.images : [{ url: product.thumbnail_url ?? "", alt_text: product.title }];
  const discount =
    product.compare_at_price_cents && product.compare_at_price_cents > product.price_cents
      ? Math.round((1 - product.price_cents / product.compare_at_price_cents) * 100)
      : null;

  return (
    <div className="container product-detail">
      <div className="product-detail-layout">
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="product-gallery">
          <div className="product-gallery-main glass">
            <img src={images[activeImage]?.url} alt={images[activeImage]?.alt_text ?? product.title} />
          </div>
          {images.length > 1 && (
            <div className="product-gallery-thumbs">
              {images.map((img, i) => (
                <button
                  key={i}
                  className={`product-gallery-thumb ${i === activeImage ? "active" : ""}`}
                  onClick={() => setActiveImage(i)}
                >
                  <img src={img.url} alt="" />
                </button>
              ))}
            </div>
          )}
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <span className="eyebrow">{product.brand}</span>
          <h1 className="product-title">{product.title}</h1>
          <div className="row gap-1" style={{ marginTop: 10 }}>
            <StarRating value={product.avg_rating} />
            <span className="product-review-count">
              {product.avg_rating.toFixed(1)} · {product.review_count} reviews
            </span>
          </div>

          <div className="row gap-2 product-price-row">
            <span className="product-price">{formatPrice(product.price_cents)}</span>
            {product.compare_at_price_cents && (
              <>
                <span className="price-was" style={{ fontSize: 16 }}>{formatPrice(product.compare_at_price_cents)}</span>
                {discount && <span className="badge badge-danger">Save {discount}%</span>}
              </>
            )}
          </div>

          <p className="product-description">{product.description}</p>

          <div className="row gap-1" style={{ margin: "8px 0 20px" }}>
            {product.stock_qty > 0 ? (
              <span className="badge badge-success">In stock ({product.stock_qty} left)</span>
            ) : (
              <span className="badge badge-danger">Out of stock</span>
            )}
          </div>

          <div className="row gap-2 product-add-row">
            <div className="qty-stepper">
              <button onClick={() => setQty((q) => Math.max(1, q - 1))}>−</button>
              <span>{qty}</span>
              <button onClick={() => setQty((q) => Math.min(product.stock_qty, q + 1))}>+</button>
            </div>
            <button className="btn btn-primary" disabled={adding || product.stock_qty === 0} onClick={handleAddToCart}>
              {adding ? <span className="spinner" /> : "Add to cart"}
            </button>
          </div>
        </motion.div>
      </div>

      <section className="product-reviews-section">
        <h2 className="section-title">Reviews</h2>
        <div className="reviews-layout">
          <ReviewList reviews={reviews} />
          {isAuthenticated ? (
            <ReviewForm onSubmit={handleReview} submitting={submittingReview} />
          ) : (
            <div className="glass" style={{ padding: 24, height: "fit-content" }}>
              <p style={{ color: "var(--text-dim)", marginBottom: 14 }}>Sign in to write a review.</p>
              <button className="btn btn-outline" onClick={() => navigate(`/login?next=/product/${slug}`)}>
                Sign in
              </button>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
