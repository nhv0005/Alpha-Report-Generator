"use client";

import type { AlphaReport } from "@/lib/types";
import Badge from "@/components/ui/Badge";
import ScoreGauge from "./ScoreGauge";
import ReportSection from "./ReportSection";
import MetricsTable from "./MetricsTable";
import {
  formatCurrency,
  formatDateTime,
  formatPercentage,
  getRecommendationColor,
  getRiskColor,
  percentageClass,
} from "@/lib/utils";

export default function ReportViewer({ report }: { report: AlphaReport }) {
  // Find financial data from any section that captured it
  const fundData = report.sections.find((s) => s.type === "fundamental_analysis")?.data;
  const peerData = (fundData?.peer_comparison as any[] | undefined) || [];

  return (
    <div className="flex gap-8">
      {/* TOC sidebar */}
      <aside className="hidden lg:block w-56 shrink-0 sticky top-6 h-fit">
        <div className="text-xs uppercase tracking-wider text-gray-500 mb-2">Sections</div>
        <nav className="space-y-1">
          {report.sections.map((s) => (
            <a
              key={s.id}
              href={`#${s.id}`}
              className="block text-sm text-gray-400 hover:text-gray-100 py-1 truncate"
            >
              {s.title}
            </a>
          ))}
          <a href="#appendix" className="block text-sm text-gray-400 hover:text-gray-100 py-1">
            Appendix
          </a>
        </nav>
      </aside>

      <div className="flex-1 min-w-0 space-y-10">
        {/* Header */}
        <header className="rounded-xl border border-gray-800 bg-gray-900/40 p-6">
          <div className="flex items-start justify-between gap-6">
            <div className="min-w-0">
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-semibold tracking-tight">
                  {report.company_name || report.ticker}
                </h1>
                <Badge className="font-mono">{report.ticker}</Badge>
                <Badge className={getRecommendationColor(report.recommendation)}>
                  {report.recommendation.replace("_", " ")}
                </Badge>
              </div>
              <div className="text-sm text-gray-500 mt-1">
                {report.sector} - {formatDateTime(report.generated_at)}
              </div>
            </div>
            <ScoreGauge score={report.conviction_score} size={96} />
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
            <div>
              <div className="text-xs text-gray-500">Target Price</div>
              <div className="text-lg text-gray-100">{formatCurrency(report.target_price)}</div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Current Price</div>
              <div className="text-lg text-gray-100">{formatCurrency(report.current_price)}</div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Upside</div>
              <div className={`text-lg ${percentageClass(report.upside_percentage)}`}>
                {formatPercentage(report.upside_percentage)}
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Risk Rating</div>
              <div>
                <Badge className={getRiskColor(report.risk_rating)}>{report.risk_rating}</Badge>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4 text-xs text-gray-500 pt-4 border-t border-gray-800">
            <div>Model: <span className="text-gray-300">{report.metadata.model}</span></div>
            <div>Total Tokens: <span className="text-gray-300">{report.metadata.total_tokens.toLocaleString()}</span></div>
            <div>Gen Time: <span className="text-gray-300">{(report.metadata.total_generation_time_ms / 1000).toFixed(1)}s</span></div>
            <div>Trace: <span className="text-gray-300 font-mono text-[10px]">{report.metadata.trace_id?.slice(0, 16) || "-"}</span></div>
          </div>
        </header>

        {/* Peer comparison table (if available) */}
        {peerData.length > 0 && (
          <section>
            <h2 className="text-lg font-semibold mb-3 text-gray-100">Peer Comparison</h2>
            <div className="overflow-x-auto rounded-xl border border-gray-800">
              <table className="w-full text-sm">
                <thead className="bg-gray-900/60 text-gray-400">
                  <tr>
                    <th className="text-left px-3 py-2">Ticker</th>
                    <th className="text-left px-3 py-2">Company</th>
                    <th className="text-right px-3 py-2">Market Cap</th>
                    <th className="text-right px-3 py-2">P/E</th>
                    <th className="text-right px-3 py-2">Rev Growth</th>
                    <th className="text-right px-3 py-2">Op Margin</th>
                    <th className="text-right px-3 py-2">ROE</th>
                  </tr>
                </thead>
                <tbody>
                  {peerData.map((p: any) => (
                    <tr key={p.ticker} className="border-t border-gray-800">
                      <td className="px-3 py-2 font-mono">{p.ticker}</td>
                      <td className="px-3 py-2 text-gray-400">{p.company_name}</td>
                      <td className="px-3 py-2 text-right">{formatCurrency(p.market_cap / 1e9)}B</td>
                      <td className="px-3 py-2 text-right">{p.pe_ratio?.toFixed(1)}</td>
                      <td className={`px-3 py-2 text-right ${percentageClass(p.revenue_growth)}`}>
                        {formatPercentage(p.revenue_growth * 100)}
                      </td>
                      <td className="px-3 py-2 text-right">{formatPercentage(p.operating_margin * 100)}</td>
                      <td className="px-3 py-2 text-right">{formatPercentage(p.roe * 100)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* Sections */}
        {report.sections.map((s) => (
          <ReportSection key={s.id} section={s} />
        ))}

        {/* Appendix */}
        <section id="appendix" className="border-t border-gray-800 pt-6">
          <h2 className="text-lg font-semibold mb-3 text-gray-100">Appendix</h2>
          <div className="text-sm text-gray-400 space-y-3">
            <p>
              <strong>Methodology:</strong> This report was produced by a multi-agent AI system
              (research, analysis, sentiment, risk, and writer agents) using mock financial data
              for demonstration purposes. Target prices are derived from peer-relative valuation
              and qualitative synthesis.
            </p>
            <p>
              <strong>Disclaimer:</strong> This is a demonstration of Dynatrace AI Observability
              instrumentation and is NOT investment advice. All financial data is synthetic.
            </p>
            <p>
              <strong>Agents used:</strong> {report.metadata.agents_used.join(", ") || "-"}
            </p>
            <p>
              <strong>Tools called:</strong> {report.metadata.tools_called.join(", ") || "-"}
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
