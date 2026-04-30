"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { PlusCircle } from "lucide-react";
import { fetchReports } from "@/lib/api";
import type { AlphaReport } from "@/lib/types";
import ReportCard from "@/components/reports/ReportCard";
import { Card, CardTitle, CardValue } from "@/components/ui/Card";
import Skeleton from "@/components/ui/Skeleton";

export default function DashboardPage() {
  const [reports, setReports] = useState<AlphaReport[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchReports()
      .then((data) => { if (!cancelled) setReports(data); })
      .catch((e) => {
        if (!cancelled) {
          setError(e.message);
          // Render zeros instead of infinite skeletons so the UI is usable
          // even when the engine is slow or unreachable.
          setReports([]);
        }
      });
    return () => { cancelled = true; };
  }, []);

  const completed = reports?.filter((r) => r.status === "complete") || [];
  const avgConviction =
    completed.length > 0
      ? completed.reduce((s, r) => s + (r.conviction_score || 0), 0) / completed.length
      : 0;
  const totalTokens = completed.reduce((s, r) => s + (r.metadata?.total_tokens || 0), 0);
  const sectorCounts: Record<string, number> = {};
  completed.forEach((r) => {
    if (r.sector) sectorCounts[r.sector] = (sectorCounts[r.sector] || 0) + 1;
  });
  const topSector = Object.entries(sectorCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || "-";

  const recent = [...(reports || [])]
    .sort((a, b) => (b.generated_at || "").localeCompare(a.generated_at || ""))
    .slice(0, 5);

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Alpha Report Lab</h1>
          <p className="text-gray-500 mt-1">
            AI-Powered Investment Research - Dynatrace Instrumentation Demo
          </p>
        </div>
        <Link
          href="/generate"
          className="flex items-center gap-2 px-4 py-2 bg-alpha-blue hover:bg-alpha-blue/90 rounded-lg text-white font-medium"
        >
          <PlusCircle size={16} /> Generate New Report
        </Link>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
        <Card>
          <CardTitle>Reports Generated</CardTitle>
          <CardValue>{reports?.length ?? <Skeleton className="h-7 w-12" />}</CardValue>
        </Card>
        <Card>
          <CardTitle>Avg Conviction</CardTitle>
          <CardValue>{reports ? avgConviction.toFixed(1) : <Skeleton className="h-7 w-12" />}</CardValue>
        </Card>
        <Card>
          <CardTitle>Top Sector</CardTitle>
          <CardValue>{reports ? topSector : <Skeleton className="h-7 w-20" />}</CardValue>
        </Card>
        <Card>
          <CardTitle>Total Tokens</CardTitle>
          <CardValue>{reports ? totalTokens.toLocaleString() : <Skeleton className="h-7 w-16" />}</CardValue>
        </Card>
      </div>

      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-100">Recent Reports</h2>
        <Link href="/reports" className="text-sm text-alpha-blue hover:underline">
          View all -&gt;
        </Link>
      </div>

      {error && <div className="text-alpha-red text-sm mb-4">{error}</div>}

      {!reports ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-40" />
          ))}
        </div>
      ) : recent.length === 0 ? (
        <div className="text-center py-12 text-gray-500 border border-dashed border-gray-800 rounded-xl">
          No reports yet.{" "}
          <Link href="/generate" className="text-alpha-blue hover:underline">
            Generate your first report
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {recent.map((r) => (
            <ReportCard key={r.id} report={r} />
          ))}
        </div>
      )}
    </div>
  );
}
