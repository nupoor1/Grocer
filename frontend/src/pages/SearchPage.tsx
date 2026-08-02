import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { searchProducts, type ProductResult } from "../api";
import DealSignals from "../components/DealSignals";

export default function SearchPage() {
  const [q, setQ] = useState("");
  const [results, setResults] = useState<ProductResult[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!q.trim()) return;
    setLoading(true);
    setError(null);
    try {
      setResults(await searchProducts(q.trim()));
    } catch {
      setError("Search failed. Try again.");
    } finally {
      setLoading(false);
    }
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

      {error && <p className="error">{error}</p>}
      {results !== null && results.length === 0 && <p className="muted">No results.</p>}

      <ul className="product-list">
        {results?.map((product, idx) => (
          <li key={idx} className="product-card">
            <div className="product-name">{product.name}</div>
            <ul className="offer-list">
              {product.offers.map((offer) => (
                <li key={offer.item_id}>
                  <Link
                    className="offer-row"
                    to={
                      product.group_id != null
                        ? `/item/group/${product.group_id}`
                        : `/item/item/${offer.item_id}`
                    }
                    state={{ name: product.name }}
                  >
                    <div className="offer-top">
                      <span className="offer-merchant">{offer.merchant}</span>
                      <span className="offer-price">
                        ${offer.current_price.toFixed(2)}
                        {offer.original_price != null && offer.original_price > offer.current_price && (
                          <span className="deal-was"> was ${offer.original_price.toFixed(2)}</span>
                        )}
                      </span>
                    </div>
                    <DealSignals
                      discountPct={offer.discount_pct}
                      vsOwnHistoryPct={offer.vs_own_history_pct}
                      vsStatcanPct={offer.vs_statcan_pct}
                    />
                  </Link>
                </li>
              ))}
            </ul>
          </li>
        ))}
      </ul>
    </div>
  );
}
