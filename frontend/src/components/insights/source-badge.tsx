"use client";

import { Badge } from "@/components/ui/badge";
import type { SourceLayer } from "@/lib/types";
import { cn } from "@/lib/utils";

const config: Record<SourceLayer, { label: string; className: string }> = {
  technical: {
    label: "Technical",
    className: "bg-blue-100 text-blue-800 hover:bg-blue-100",
  },
  semantic: {
    label: "Semantic",
    className: "bg-emerald-100 text-emerald-800 hover:bg-emerald-100",
  },
  ontology: {
    label: "Ontology",
    className: "bg-purple-100 text-purple-800 hover:bg-purple-100",
  },
};

export function SourceBadge({ layer }: { layer: SourceLayer }) {
  const c = config[layer];
  return (
    <Badge variant="secondary" className={cn("text-xs font-medium", c.className)}>
      {c.label}
    </Badge>
  );
}
