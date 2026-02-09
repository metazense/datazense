"use client";

import { cn } from "@/lib/utils";
import type { InsightItem } from "@/lib/types";
import { SourceBadge } from "./source-badge";

const style: Record<string, { border: string; bg: string; icon: string }> = {
  WARNING: {
    border: "border-l-amber-500",
    bg: "bg-amber-50",
    icon: "⚠",
  },
  CONTEXT: {
    border: "border-l-blue-500",
    bg: "bg-blue-50",
    icon: "ℹ",
  },
  RULE: {
    border: "border-l-purple-500",
    bg: "bg-purple-50",
    icon: "§",
  },
  INSIGHT: {
    border: "border-l-emerald-500",
    bg: "bg-emerald-50",
    icon: "✦",
  },
};

export function InsightCard({ insight }: { insight: InsightItem }) {
  const s = style[insight.type] ?? style.CONTEXT;
  return (
    <div
      className={cn(
        "rounded-md border-l-4 px-4 py-3 text-sm",
        s.border,
        s.bg,
      )}
    >
      <div className="flex items-start gap-2">
        <span className="mt-0.5 shrink-0">{s.icon}</span>
        <div className="min-w-0 flex-1">
          <p className="leading-relaxed text-foreground/90">{insight.text}</p>
          <div className="mt-2">
            <SourceBadge layer={insight.source} />
          </div>
        </div>
      </div>
    </div>
  );
}
