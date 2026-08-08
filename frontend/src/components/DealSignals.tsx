interface Props {
  discountPct: number | null;
  vsOwnHistoryPct: number | null;
  vsStatcanPct: number | null;
  compact?: boolean;
}

interface SignalProps {
  label: string;
  compactLabel: string;
  value: number | null;
  compact?: boolean;
}

function Signal({ label, compactLabel, value, compact }: SignalProps) {
  const text = compact ? compactLabel : label;

  if (value === null) {
    if (compact) return null;
    return (
      <span className="signal signal-empty">
        {text}: <span className="signal-value">—</span>
      </span>
    );
  }

  if (value === 0) {
    if (compact) return null;
    return (
      <span className="signal signal-empty">
        {text}: <span className="signal-value">— 0.0%</span>
      </span>
    );
  }

  const isGood = value > 0;
  return (
    <span className={`signal ${isGood ? "signal-good" : "signal-bad"}`}>
      {text}: <span className="signal-value">{isGood ? "▼" : "▲"} {Math.abs(value).toFixed(1)}%</span>
    </span>
  );
}

export default function DealSignals({ discountPct, vsOwnHistoryPct, vsStatcanPct, compact }: Props) {
  return (
    <div className={`signals-row ${compact ? "signals-row-compact" : ""}`}>
      <Signal label="Sale" compactLabel="Sale" value={discountPct} compact={compact} />
      <Signal label="vs history" compactLabel="Hist" value={vsOwnHistoryPct} compact={compact} />
      <Signal label="vs region" compactLabel="Region" value={vsStatcanPct} compact={compact} />
    </div>
  );
}
