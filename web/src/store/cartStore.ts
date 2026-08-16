import { create } from "zustand";
import { cartApi } from "../api/cart";
import { ApiError } from "../api/types";
import type { Cart } from "../api/types";

interface CartState {
  cart: Cart | null;
  loading: boolean;
  fetch: () => Promise<void>;
  addItem: (productId: string, quantity?: number) => Promise<void>;
  updateItem: (productId: string, quantity: number) => Promise<void>;
  removeItem: (productId: string) => Promise<void>;
  reset: () => void;
}

export const useCartStore = create<CartState>((set) => ({
  cart: null,
  loading: false,

  fetch: async () => {
    set({ loading: true });
    try {
      const cart = await cartApi.get();
      set({ cart, loading: false });
    } catch (e) {
      set({ loading: false });
      if (!(e instanceof ApiError && e.status === 401)) throw e;
    }
  },

  addItem: async (productId, quantity = 1) => {
    const cart = await cartApi.addItem(productId, quantity);
    set({ cart });
  },

  updateItem: async (productId, quantity) => {
    const cart = await cartApi.updateItem(productId, quantity);
    set({ cart });
  },

  removeItem: async (productId) => {
    const cart = await cartApi.removeItem(productId);
    set({ cart });
  },

  reset: () => set({ cart: null }),
}));
