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

export default function ItemDetailPage() {
  const { type, id } = useParams<{ type: "group" | "item"; id: string }>();
  const location = useLocation();
  const name = (location.state as { name?: string } | null)?.name ?? "Price history";

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

  return (
    <div className="page">
      <h1>{name}</h1>

      {error && <p className="error">{error}</p>}
      {!error && points === null && <p className="muted">Loading...</p>}
      {points !== null && rows.length === 0 && <p className="muted">No price history yet.</p>}

      {rows.length > 0 && (
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height={320}>
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
