"use client";

import { useEffect, useState } from "react";
import type { AlphaReport } from "@/lib/types";
import { fetchReport } from "@/lib/api";

export function useReport(id: string | null) {
  const [report, setReport] = useState<AlphaReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    fetchReport(id)
      .then((r) => {
        setReport(r);
        setError(null);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  return { report, loading, error };
}
