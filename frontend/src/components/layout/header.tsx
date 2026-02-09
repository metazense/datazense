"use client";

import { useEffect, useState } from "react";
import { getHealth } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { Dataset } from "@/lib/types";

const DATASET_CONFIG: Record<
  Dataset,
  { label: string; subtitle: string; accent: string; icon: string }
> = {
  nyc_taxi: {
    label: "NYC Taxi",
    subtitle: "NYC Taxi Data Intelligence",
    accent: "bg-emerald-600",
    icon: "DZ",
  },
  healthcare: {
    label: "Healthcare",
    subtitle: "Healthcare Analytics (Synthea)",
    accent: "bg-blue-600",
    icon: "DZ",
  },
};

interface Props {
  dataset: Dataset;
  onDatasetChange: (d: Dataset) => void;
}

export function Header({ dataset, onDatasetChange }: Props) {
  const [layers, setLayers] = useState<Record<string, boolean>>({});

  useEffect(() => {
    getHealth(dataset)
      .then((h) => setLayers(h.layers))
      .catch(() => {});
  }, [dataset]);

  const config = DATASET_CONFIG[dataset];

  const dots: { key: string; label: string; color: string }[] = [
    {
      key: "technical",
      label: "Technical",
      color: layers.technical ? "bg-blue-500" : "bg-gray-300",
    },
    {
      key: "semantic",
      label: "Semantic",
      color: layers.semantic ? "bg-emerald-500" : "bg-gray-300",
    },
    {
      key: "ontology",
      label: "Ontology",
      color: layers.ontology ? "bg-purple-500" : "bg-gray-300",
    },
  ];

  return (
    <header className="flex items-center justify-between border-b px-6 py-3">
      <div className="flex items-center gap-3">
        <div
          className={cn(
            "flex h-8 w-8 items-center justify-center rounded-lg text-white text-sm font-bold",
            config.accent,
          )}
        >
          {config.icon}
        </div>
        <div>
          <h1 className="text-sm font-semibold leading-none">
            DataZense
          </h1>
          <p className="text-xs text-muted-foreground">{config.subtitle}</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* Dataset selector */}
        <select
          value={dataset}
          onChange={(e) => onDatasetChange(e.target.value as Dataset)}
          className="rounded-md border bg-background px-2 py-1 text-xs font-medium focus:outline-none focus:ring-2 focus:ring-ring"
        >
          <option value="nyc_taxi">NYC Taxi</option>
          <option value="healthcare">Healthcare</option>
        </select>

        {/* Layer status dots */}
        <div className="flex items-center gap-3">
          {dots.map((d) => (
            <div
              key={d.key}
              className="flex items-center gap-1.5"
              title={d.label}
            >
              <span
                className={cn("inline-block h-2 w-2 rounded-full", d.color)}
              />
              <span className="text-xs text-muted-foreground hidden sm:inline">
                {d.label}
              </span>
            </div>
          ))}
        </div>
      </div>
    </header>
  );
}
