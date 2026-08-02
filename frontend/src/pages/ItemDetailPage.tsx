import { useEffect, useState } from "react";
import { useLocation, useParams } from "react-router-dom";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { fetchHistory, type HistoryPoint } from "../api";
import ProductImage from "../components/ProductImage";

const LINE_COLORS = ["#2563eb", "#dc2626", "#16a34a", "#d97706", "#7c3aed", "#0891b2"];

// Reshape from one-row-per-observation to one-row-per-day, with each merchant as its
// own column, since recharts wants "wide" data to draw one Line per merchant.
function toChartRows(points: HistoryPoint[]) {
  const byDate = new Map<string, Record<string, number>>();
  for (const p of points) {
    const date = p.observed_at.slice(0, 10);
    if (!byDate.has(date)) byDate.set(date, {});
    byDate.get(date)![p.merchant] = p.current_price;
  }
  return [...byDate.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, merchantPrices]) => ({ date, ...merchantPrices }));
}

// The most recent observation per merchant IS the current cross-merchant price
// comparison -- no need for a separate API call, /history already has it.
function currentPricesByMerchant(points: HistoryPoint[]) {
  const latest = new Map<string, HistoryPoint>();
  for (const p of points) {
    const existing = latest.get(p.merchant);
    if (!existing || p.observed_at > existing.observed_at) {
      latest.set(p.merchant, p);
    }
  }
  return [...latest.values()].sort((a, b) => a.current_price - b.current_price);
}

export default function ItemDetailPage() {
  const { type, id } = useParams<{ type: "group" | "item"; id: string }>();
  const location = useLocation();
  const state = location.state as { name?: string; imageUrl?: string } | null;
  const name = state?.name ?? "Price history";
  const imageUrl = state?.imageUrl ?? null;

  const [points, setPoints] = useState<HistoryPoint[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    const params = type === "group" ? { groupId: Number(id) } : { itemId: Number(id) };
    fetchHistory(params)
      .then(setPoints)
      .catch(() => setError("Couldn't load price history."));
  }, [type, id]);

  const merchants = points ? [...new Set(points.map((p) => p.merchant))] : [];
  const rows = points ? toChartRows(points) : [];
  const currentPrices = points ? currentPricesByMerchant(points) : [];

  return (
    <div className="page">
      <div className="detail-header">
        <ProductImage src={imageUrl} alt={name} />
        <h1>{name}</h1>
      </div>

      {error && <p className="error">{error}</p>}
      {!error && points === null && <p className="muted">Loading...</p>}
      {points !== null && rows.length === 0 && <p className="muted">No price history yet.</p>}

      {currentPrices.length > 0 && (
        <div className="compare-card">
          <h2>Compare stores</h2>
          <ul className="compare-list">
            {currentPrices.map((p, i) => (
              <li key={p.merchant} className={i === 0 ? "compare-cheapest" : ""}>
                <span>{p.merchant}</span>
                <span className="compare-price">${p.current_price.toFixed(2)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {rows.length > 0 && (
        <div className="chart-wrap">
          <h2>Price history</h2>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={rows} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" fontSize={12} />
              <YAxis fontSize={12} tickFormatter={(v) => `$${v}`} width={45} />
              <Tooltip formatter={(v: number) => `$${v.toFixed(2)}`} />
              <Legend />
              {merchants.map((m, i) => (
                <Line
                  key={m}
                  type="monotone"
                  dataKey={m}
                  stroke={LINE_COLORS[i % LINE_COLORS.length]}
                  connectNulls
                  dot={{ r: 3 }}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {rows.length === 1 && (
        <p className="muted">
          Only one price snapshot so far — the chart fills in as ingest.py runs over time.
        </p>
      )}
    </div>
  );
}
