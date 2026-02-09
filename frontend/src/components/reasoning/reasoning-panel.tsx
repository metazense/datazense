"use client";

import { useState } from "react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { SourceBadge } from "@/components/insights/source-badge";
import type { ToolCall } from "@/lib/types";

export function ReasoningPanel({ tools }: { tools: ToolCall[] }) {
  const [open, setOpen] = useState(false);

  if (!tools.length) return null;

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <CollapsibleTrigger className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground transition-colors">
        <span
          className="inline-block transition-transform"
          style={{ transform: open ? "rotate(90deg)" : undefined }}
        >
          ▶
        </span>
        <span>
          {tools.length} tool{tools.length > 1 ? "s" : ""} used
        </span>
      </CollapsibleTrigger>
      <CollapsibleContent className="mt-2 space-y-1.5">
        {tools.map((tc, i) => (
          <div
            key={i}
            className="flex items-center gap-2 rounded-md bg-muted/50 px-3 py-1.5 text-xs"
          >
            <code className="font-mono text-foreground/70">{tc.tool}</code>
            <SourceBadge layer={tc.layer} />
          </div>
        ))}
      </CollapsibleContent>
    </Collapsible>
  );
}
