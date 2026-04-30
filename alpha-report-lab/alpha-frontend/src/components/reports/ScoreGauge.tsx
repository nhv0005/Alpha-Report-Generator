export default function ScoreGauge({ score, size = 96 }: { score: number; size?: number }) {
  const clamped = Math.max(1, Math.min(10, score));
  const pct = (clamped - 1) / 9;
  const stroke = pct < 0.3 ? "#EF4444" : pct < 0.5 ? "#F59E0B" : pct < 0.75 ? "#10B981" : "#34D399";
  const r = size / 2 - 6;
  const c = 2 * Math.PI * r;
  const dash = c * pct;
  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} stroke="#1f2937" strokeWidth={6} fill="none" />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          stroke={stroke}
          strokeWidth={6}
          fill="none"
          strokeDasharray={`${dash} ${c - dash}`}
          strokeLinecap="round"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <div className="text-xl font-semibold text-gray-100">{clamped.toFixed(1)}</div>
        <div className="text-[10px] uppercase tracking-wider text-gray-500">/ 10</div>
      </div>
    </div>
  );
}
