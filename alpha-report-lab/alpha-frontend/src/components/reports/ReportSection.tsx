"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ReportSection as RS } from "@/lib/types";
import Badge from "@/components/ui/Badge";

export default function ReportSection({ section }: { section: RS }) {
  return (
    <section id={section.id} className="scroll-mt-24">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-xl font-semibold text-gray-100">{section.title}</h2>
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <Badge>{section.agent}</Badge>
          <span>{section.tokens_used.toLocaleString()} tokens</span>
          <span>{section.generation_time_ms}ms</span>
        </div>
      </div>
      <div className="prose-report">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{section.content}</ReactMarkdown>
      </div>
    </section>
  );
}
