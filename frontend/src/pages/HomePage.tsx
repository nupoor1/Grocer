import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchBestDeals, type DealObservation } from "../api";
import DealSignals from "../components/DealSignals";

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
      <h1>Best deals right now</h1>

      {error && <p className="error">{error}</p>}
      {!error && deals === null && <p className="muted">Loading...</p>}
      {deals !== null && deals.length === 0 && <p className="muted">No deals found.</p>}

      <ul className="deal-list">
        {deals?.map((d) => (
          <li key={`${d.item_id}-${d.merchant}`}>
            <Link
              className="deal-card"
              to={d.group_id != null ? `/item/group/${d.group_id}` : `/item/item/${d.item_id}`}
              state={{ name: d.item_name }}
            >
              <div className="deal-card-top">
                <span className="deal-name">{d.item_name}</span>
                <span className="deal-price">
                  ${d.current_price.toFixed(2)}
                  {d.original_price != null && d.original_price > d.current_price && (
                    <span className="deal-was"> was ${d.original_price.toFixed(2)}</span>
                  )}
                </span>
              </div>
              <div className="deal-merchant">{d.merchant}</div>
              <DealSignals
                discountPct={d.discount_pct}
                vsOwnHistoryPct={d.vs_own_history_pct}
                vsStatcanPct={d.vs_statcan_pct}
              />
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
