import { useEffect, useState } from "react";
import { fetchBestDeals, type DealObservation } from "../api";
import ProductCard from "../components/ProductCard";
import CategoryChips from "../components/CategoryChips";

export default function HomePage() {
  const [deals, setDeals] = useState<DealObservation[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchBestDeals(20)
      .then(setDeals)
      .catch(() => setError("Couldn't load deals right now."));
  }, []);

  return (
    <div className="page">
      <div className="hero">
        <h1>Best deals right now</h1>
        <p className="hero-subtitle">Top price drops across every store we track</p>
      </div>

      <CategoryChips />

      {error && <p className="error">{error}</p>}
      {!error && deals === null && <p className="muted">Loading...</p>}
      {deals !== null && deals.length === 0 && <p className="muted">No deals found.</p>}

      <div className="product-grid">
        {deals?.map((d) => (
          <ProductCard
            key={`${d.item_id}-${d.merchant}`}
            name={d.item_name}
            merchant={d.merchant}
            currentPrice={d.current_price}
            originalPrice={d.original_price}
            imageUrl={d.image_url}
            discountPct={d.discount_pct}
            vsOwnHistoryPct={d.vs_own_history_pct}
            vsStatcanPct={d.vs_statcan_pct}
            linkTo={d.group_id != null ? `/item/group/${d.group_id}` : `/item/item/${d.item_id}`}
          />
        ))}
      </div>
    </div>
  );
}
