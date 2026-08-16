import { api } from "./client";
import type { Cart } from "./types";

export const cartApi = {
  get: () => api.get<Cart>("/cart", true),
  addItem: (product_id: string, quantity = 1) => api.post<Cart>("/cart/items", { product_id, quantity }, true),
  updateItem: (product_id: string, quantity: number) => api.patch<Cart>(`/cart/items/${product_id}`, { quantity }, true),
  removeItem: (product_id: string) => api.delete<Cart>(`/cart/items/${product_id}`, true),
  clear: () => api.delete<void>("/cart", true),
};
