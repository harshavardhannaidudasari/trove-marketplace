import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { catalogApi } from "../api/catalog";
import type { Category, ProductSummary } from "../api/types";
import { ProductGrid } from "../components/product/ProductGrid";
import "./home.css";

export function HomePage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [trending, setTrending] = useState<ProductSummary[]>([]);
  const [fresh, setFresh] = useState<ProductSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const [cats, top, newest] = await Promise.all([
        catalogApi.categories(),
        catalogApi.products({ sort: "rating", page_size: 8 }),
        catalogApi.products({ sort: "newest", page_size: 4 }),
      ]);
      setCategories(cats);
      setTrending(top.items);
      setFresh(newest.items);
      setLoading(false);
    })();
  }, []);

  return (
    <div>
      <section className="hero">
        <div className="container hero-inner">
          <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
            <span className="eyebrow">The marketplace, reimagined</span>
            <h1 className="hero-title">
              Shop the <span className="text-gradient">future</span> of
              <br /> everyday things.
            </h1>
            <p className="hero-sub">
              200+ curated products, real-time search, and checkout that just works. Trove is a full-stack demo
              marketplace built to feel like the real thing.
            </p>
            <div className="row gap-2 hero-cta">
              <Link to="/browse" className="btn btn-primary">
                Start shopping
              </Link>
              <Link to="/browse?sort=rating" className="btn btn-outline">
                Top rated
              </Link>
            </div>
            <div className="row gap-3 hero-stats">
              <div>
                <strong>200+</strong>
                <span>products</span>
              </div>
              <div>
                <strong>{categories.length || 10}</strong>
                <span>categories</span>
              </div>
              <div>
                <strong>4.6</strong>
                <span>avg. rating</span>
              </div>
            </div>
          </motion.div>

          <motion.div
            className="hero-visual"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.7, delay: 0.15 }}
          >
            <div className="hero-orb" />
            {trending.slice(0, 3).map((p, i) => (
              <motion.img
                key={p.id}
                src={p.thumbnail_url ?? undefined}
                alt=""
                className={`hero-float hero-float-${i}`}
                animate={{ y: [0, -16, 0] }}
                transition={{ duration: 4 + i, repeat: Infinity, ease: "easeInOut" }}
              />
            ))}
          </motion.div>
        </div>
      </section>

      <section className="container section">
        <h2 className="section-title">Shop by category</h2>
        <div className="category-tiles">
          {categories.slice(0, 6).map((cat, i) => (
            <motion.div
              key={cat.id}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.05 }}
            >
              <Link to={`/browse?category=${cat.slug}`} className="category-tile glass">
                <span className="category-tile-name">{cat.name}</span>
                <span className="category-tile-count">{cat.children.length} subcategories</span>
              </Link>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="container section">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <h2 className="section-title">Trending now</h2>
          <Link to="/browse?sort=rating" className="navbar-link">
            View all →
          </Link>
        </div>
        <ProductGrid products={trending} loading={loading} />
      </section>

      <section className="container section">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <h2 className="section-title">Just landed</h2>
          <Link to="/browse?sort=newest" className="navbar-link">
            View all →
          </Link>
        </div>
        <ProductGrid products={fresh} loading={loading} />
      </section>
    </div>
  );
}
