"use client";

import ReactMarkdown from "react-markdown";
import { Skeleton } from "@/components/ui/skeleton";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { MetricChart } from "@/components/insights/metric-chart";
import { DataTable } from "@/components/insights/data-table";
import { InsightCard } from "@/components/insights/insight-card";
import { SourceBadge } from "@/components/insights/source-badge";
import { ReasoningPanel } from "@/components/reasoning/reasoning-panel";
import { SuggestedQuestions } from "@/components/chat/suggested-questions";
import type { Message } from "@/lib/types";

interface Props {
  message: Message;
  onSuggestionClick?: (q: string) => void;
}

export function ChatMessage({ message, onSuggestionClick }: Props) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="flex items-start gap-3 max-w-[80%]">
          <div className="rounded-2xl rounded-tr-sm bg-primary px-4 py-2.5 text-sm text-primary-foreground">
            {message.content}
          </div>
          <Avatar className="h-8 w-8 shrink-0">
            <AvatarFallback className="bg-primary text-primary-foreground text-xs">
              You
            </AvatarFallback>
          </Avatar>
        </div>
      </div>
    );
  }

  // Assistant message
  if (message.isLoading) {
    return (
      <div className="flex items-start gap-3 max-w-[85%]">
        <Avatar className="h-8 w-8 shrink-0">
          <AvatarFallback className="bg-[#8142ff] text-white text-xs">
            AI
          </AvatarFallback>
        </Avatar>
        <div className="space-y-3 flex-1">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
          <Skeleton className="h-4 w-2/3" />
          <p className="text-xs text-muted-foreground animate-pulse">
            Querying semantic layer…
          </p>
        </div>
      </div>
    );
  }

  const d = message.data;

  return (
    <div className="flex items-start gap-3 max-w-[85%]">
      <Avatar className="h-8 w-8 shrink-0">
        <AvatarFallback className="bg-[#8142ff] text-white text-xs">
          AI
        </AvatarFallback>
      </Avatar>
      <div className="min-w-0 flex-1 space-y-4">
        {/* Chart */}
        {d?.chart && <MetricChart data={d.chart} />}

        {/* Markdown answer */}
        <div className="prose prose-sm max-w-none text-foreground/90 prose-p:leading-relaxed prose-headings:text-foreground">
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>

        {/* Data table */}
        {d?.table && d.table.length > 0 && <DataTable rows={d.table} />}

        {/* Insight cards */}
        {d?.insights && d.insights.length > 0 && (
          <div className="space-y-2">
            {d.insights.map((ins, i) => (
              <InsightCard key={i} insight={ins} />
            ))}
          </div>
        )}

        {/* Source badges */}
        {d?.sources && d.sources.length > 0 && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Sources:</span>
            {d.sources.map((s) => (
              <SourceBadge key={s} layer={s} />
            ))}
          </div>
        )}

        {/* Reasoning panel */}
        {d?.tools_used && d.tools_used.length > 0 && (
          <ReasoningPanel tools={d.tools_used} />
        )}

        {/* Follow-up suggestions */}
        {d?.suggestions && d.suggestions.length > 0 && onSuggestionClick && (
          <SuggestedQuestions
            questions={d.suggestions}
            onSelect={onSuggestionClick}
            variant="inline"
          />
        )}
      </div>
    </div>
  );
}
