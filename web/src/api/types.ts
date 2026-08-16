export interface Category {
  id: string;
  name: string;
  slug: string;
  image_url: string | null;
  children: Category[];
}

export interface ProductImage {
  url: string;
  alt_text: string;
}

export interface ProductSummary {
  id: string;
  title: string;
  slug: string;
  price_cents: number;
  compare_at_price_cents: number | null;
  brand: string;
  avg_rating: number;
  review_count: number;
  thumbnail_url: string | null;
}

export interface ProductDetail extends ProductSummary {
  description: string;
  stock_qty: number;
  images: ProductImage[];
  category_id: string;
}

export interface ProductListResponse {
  items: ProductSummary[];
  total: number;
  page: number;
  page_size: number;
}

export type SortOption = "newest" | "price_asc" | "price_desc" | "rating";

export interface Review {
  id: string;
  rating: number;
  title: string;
  body: string;
  reviewer_name: string;
}

export interface ReviewCreate {
  rating: number;
  title: string;
  body: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Address {
  id: string;
  line1: string;
  line2: string | null;
  city: string;
  state: string;
  postal_code: string;
  country: string;
  is_default: boolean;
}

export type AddressInput = Omit<Address, "id">;

export interface CartItem {
  product_id: string;
  title: string;
  slug: string;
  thumbnail_url: string | null;
  unit_price_cents: number;
  quantity: number;
  line_total_cents: number;
}

export interface Cart {
  items: CartItem[];
  subtotal_cents: number;
  item_count: number;
}

export type OrderStatus = "pending" | "paid" | "shipped" | "delivered" | "cancelled";

export interface OrderItem {
  product_id: string;
  product_title_snapshot: string;
  unit_price_cents_snapshot: number;
  quantity: number;
}

export interface Order {
  id: string;
  status: OrderStatus;
  subtotal_cents: number;
  tax_cents: number;
  shipping_cents: number;
  total_cents: number;
  payment_method: string | null;
  payment_reference: string | null;
  created_at: string;
  shipping_address: Address;
  items: OrderItem[];
}

export interface OrderSummary {
  id: string;
  status: OrderStatus;
  total_cents: number;
  created_at: string;
  item_count: number;
}

export interface CheckoutPreview {
  subtotal_cents: number;
  tax_cents: number;
  shipping_cents: number;
  total_cents: number;
}

export type PaymentMethodType = "card" | "upi" | "wallet" | "cod";

export interface CardPayload {
  number: string;
  expiry_month: number;
  expiry_year: number;
  cvv: string;
  name_on_card: string;
}

export interface UpiPayload {
  vpa: string;
}

export interface WalletPayload {
  provider: string;
}

export interface CheckoutRequest {
  shipping_address_id: string;
  method: PaymentMethodType;
  card?: CardPayload;
  upi?: UpiPayload;
  wallet?: WalletPayload;
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}
