"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { getHealth } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { Dataset } from "@/lib/types";

const DATASET_CONFIG: Record<
  Dataset,
  { label: string; subtitle: string }
> = {
  nyc_taxi: {
    label: "NYC Taxi",
    subtitle: "NYC Taxi Data Intelligence",
  },
  healthcare: {
    label: "Healthcare",
    subtitle: "Healthcare Analytics (Synthea)",
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
      color: layers.technical ? "bg-blue-500" : "bg-[#969499]",
    },
    {
      key: "semantic",
      label: "Semantic",
      color: layers.semantic ? "bg-emerald-500" : "bg-[#969499]",
    },
    {
      key: "ontology",
      label: "Ontology",
      color: layers.ontology ? "bg-[#8142ff]" : "bg-[#969499]",
    },
  ];

  return (
    <header className="flex items-center justify-between bg-black px-6 py-3">
      {/* Logo + brand */}
      <div className="flex items-center gap-3">
        <Image
          src="/logo.png"
          alt="Metazense Logo"
          width={36}
          height={36}
          className="rounded-lg"
        />
        <div>
          <h1 className="font-display text-sm font-medium leading-none text-white tracking-tight">
            DataZense
          </h1>
          <p className="text-xs text-white/60">{config.subtitle}</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* Dataset selector */}
        <select
          value={dataset}
          onChange={(e) => onDatasetChange(e.target.value as Dataset)}
          className="rounded-full border border-white/10 bg-[#29282a] px-3 py-1 text-xs font-medium text-white/90 focus:outline-none focus:ring-2 focus:ring-[#8142ff]"
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
              <span className="text-xs text-white/60 hidden sm:inline">
                {d.label}
              </span>
            </div>
          ))}
        </div>
      </div>
    </header>
  );
}
