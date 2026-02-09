import type { ChatResponseData, Dataset, HealthStatus, CapabilitiesResponse } from "./types";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function sendMessage(content: string, dataset: Dataset = "nyc_taxi"): Promise<ChatResponseData> {
  const res = await fetch(`${API}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      messages: [{ role: "user", content }],
      dataset,
    }),
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => "Unknown error");
    throw new Error(`API error ${res.status}: ${detail}`);
  }
  return res.json();
}

export async function getHealth(dataset: Dataset = "nyc_taxi"): Promise<HealthStatus> {
  const res = await fetch(`${API}/api/health?dataset=${dataset}`);
  if (!res.ok) throw new Error("Health check failed");
  return res.json();
}

export async function getCapabilities(dataset: Dataset = "nyc_taxi"): Promise<CapabilitiesResponse> {
  const res = await fetch(`${API}/api/capabilities?dataset=${dataset}`);
  if (!res.ok) throw new Error("Capabilities fetch failed");
  return res.json();
}
