import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <div className="empty-state">
      <h1 className="text-gradient" style={{ fontSize: 72, fontFamily: "var(--font-display)" }}>
        404
      </h1>
      <h3>Page not found</h3>
      <Link to="/" className="btn btn-primary" style={{ marginTop: 20 }}>
        Back home
      </Link>
    </div>
  );
}
