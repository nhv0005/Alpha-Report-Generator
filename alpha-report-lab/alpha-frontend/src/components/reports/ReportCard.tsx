"use client";

import Link from "next/link";
import type { AlphaReport } from "@/lib/types";
import Badge from "@/components/ui/Badge";
import ScoreGauge from "./ScoreGauge";
import {
  formatCurrency,
  formatDate,
  formatPercentage,
  getRecommendationColor,
  percentageClass,
} from "@/lib/utils";

export default function ReportCard({ report }: { report: AlphaReport }) {
  return (
    <Link
      href={`/reports/${report.id}`}
      className="block rounded-xl border border-gray-800 bg-gray-900/40 hover:bg-gray-900/80 hover:border-gray-700 transition p-5"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <div className="font-mono font-semibold text-lg text-gray-100">{report.ticker}</div>
            <Badge className={getRecommendationColor(report.recommendation)}>
              {report.recommendation.replace("_", " ")}
            </Badge>
          </div>
          <div className="text-sm text-gray-400 truncate">{report.company_name || report.sector}</div>
          <div className="text-xs text-gray-500 mt-1">
            {formatDate(report.generated_at)}
          </div>
        </div>
        <ScoreGauge score={report.conviction_score} size={72} />
      </div>

      <div className="mt-4 grid grid-cols-3 gap-3 text-sm">
        <div>
          <div className="text-gray-500 text-xs">Current</div>
          <div className="text-gray-200">{formatCurrency(report.current_price)}</div>
        </div>
        <div>
          <div className="text-gray-500 text-xs">Target</div>
          <div className="text-gray-200">{formatCurrency(report.target_price)}</div>
        </div>
        <div>
          <div className="text-gray-500 text-xs">Upside</div>
          <div className={percentageClass(report.upside_percentage)}>
            {formatPercentage(report.upside_percentage)}
          </div>
        </div>
      </div>
    </Link>
  );
}
