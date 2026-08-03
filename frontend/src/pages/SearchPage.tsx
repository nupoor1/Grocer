import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { searchProducts, type ProductResult } from "../api";
import ProductCard from "../components/ProductCard";
import CategoryChips from "../components/CategoryChips";
import BestValueBanner from "../components/BestValueBanner";

export default function SearchPage() {
  const [params] = useSearchParams();
  const q = params.get("q") ?? "";
  const [results, setResults] = useState<ProductResult[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!q.trim()) return;
    setLoading(true);
    setError(null);
    searchProducts(q.trim())
      .then(setResults)
      .catch(() => setError("Search failed. Try again."))
      .finally(() => setLoading(false));
  }, [q]);

  return (
    <div className="page">
      <h1>{q ? `Results for "${q}"` : "Search groceries"}</h1>

      <CategoryChips />

      {loading && <p className="muted">Searching...</p>}
      {error && <p className="error">{error}</p>}
      {!loading && results !== null && results.length === 0 && <p className="muted">No results.</p>}

      {results !== null && results.length > 0 && <BestValueBanner results={results} query={q} />}

      <div className="product-grid">
        {results?.map((product, idx) => {
          const cheapest = product.offers[0];
          return (
            <ProductCard
              key={idx}
              name={product.name}
              merchant={cheapest.merchant}
              currentPrice={cheapest.current_price}
              originalPrice={cheapest.original_price}
              imageUrl={cheapest.image_url}
              discountPct={cheapest.discount_pct}
              vsOwnHistoryPct={cheapest.vs_own_history_pct}
              vsStatcanPct={cheapest.vs_statcan_pct}
              storeCount={product.offers.length}
              linkTo={
                product.group_id != null
                  ? `/item/group/${product.group_id}`
                  : `/item/item/${cheapest.item_id}`
              }
            />
          );
        })}
      </div>
    </div>
  );
}
