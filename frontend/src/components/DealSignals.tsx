interface Props {
  discountPct: number | null;
  vsOwnHistoryPct: number | null;
  vsStatcanPct: number | null;
  /** Compact mode drops empty signals entirely instead of showing a "—" placeholder,
   * for tight spaces like grid cards -- the full row is for detail-style layouts. */
  compact?: boolean;
}

interface SignalProps {
  label: string;
  value: number | null;
  compact?: boolean;
}

// Every signal uses the same convention: positive = currently cheaper (good for the
// buyer), so a single indicator function covers discount/history/regional signals alike.
function Signal({ label, value, compact }: SignalProps) {
  if (value === null) {
    if (compact) return null;
    return (
      <span className="signal signal-empty">
        {label}: <span className="signal-value">—</span>
      </span>
    );
  }

  // value === 0 means "exactly at baseline" -- neutral, not a price increase
  if (value === 0) {
    if (compact) return null;
    return (
      <span className="signal signal-empty">
        {label}: <span className="signal-value">— 0.0%</span>
      </span>
    );
  }

  const isGood = value > 0;
  return (
    <span className={`signal ${isGood ? "signal-good" : "signal-bad"}`}>
      {!compact && `${label}: `}
      <span className="signal-value">{isGood ? "▼" : "▲"} {Math.abs(value).toFixed(1)}%</span>
    </span>
  );
}

export default function DealSignals({ discountPct, vsOwnHistoryPct, vsStatcanPct, compact }: Props) {
  return (
    <div className={`signals-row ${compact ? "signals-row-compact" : ""}`}>
      <Signal label="Sale" value={discountPct} compact={compact} />
      <Signal label="vs history" value={vsOwnHistoryPct} compact={compact} />
      <Signal label="vs region" value={vsStatcanPct} compact={compact} />
    </div>
  );
}
