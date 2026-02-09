// ── Mirrors backend schemas ────────────────────────────────────────────────

export type Dataset = "nyc_taxi" | "healthcare";

export type SourceLayer = "technical" | "semantic" | "ontology";

export type InsightType = "WARNING" | "CONTEXT" | "RULE" | "INSIGHT";

export interface InsightItem {
  type: InsightType;
  text: string;
  source: SourceLayer;
}

export interface ChartData {
  type: "bar" | "table";
  title: string;
  labels: string[];
  values: number[];
  metric_label: string;
}

export interface ToolCall {
  tool: string;
  layer: SourceLayer;
  summary: string;
}

export interface ChatResponseData {
  answer: string;
  chart: ChartData | null;
  table: Record<string, unknown>[] | null;
  insights: InsightItem[];
  sources: SourceLayer[];
  tools_used: ToolCall[];
  suggestions: string[];
  error: string | null;
}

// ── Local UI types ─────────────────────────────────────────────────────────

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  data?: ChatResponseData;
  isLoading?: boolean;
}

export interface HealthStatus {
  status: "ok" | "degraded" | "error";
  agent_ready: boolean;
  layers: Record<string, boolean>;
}

export interface Capability {
  name: string;
  description: string;
  example: string;
}

export interface CapabilitiesResponse {
  capabilities: Capability[];
  starter_questions: string[];
}
