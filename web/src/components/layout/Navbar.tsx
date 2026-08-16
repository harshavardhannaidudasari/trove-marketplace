import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useAuth } from "../../hooks/useAuth";
import { useCartStore } from "../../store/cartStore";
import "./navbar.css";

export function Navbar() {
  const navigate = useNavigate();
  const { user, isAuthenticated, logout } = useAuth();
  const cart = useCartStore((s) => s.cart);
  const [q, setQ] = useState("");
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    function onScroll() {
      setScrolled(window.scrollY > 12);
    }
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  function onSearch(e: FormEvent) {
    e.preventDefault();
    navigate(q.trim() ? `/browse?q=${encodeURIComponent(q.trim())}` : "/browse");
  }

  return (
    <header className={`navbar ${scrolled ? "navbar--scrolled" : ""}`}>
      <div className="container navbar-inner">
        <Link to="/" className="brand">
          <span className="brand-mark">T</span>
          <span className="brand-word text-gradient">Trove</span>
        </Link>

        <form className="navbar-search" onSubmit={onSearch}>
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="7" />
            <path d="m21 21-4.3-4.3" />
          </svg>
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search products, brands, categories…"
            aria-label="Search"
          />
        </form>

        <nav className="navbar-actions">
          <Link to="/browse" className="navbar-link">
            Browse
          </Link>

          {isAuthenticated ? (
            <div className="user-menu" onMouseLeave={() => setMenuOpen(false)}>
              <button className="navbar-link user-trigger" onClick={() => setMenuOpen((v) => !v)}>
                Hi, {user?.full_name.split(" ")[0]}
              </button>
              {menuOpen && (
                <motion.div
                  className="user-dropdown glass"
                  initial={{ opacity: 0, y: -8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.15 }}
                >
                  <Link to="/orders" onClick={() => setMenuOpen(false)}>
                    Order history
                  </Link>
                  <button
                    onClick={() => {
                      logout();
                      setMenuOpen(false);
                      navigate("/");
                    }}
                  >
                    Log out
                  </button>
                </motion.div>
              )}
            </div>
          ) : (
            <Link to="/login" className="navbar-link">
              Sign in
            </Link>
          )}

          <Link to="/cart" className="icon-btn cart-btn" aria-label="Cart">
            <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="9" cy="21" r="1" />
              <circle cx="20" cy="21" r="1" />
              <path d="M1 1h4l2.7 13.4a2 2 0 0 0 2 1.6h9.7a2 2 0 0 0 2-1.6L23 6H6" />
            </svg>
            {!!cart?.item_count && (
              <motion.span
                key={cart.item_count}
                initial={{ scale: 0.5 }}
                animate={{ scale: 1 }}
                className="cart-badge"
              >
                {cart.item_count}
              </motion.span>
            )}
          </Link>
        </nav>
      </div>
    </header>
  );
}
