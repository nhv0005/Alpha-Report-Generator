"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, Circle, Loader2, AlertCircle, StopCircle, Ban } from "lucide-react";
import { fetchProgress, cancelReport } from "@/lib/api";
import type { GenerationProgress } from "@/lib/types";

const STEPS = [
  { key: "pending", label: "Queued" },
  { key: "researching", label: "Research" },
  { key: "analyzing", label: "Analysis" },
  { key: "assessing_risk", label: "Risk" },
  { key: "writing", label: "Writing" },
  { key: "complete", label: "Complete" },
];

function indexOf(status: string): number {
  return STEPS.findIndex((s) => s.key === status);
}

export default function ProgressTracker({
  reportId,
  onComplete,
}: {
  reportId: string;
  onComplete: () => void;
}) {
  const [progress, setProgress] = useState<GenerationProgress | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cancelling, setCancelling] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function poll() {
      try {
        const p = await fetchProgress(reportId);
        if (cancelled) return;
        setProgress(p);
        if (p.status === "complete") {
          setTimeout(onComplete, 400);
        } else if (p.status !== "error" && p.status !== "cancelled") {
          setTimeout(poll, 2000);
        }
      } catch (e: any) {
        if (!cancelled) setError(e.message || "status fetch failed");
      }
    }
    poll();
    return () => {
      cancelled = true;
    };
  }, [reportId, onComplete]);

  async function handleCancel() {
    if (cancelling) return;
    setCancelling(true);
    try {
      await cancelReport(reportId);
    } catch (e: any) {
      setError(e.message || "cancel failed");
      setCancelling(false);
    }
  }

  const isTerminal =
    progress?.status === "complete" ||
    progress?.status === "error" ||
    progress?.status === "cancelled";

  if (error) {
    return (
      <div className="rounded-lg border border-alpha-red/40 bg-alpha-red/10 p-4 flex items-center gap-3">
        <AlertCircle className="text-alpha-red" />
        <div>
          <div className="text-alpha-red font-medium">Generation error</div>
          <div className="text-sm text-gray-400">{error}</div>
        </div>
      </div>
    );
  }

  const currentIdx = progress ? indexOf(progress.status) : 0;

  const cancelledView = progress?.status === "cancelled";

  return (
    <div className="max-w-2xl space-y-6">
      <div className="rounded-xl border border-gray-800 bg-gray-900/40 p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="text-sm text-gray-400">Report ID</div>
            <div className="font-mono text-xs text-gray-500 break-all">{reportId}</div>
          </div>
          {!isTerminal && (
            <button
              onClick={handleCancel}
              disabled={cancelling}
              className="flex-shrink-0 inline-flex items-center gap-2 px-3 py-1.5 text-sm rounded-lg border border-alpha-red/40 text-alpha-red hover:bg-alpha-red/10 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              title="Stop generating this report"
            >
              <StopCircle size={16} />
              {cancelling ? "Cancelling..." : "Stop Generating"}
            </button>
          )}
        </div>
        <div className="mt-4 flex items-center gap-3">
          {cancelledView ? (
            <Ban className="text-alpha-red" size={20} />
          ) : (
            <Loader2 className="animate-spin text-alpha-blue" size={20} />
          )}
          <div>
            <div className={"font-medium " + (cancelledView ? "text-alpha-red" : "text-gray-100")}>
              {cancelledView
                ? "Cancelled by user"
                : cancelling
                ? "Stopping after current step..."
                : progress?.current_step || "Starting..."}
            </div>
            <div className="text-xs text-gray-500">
              Agent: {progress?.current_agent || "-"} -
              {" "}Elapsed: {((progress?.elapsed_time_ms || 0) / 1000).toFixed(1)}s
            </div>
          </div>
        </div>
      </div>

      <ol className="space-y-2">
        {STEPS.map((s, i) => {
          const done = i < currentIdx;
          const active = i === currentIdx;
          return (
            <li
              key={s.key}
              className={
                "flex items-center gap-3 px-4 py-3 rounded-lg border " +
                (done
                  ? "border-alpha-green/40 bg-alpha-green/5"
                  : active
                  ? "border-alpha-blue/40 bg-alpha-blue/5"
                  : "border-gray-800 bg-gray-900/40")
              }
            >
              {done ? (
                <CheckCircle2 className="text-alpha-green" size={18} />
              ) : active ? (
                <Loader2 className="text-alpha-blue animate-spin" size={18} />
              ) : (
                <Circle className="text-gray-600" size={18} />
              )}
              <span className={done ? "text-gray-300" : active ? "text-gray-100" : "text-gray-500"}>
                {s.label}
              </span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
