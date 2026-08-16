import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { catalogApi } from "../api/catalog";
import type { Category, ProductSummary, SortOption } from "../api/types";
import { CategoryNav } from "../components/product/CategoryNav";
import { ProductGrid } from "../components/product/ProductGrid";
import { Pagination } from "../components/product/Pagination";
import { useDebounce } from "../hooks/useDebounce";
import "./browse.css";

const PAGE_SIZE = 24;

export function BrowsePage() {
  const [params, setParams] = useSearchParams();
  const [categories, setCategories] = useState<Category[]>([]);
  const [products, setProducts] = useState<ProductSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  const category = params.get("category") ?? undefined;
  const q = params.get("q") ?? "";
  const sort = (params.get("sort") as SortOption) ?? "newest";
  const page = Number(params.get("page") ?? "1");
  const minPrice = params.get("min") ?? "";
  const maxPrice = params.get("max") ?? "";

  const [searchInput, setSearchInput] = useState(q);
  const debouncedSearch = useDebounce(searchInput, 400);

  useEffect(() => {
    catalogApi.categories().then(setCategories);
  }, []);

  useEffect(() => {
    setSearchInput(q);
  }, [q]);

  useEffect(() => {
    if (debouncedSearch === q) return;
    updateParams({ q: debouncedSearch, page: "1" });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedSearch]);

  useEffect(() => {
    setLoading(true);
    catalogApi
      .products({
        category,
        q: q || undefined,
        sort,
        page,
        page_size: PAGE_SIZE,
        min_price: minPrice ? Number(minPrice) : undefined,
        max_price: maxPrice ? Number(maxPrice) : undefined,
      })
      .then((res) => {
        setProducts(res.items);
        setTotal(res.total);
        setLoading(false);
      });
  }, [category, q, sort, page, minPrice, maxPrice]);

  function updateParams(patch: Record<string, string>) {
    const next = new URLSearchParams(params);
    for (const [k, v] of Object.entries(patch)) {
      if (v) next.set(k, v);
      else next.delete(k);
    }
    setParams(next, { replace: true });
  }

  const activeCategory = findCategory(categories, category);
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="container browse-page">
      <div className="browse-layout">
        <CategoryNav categories={categories} activeSlug={category} />

        <div>
          <div className="row" style={{ justifyContent: "space-between", marginBottom: 8 }}>
            <h1 className="browse-heading">{activeCategory?.name ?? (q ? `Results for "${q}"` : "All products")}</h1>
          </div>

          <div className="filter-bar">
            <input
              className="input"
              style={{ maxWidth: 220 }}
              placeholder="Min price"
              type="number"
              value={minPrice}
              onChange={(e) => updateParams({ min: e.target.value, page: "1" })}
            />
            <input
              className="input"
              style={{ maxWidth: 220 }}
              placeholder="Max price"
              type="number"
              value={maxPrice}
              onChange={(e) => updateParams({ max: e.target.value, page: "1" })}
            />
            <select className="input" style={{ maxWidth: 200 }} value={sort} onChange={(e) => updateParams({ sort: e.target.value, page: "1" })}>
              <option value="newest">Newest</option>
              <option value="price_asc">Price: low to high</option>
              <option value="price_desc">Price: high to low</option>
              <option value="rating">Top rated</option>
            </select>
            <span className="results-count">{total} results</span>
          </div>

          <ProductGrid products={products} loading={loading} />
          <Pagination page={page} totalPages={totalPages} onChange={(p) => updateParams({ page: String(p) })} />
        </div>
      </div>
    </div>
  );
}

function findCategory(categories: Category[], slug?: string): Category | undefined {
  if (!slug) return undefined;
  for (const cat of categories) {
    if (cat.slug === slug) return cat;
    const child = cat.children.find((c) => c.slug === slug);
    if (child) return child;
  }
  return undefined;
}
