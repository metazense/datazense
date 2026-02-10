"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import type { ChartData } from "@/lib/types";

function formatValue(v: number): string {
  if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`;
  if (v >= 1_000) return `${(v / 1_000).toFixed(1)}K`;
  return v.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

export function MetricChart({ data }: { data: ChartData }) {
  const chartData = data.labels.map((label, i) => ({
    name: label,
    value: data.values[i] ?? 0,
  }));

  return (
    <div className="w-full">
      {data.title && (
        <h4 className="mb-2 text-sm font-semibold text-foreground/80">
          {data.title}
        </h4>
      )}
      <div className="h-[250px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 0, right: 30, left: 0, bottom: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" horizontal={false} />
            <XAxis
              type="number"
              tickFormatter={formatValue}
              fontSize={12}
            />
            <YAxis
              type="category"
              dataKey="name"
              width={120}
              fontSize={12}
              tickLine={false}
            />
            <Tooltip
              formatter={(v: number | undefined) => [formatValue(v ?? 0), data.metric_label]}
              contentStyle={{
                borderRadius: "8px",
                border: "1px solid hsl(var(--border))",
                fontSize: "13px",
              }}
            />
            <Bar
              dataKey="value"
              fill="#8142ff"
              radius={[0, 4, 4, 0]}
              barSize={24}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
