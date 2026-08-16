import { Link } from "react-router-dom";
import "./footer.css";

export function Footer() {
  return (
    <footer className="footer">
      <div className="container footer-inner">
        <div className="footer-brand">
          <div className="row gap-1">
            <span className="brand-mark">T</span>
            <span className="brand-word text-gradient">Trove</span>
          </div>
          <p>A demo marketplace. Real backend, real checkout flow (Stripe test mode), zero real money.</p>
        </div>
        <div className="footer-links">
          <div>
            <h4>Shop</h4>
            <Link to="/browse">All products</Link>
            <Link to="/browse?sort=rating">Top rated</Link>
            <Link to="/browse?sort=newest">New arrivals</Link>
          </div>
          <div>
            <h4>Account</h4>
            <Link to="/orders">Order history</Link>
            <Link to="/login">Sign in</Link>
          </div>
        </div>
      </div>
      <div className="footer-bottom">
        <div className="container">© {new Date().getFullYear()} Trove Marketplace — demo project.</div>
      </div>
    </footer>
  );
}
