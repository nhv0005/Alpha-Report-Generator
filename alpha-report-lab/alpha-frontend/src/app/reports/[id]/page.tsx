"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import type { AlphaReport } from "@/lib/types";
import { fetchReport } from "@/lib/api";
import ReportViewer from "@/components/reports/ReportViewer";
import Skeleton from "@/components/ui/Skeleton";

export default function ReportDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params?.id;
  const [report, setReport] = useState<AlphaReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    fetchReport(id as string).then(setReport).catch((e) => setError(e.message));
  }, [id]);

  if (error) {
    return (
      <div className="p-8">
        <div className="text-alpha-red">{error}</div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="p-8 space-y-4">
        <Skeleton className="h-24" />
        <Skeleton className="h-40" />
        <Skeleton className="h-40" />
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <ReportViewer report={report} />
    </div>
  );
}
