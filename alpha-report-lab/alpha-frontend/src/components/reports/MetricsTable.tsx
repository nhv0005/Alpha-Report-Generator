import { formatLargeNumber, formatPercentage, percentageClass } from "@/lib/utils";

type Row = {
  label: string;
  value: string | number;
  isPercent?: boolean;
  isLarge?: boolean;
  goodWhen?: "high" | "low";
};

export default function MetricsTable({ rows }: { rows: Row[] }) {
  return (
    <table className="w-full text-sm">
      <tbody>
        {rows.map((r, i) => {
          let valueDisplay: string;
          let colorClass = "text-gray-200";
          if (r.isPercent && typeof r.value === "number") {
            valueDisplay = formatPercentage(r.value * 100);
            colorClass = percentageClass(r.value);
          } else if (r.isLarge && typeof r.value === "number") {
            valueDisplay = formatLargeNumber(r.value);
          } else {
            valueDisplay = String(r.value);
          }
          return (
            <tr key={i} className="border-b border-gray-800/70 last:border-0">
              <td className="py-2 text-gray-400">{r.label}</td>
              <td className={`py-2 text-right font-medium ${colorClass}`}>{valueDisplay}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
