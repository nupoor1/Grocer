interface Props {
  discountPct: number | null;
  vsOwnHistoryPct: number | null;
  vsStatcanPct: number | null;
}

interface SignalProps {
  label: string;
  value: number | null;
}

// Every signal uses the same convention: positive = currently cheaper (good for the
// buyer), so a single indicator function covers discount/history/regional signals alike.
function Signal({ label, value }: SignalProps) {
  if (value === null) {
    return (
      <span className="signal signal-empty">
        {label}: <span className="signal-value">—</span>
      </span>
    );
  }

  // value === 0 means "exactly at baseline" -- neutral, not a price increase
  if (value === 0) {
    return (
      <span className="signal signal-empty">
        {label}: <span className="signal-value">— 0.0%</span>
      </span>
    );
  }

  const isGood = value > 0;
  return (
    <span className={`signal ${isGood ? "signal-good" : "signal-bad"}`}>
      {label}: <span className="signal-value">{isGood ? "▼" : "▲"} {Math.abs(value).toFixed(1)}%</span>
    </span>
  );
}

export default function DealSignals({ discountPct, vsOwnHistoryPct, vsStatcanPct }: Props) {
  return (
    <div className="signals-row">
      <Signal label="Sale" value={discountPct} />
      <Signal label="vs history" value={vsOwnHistoryPct} />
      <Signal label="vs region" value={vsStatcanPct} />
    </div>
  );
}
