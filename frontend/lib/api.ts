import type {
  Block,
  District,
  Forecast,
  HealthResponse,
  Panchayat,
  PanchayatListItem,
  RiskMap,
} from "@/types/api";

const baseUrl = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";
const requestTimeoutMs = 10000;

export class ApiError extends Error {
  status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string): Promise<T> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), requestTimeoutMs);

  try {
    const response = await fetch(`${baseUrl}${path}`, {
      signal: controller.signal,
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    const body: unknown = await response.json().catch(() => null);

    if (!response.ok) {
      const detail = typeof body === "object" && body !== null && "detail" in body && typeof body.detail === "string"
        ? body.detail
        : `Request failed with status ${response.status}.`;
      throw new ApiError(detail, response.status);
    }

    return body as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiError("The weather service took too long to respond.");
    }
    throw new ApiError("Unable to connect to the weather service.");
  } finally {
    window.clearTimeout(timeout);
  }
}

export const api = {
  health: () => request<HealthResponse>("/api/health"),
  districts: () => request<District[]>("/api/districts"),
  blocks: () => request<Block[]>("/api/blocks"),
  panchayatsForBlock: (blockId: string) => request<PanchayatListItem[]>(`/api/blocks/${encodeURIComponent(blockId)}/panchayats`),
  panchayat: (panchayatId: string) => request<Panchayat>(`/api/panchayats/${encodeURIComponent(panchayatId)}`),
  forecast: (panchayatId: string) => request<Forecast>(`/api/forecast/${encodeURIComponent(panchayatId)}`),
  riskMap: () => request<RiskMap>("/api/risk-map"),
};