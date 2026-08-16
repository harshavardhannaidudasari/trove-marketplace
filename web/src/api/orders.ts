import { api } from "./client";
import type { Address, AddressInput, CheckoutPreview, CheckoutRequest, Order, OrderSummary } from "./types";

export const usersApi = {
  addresses: () => api.get<Address[]>("/users/me/addresses", true),
  addAddress: (payload: AddressInput) => api.post<Address>("/users/me/addresses", payload, true),
  updateAddress: (id: string, payload: AddressInput) => api.patch<Address>(`/users/me/addresses/${id}`, payload, true),
  deleteAddress: (id: string) => api.delete<void>(`/users/me/addresses/${id}`, true),
};

export const ordersApi = {
  preview: (shipping_address_id: string) =>
    api.get<CheckoutPreview>(`/orders/checkout/preview?shipping_address_id=${shipping_address_id}`, true),

  checkout: (payload: CheckoutRequest) => api.post<Order>("/orders/checkout", payload, true),

  list: () => api.get<OrderSummary[]>("/orders", true),

  get: (id: string) => api.get<Order>(`/orders/${id}`, true),
};
