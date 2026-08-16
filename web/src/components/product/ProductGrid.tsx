import type { ProductSummary } from "../../api/types";
import { ProductCard } from "./ProductCard";
import "./product-list.css";

export function ProductGrid({ products, loading }: { products: ProductSummary[]; loading?: boolean }) {
  if (loading) {
    return (
      <div className="product-grid">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="skeleton product-card-skeleton" />
        ))}
      </div>
    );
  }

  if (products.length === 0) {
    return (
      <div className="empty-state">
        <h3>No products found</h3>
        <p>Try a different search term or clear your filters.</p>
      </div>
    );
  }

  return (
    <div className="product-grid">
      {products.map((p, i) => (
        <ProductCard key={p.id} product={p} index={i} />
      ))}
    </div>
  );
}
