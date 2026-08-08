const API_BASE = "/api";

export interface Offer {
  item_id: number;
  merchant: string;
  current_price: number;
  original_price: number | null;
  is_deal: boolean;
  discount_pct: number | null;
  vs_own_history_pct: number | null;
  vs_statcan_pct: number | null;
  composite_score: number | null;
  image_url: string | null;
  price_per_unit: number | null;
  unit_label: string | null;
}

export interface ProductResult {
  name: string;
  grouped: boolean;
  group_id: number | null;
  offers: Offer[];
}

export interface DealObservation {
  item_id: number;
  group_id: number | null;
  item_name: string;
  merchant: string;
  current_price: number;
  original_price: number | null;
  is_deal: boolean;
  discount_pct: number | null;
  vs_own_history_pct: number | null;
  vs_statcan_pct: number | null;
  composite_score: number | null;
  image_url: string | null;
  store_count: number;
  price_per_unit: number | null;
  unit_label: string | null;
}

export interface HistoryPoint {
  merchant: string;
  observed_at: string;
  current_price: number;
}

export interface Category {
  search_term: string;
  item_count: number;
}

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    throw new Error(`${path} failed: ${res.status}`);
  }
  return res.json();
}

export function fetchBestDeals(limit = 20): Promise<DealObservation[]> {
  return getJSON(`/deals?limit=${limit}`);
}

export function searchProducts(q: string): Promise<ProductResult[]> {
  return getJSON(`/search?q=${encodeURIComponent(q)}`);
}

export function fetchHistory(params: { groupId?: number; itemId?: number }): Promise<HistoryPoint[]> {
  const query = params.groupId != null ? `group_id=${params.groupId}` : `item_id=${params.itemId}`;
  return getJSON(`/history?${query}`);
}

export function fetchProduct(params: { groupId?: number; itemId?: number }): Promise<ProductResult> {
  const query = params.groupId != null ? `group_id=${params.groupId}` : `item_id=${params.itemId}`;
  return getJSON(`/product?${query}`);
}

export function fetchCategories(): Promise<Category[]> {
  return getJSON(`/categories`);
}
