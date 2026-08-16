import { api } from "./client";
import type { Address, AddressInput, CheckoutIntent, Order, OrderSummary } from "./types";

export const usersApi = {
  addresses: () => api.get<Address[]>("/users/me/addresses", true),
  addAddress: (payload: AddressInput) => api.post<Address>("/users/me/addresses", payload, true),
  updateAddress: (id: string, payload: AddressInput) => api.patch<Address>(`/users/me/addresses/${id}`, payload, true),
  deleteAddress: (id: string) => api.delete<void>(`/users/me/addresses/${id}`, true),
};

export const ordersApi = {
  createIntent: (shipping_address_id: string) =>
    api.post<CheckoutIntent>("/orders/checkout/intent", { shipping_address_id }, true),

  confirm: (payment_intent_id: string, shipping_address_id: string) =>
    api.post<Order>("/orders/checkout/confirm", { payment_intent_id, shipping_address_id }, true),

  list: () => api.get<OrderSummary[]>("/orders", true),

  get: (id: string) => api.get<Order>(`/orders/${id}`, true),
};
