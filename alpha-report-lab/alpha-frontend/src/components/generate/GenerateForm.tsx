"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import TickerInput from "./TickerInput";
import ProgressTracker from "./ProgressTracker";
import { generateReport } from "@/lib/api";
import type { GenerateRequest } from "@/lib/types";

const FOCUS_OPTIONS = [
  "Fundamental Analysis",
  "Technical Analysis",
  "Catalyst Identification",
  "Risk Assessment",
  "Competitive Landscape",
  "Sentiment Analysis",
];

export default function GenerateForm() {
  const router = useRouter();
  const [ticker, setTicker] = useState("");
  const [horizon, setHorizon] = useState<"short_term" | "medium_term" | "long_term">("medium_term");
  const [risk, setRisk] = useState<"conservative" | "moderate" | "aggressive">("moderate");
  const [focus, setFocus] = useState<string[]>(FOCUS_OPTIONS);
  const [instructions, setInstructions] = useState("");
  const [reportId, setReportId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggleFocus = (f: string) => {
    setFocus((prev) => (prev.includes(f) ? prev.filter((x) => x !== f) : [...prev, f]));
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ticker) return;
    setError(null);
    setLoading(true);
    try {
      const req: GenerateRequest = {
        ticker,
        investment_horizon: horizon,
        risk_tolerance: risk,
        focus_areas: focus,
        custom_instructions: instructions || undefined,
        user_id: "lab-user",
      };
      const res = await generateReport(req);
      setReportId(res.report_id);
    } catch (e: any) {
      setError(e.message || "Failed to start generation");
      setLoading(false);
    }
  };

  if (reportId) {
    return (
      <ProgressTracker
        reportId={reportId}
        onComplete={() => router.push(`/reports/${reportId}`)}
      />
    );
  }

  return (
    <form onSubmit={submit} className="space-y-6 max-w-2xl">
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">Ticker Symbol</label>
        <TickerInput value={ticker} onChange={setTicker} />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">Investment Horizon</label>
        <div className="grid grid-cols-3 gap-2">
          {[
            { v: "short_term", l: "Short Term", sub: "< 3 months" },
            { v: "medium_term", l: "Medium Term", sub: "3-12 months" },
            { v: "long_term", l: "Long Term", sub: "> 1 year" },
          ].map((o) => (
            <button
              type="button"
              key={o.v}
              onClick={() => setHorizon(o.v as any)}
              className={
                "rounded-lg border px-3 py-3 text-left transition " +
                (horizon === o.v
                  ? "border-alpha-blue bg-alpha-blue/10 text-gray-100"
                  : "border-gray-800 bg-gray-900/40 text-gray-400 hover:border-gray-700")
              }
            >
              <div className="text-sm font-medium">{o.l}</div>
              <div className="text-xs text-gray-500">{o.sub}</div>
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">Risk Tolerance</label>
        <div className="grid grid-cols-3 gap-2">
          {["conservative", "moderate", "aggressive"].map((o) => (
            <button
              type="button"
              key={o}
              onClick={() => setRisk(o as any)}
              className={
                "rounded-lg border px-3 py-3 capitalize transition " +
                (risk === o
                  ? "border-alpha-blue bg-alpha-blue/10 text-gray-100"
                  : "border-gray-800 bg-gray-900/40 text-gray-400 hover:border-gray-700")
              }
            >
              {o}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">Focus Areas</label>
        <div className="grid grid-cols-2 gap-2">
          {FOCUS_OPTIONS.map((f) => (
            <label
              key={f}
              className="flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-800 bg-gray-900/40 text-sm cursor-pointer hover:border-gray-700"
            >
              <input
                type="checkbox"
                checked={focus.includes(f)}
                onChange={() => toggleFocus(f)}
                className="accent-alpha-blue"
              />
              <span className="text-gray-300">{f}</span>
            </label>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Custom Instructions (optional)
        </label>
        <textarea
          value={instructions}
          onChange={(e) => setInstructions(e.target.value)}
          rows={3}
          placeholder="Any additional guidance for the agents..."
          className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-alpha-blue/40"
        />
      </div>

      {error && <div className="text-sm text-alpha-red">{error}</div>}

      <button
        type="submit"
        disabled={!ticker || loading}
        className="px-5 py-2.5 bg-alpha-blue hover:bg-alpha-blue/90 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-white font-medium transition"
      >
        {loading ? "Starting..." : "Generate Alpha Report"}
      </button>
    </form>
  );
}
