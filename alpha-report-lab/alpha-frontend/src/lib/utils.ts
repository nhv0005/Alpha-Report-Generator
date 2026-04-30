import { format, parseISO } from "date-fns";

export function formatCurrency(value: number | undefined | null): string {
  if (value === undefined || value === null || isNaN(value as number)) return "-";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(value as number);
}

export function formatLargeNumber(value: number | undefined | null): string {
  if (value === undefined || value === null || isNaN(value as number)) return "-";
  const abs = Math.abs(value as number);
  if (abs >= 1e12) return `$${((value as number) / 1e12).toFixed(2)}T`;
  if (abs >= 1e9) return `$${((value as number) / 1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `$${((value as number) / 1e6).toFixed(2)}M`;
  if (abs >= 1e3) return `$${((value as number) / 1e3).toFixed(2)}K`;
  return `$${(value as number).toFixed(2)}`;
}

export function formatPercentage(value: number | undefined | null): string {
  if (value === undefined || value === null || isNaN(value as number)) return "-";
  const sign = (value as number) > 0 ? "+" : "";
  return `${sign}${(value as number).toFixed(2)}%`;
}

export function percentageClass(value: number | undefined | null): string {
  if (value === undefined || value === null) return "text-gray-400";
  if ((value as number) > 0) return "text-alpha-green";
  if ((value as number) < 0) return "text-alpha-red";
  return "text-gray-400";
}

export function formatDate(date: string | Date | undefined | null): string {
  if (!date) return "-";
  try {
    const d = typeof date === "string" ? parseISO(date) : date;
    return format(d, "MMM d, yyyy");
  } catch {
    return String(date);
  }
}

export function formatDateTime(date: string | Date | undefined | null): string {
  if (!date) return "-";
  try {
    const d = typeof date === "string" ? parseISO(date) : date;
    return format(d, "MMM d, yyyy HH:mm");
  } catch {
    return String(date);
  }
}

export function getRecommendationColor(rec: string): string {
  switch (rec) {
    case "STRONG_BUY":
      return "bg-emerald-500/20 text-emerald-300 border-emerald-500/40";
    case "BUY":
      return "bg-green-500/15 text-green-300 border-green-500/30";
    case "HOLD":
      return "bg-yellow-500/15 text-yellow-300 border-yellow-500/30";
    case "SELL":
      return "bg-orange-500/15 text-orange-300 border-orange-500/30";
    case "STRONG_SELL":
      return "bg-red-500/20 text-red-300 border-red-500/40";
    default:
      return "bg-gray-700 text-gray-300 border-gray-600";
  }
}

export function getRiskColor(risk: string): string {
  switch (risk) {
    case "LOW":
      return "bg-green-500/15 text-green-300 border-green-500/30";
    case "MEDIUM":
      return "bg-yellow-500/15 text-yellow-300 border-yellow-500/30";
    case "HIGH":
      return "bg-orange-500/15 text-orange-300 border-orange-500/30";
    case "VERY_HIGH":
      return "bg-red-500/20 text-red-300 border-red-500/40";
    default:
      return "bg-gray-700 text-gray-300 border-gray-600";
  }
}

export function cls(...parts: (string | false | null | undefined)[]): string {
  return parts.filter(Boolean).join(" ");
}
