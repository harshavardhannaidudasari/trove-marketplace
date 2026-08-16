import { api } from "./client";
import type { Category, ProductDetail, ProductListResponse, Review, ReviewCreate, SortOption } from "./types";

export interface ProductQuery {
  category?: string;
  q?: string;
  min_price?: number;
  max_price?: number;
  sort?: SortOption;
  page?: number;
  page_size?: number;
}

function toQueryString(query: ProductQuery): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== "") params.set(key, String(value));
  }
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export const catalogApi = {
  categories: () => api.get<Category[]>("/categories"),

  products: (query: ProductQuery = {}) => api.get<ProductListResponse>(`/products${toQueryString(query)}`),

  product: (slug: string) => api.get<ProductDetail>(`/products/${slug}`),

  reviews: (slug: string) => api.get<Review[]>(`/products/${slug}/reviews`),

  addReview: (slug: string, payload: ReviewCreate) => api.post<Review>(`/products/${slug}/reviews`, payload, true),
};
