"use client";

import { useEffect, useMemo, useState } from "react";
import type { AlphaReport, Recommendation, RiskRating } from "@/lib/types";
import { fetchReports } from "@/lib/api";
import ReportCard from "@/components/reports/ReportCard";
import Skeleton from "@/components/ui/Skeleton";

type SortKey = "date" | "conviction" | "upside";
type RecFilter = "ALL" | Recommendation;
type RiskFilter = "ALL" | RiskRating;

export default function ReportsPage() {
  const [reports, setReports] = useState<AlphaReport[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [sort, setSort] = useState<SortKey>("date");
  const [recFilter, setRecFilter] = useState<RecFilter>("ALL");
  const [riskFilter, setRiskFilter] = useState<RiskFilter>("ALL");

  useEffect(() => {
    let cancelled = false;
    fetchReports()
      .then((data) => { if (!cancelled) setReports(data); })
      .catch((e) => {
        if (!cancelled) {
          setError(e.message);
          setReports([]);
        }
      });
    return () => { cancelled = true; };
  }, []);

  const filtered = useMemo(() => {
    if (!reports) return [];
    let list = [...reports];
    if (recFilter !== "ALL") list = list.filter((r) => r.recommendation === recFilter);
    if (riskFilter !== "ALL") list = list.filter((r) => r.risk_rating === riskFilter);
    list.sort((a, b) => {
      if (sort === "date") return (b.generated_at || "").localeCompare(a.generated_at || "");
      if (sort === "conviction") return (b.conviction_score || 0) - (a.conviction_score || 0);
      return (b.upside_percentage || 0) - (a.upside_percentage || 0);
    });
    return list;
  }, [reports, sort, recFilter, riskFilter]);

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-6 flex items-end justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Report History</h1>
          <p className="text-sm text-gray-500 mt-1">{reports?.length ?? 0} reports</p>
        </div>
        <div className="flex gap-2 flex-wrap items-center text-sm">
          <Select label="Sort" value={sort} onChange={(v) => setSort(v as SortKey)}
            options={[["date","Date"],["conviction","Conviction"],["upside","Upside %"]]} />
          <Select label="Rec" value={recFilter} onChange={(v) => setRecFilter(v as RecFilter)}
            options={[["ALL","All"],["STRONG_BUY","Strong Buy"],["BUY","Buy"],["HOLD","Hold"],["SELL","Sell"],["STRONG_SELL","Strong Sell"]]} />
          <Select label="Risk" value={riskFilter} onChange={(v) => setRiskFilter(v as RiskFilter)}
            options={[["ALL","All"],["LOW","Low"],["MEDIUM","Medium"],["HIGH","High"],["VERY_HIGH","Very High"]]} />
        </div>
      </div>

      {error && <div className="text-alpha-red text-sm mb-4">{error}</div>}

      {!reports ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => <Skeleton key={i} className="h-40" />)}
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-12 text-gray-500 border border-dashed border-gray-800 rounded-xl">
          No reports match your filters.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((r) => <ReportCard key={r.id} report={r} />)}
        </div>
      )}
    </div>
  );
}

function Select({
  label, value, onChange, options,
}: { label: string; value: string; onChange: (v: string) => void; options: [string, string][] }) {
  return (
    <label className="flex items-center gap-2 text-gray-400">
      <span className="text-xs uppercase tracking-wider">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="bg-gray-900 border border-gray-700 rounded-md px-2 py-1 text-gray-200 focus:outline-none focus:ring-1 focus:ring-alpha-blue/40"
      >
        {options.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
      </select>
    </label>
  );
}
