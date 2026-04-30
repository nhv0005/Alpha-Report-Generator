"use client";

import { useEffect, useRef, useState } from "react";
import { fetchProgress, generateReport } from "@/lib/api";
import type { GenerateRequest, GenerationProgress } from "@/lib/types";

export function useGenerateReport() {
  const [reportId, setReportId] = useState<string | null>(null);
  const [progress, setProgress] = useState<GenerationProgress | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const cancelRef = useRef(false);

  const start = async (req: GenerateRequest) => {
    setError(null);
    setLoading(true);
    cancelRef.current = false;
    try {
      const res = await generateReport(req);
      setReportId(res.report_id);
      poll(res.report_id);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const poll = async (id: string) => {
    while (!cancelRef.current) {
      try {
        const p = await fetchProgress(id);
        setProgress(p);
        if (p.status === "complete" || p.status === "error") return;
      } catch (e: any) {
        setError(e.message);
        return;
      }
      await new Promise((r) => setTimeout(r, 2000));
    }
  };

  useEffect(() => () => {
    cancelRef.current = true;
  }, []);

  return { reportId, progress, error, loading, start };
}
