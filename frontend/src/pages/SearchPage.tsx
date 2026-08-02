import { useEffect, useState, type FormEvent } from "react";
import { useSearchParams } from "react-router-dom";
import { searchProducts, type ProductResult } from "../api";
import ProductCard from "../components/ProductCard";
import CategoryChips from "../components/CategoryChips";

export default function SearchPage() {
  const [params, setParams] = useSearchParams();
  const [q, setQ] = useState(params.get("q") ?? "");
  const [results, setResults] = useState<ProductResult[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runSearch(term: string) {
    if (!term.trim()) return;
    setLoading(true);
    setError(null);
    try {
      setResults(await searchProducts(term.trim()));
    } catch {
      setError("Search failed. Try again.");
    } finally {
      setLoading(false);
    }
  }

  // supports arriving here via a category chip link (?q=...), not just manual typing
  useEffect(() => {
    const urlQ = params.get("q");
    if (urlQ) {
      setQ(urlQ);
      runSearch(urlQ);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params]);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setParams({ q });
    runSearch(q);
  }

  return (
    <div className="page">
      <h1>Search groceries</h1>
      <form onSubmit={handleSubmit} className="search-form">
        <input
          type="search"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search e.g. milk, bread, coffee..."
          autoFocus
        />
        <button type="submit" disabled={loading}>
          {loading ? "..." : "Search"}
        </button>
      </form>

      <CategoryChips />

      {error && <p className="error">{error}</p>}
      {results !== null && results.length === 0 && <p className="muted">No results.</p>}

      <div className="product-grid">
        {results?.map((product, idx) => {
          const cheapest = product.offers[0];
          const moreCount = product.offers.length - 1;
          return (
            <div key={idx} className="product-tile-wrap">
              <ProductCard
                name={product.name}
                merchant={cheapest.merchant}
                currentPrice={cheapest.current_price}
                originalPrice={cheapest.original_price}
                imageUrl={cheapest.image_url}
                discountPct={cheapest.discount_pct}
                vsOwnHistoryPct={cheapest.vs_own_history_pct}
                vsStatcanPct={cheapest.vs_statcan_pct}
                linkTo={
                  product.group_id != null
                    ? `/item/group/${product.group_id}`
                    : `/item/item/${cheapest.item_id}`
                }
              />
              {moreCount > 0 && (
                <div className="more-stores">
                  +{moreCount} more store{moreCount > 1 ? "s" : ""}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
