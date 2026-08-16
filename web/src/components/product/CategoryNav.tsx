import { Link } from "react-router-dom";
import type { Category } from "../../api/types";

export function CategoryNav({ categories, activeSlug }: { categories: Category[]; activeSlug?: string }) {
  return (
    <nav className="category-nav glass">
      <Link to="/browse" className={`category-nav-item category-nav-all ${!activeSlug ? "active" : ""}`}>
        All products
      </Link>
      {categories.map((cat) => (
        <div key={cat.id} className="category-nav-group">
          <Link
            to={`/browse?category=${cat.slug}`}
            className={`category-nav-item ${activeSlug === cat.slug ? "active" : ""}`}
          >
            {cat.name}
          </Link>
          {cat.children.length > 0 && (
            <div className="category-nav-children">
              {cat.children.map((child) => (
                <Link
                  key={child.id}
                  to={`/browse?category=${child.slug}`}
                  className={`category-nav-item category-nav-child ${activeSlug === child.slug ? "active" : ""}`}
                >
                  {child.name}
                </Link>
              ))}
            </div>
          )}
        </div>
      ))}
    </nav>
  );
}
