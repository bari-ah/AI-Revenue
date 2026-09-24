"use client";

const BASE = (process.env.NEXT_PUBLIC_API_URL || "").replace(/\/$/, "");

class ApiError extends Error {
  status: number;

  constructor(path: string, status: number, detail?: string) {
    super(detail ? `${path} → ${status}: ${detail}` : `${path} → ${status}`);
    this.name = "ApiError";
    this.status = status;
  }
}

async function errorDetail(response: Response): Promise<string | undefined> {
  try {
    const body: unknown = await response.json();
    if (body && typeof body === "object" && "detail" in body) {
      const detail = (body as { detail?: unknown }).detail;
      return typeof detail === "string" ? detail : undefined;
    }
  } catch {
    // The server may have returned an empty or non-JSON response.
  }
  return undefined;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE}${path}`, {
      ...init,
      cache: "no-store",
      headers: {
        Accept: "application/json",
        ...(init?.headers ?? {}),
      },
    });
  } catch {
    throw new Error(`Unable to connect to the backend while requesting ${path}`);
  }

  if (!response.ok) {
    throw new ApiError(path, response.status, await errorDetail(response));
  }

  try {
    return (await response.json()) as T;
  } catch {
    throw new Error(`${path} returned invalid JSON`);
  }
}

async function get<T>(path: string): Promise<T> {
  return request<T>(path);
}

async function post<T>(path: string): Promise<T> {
  return request<T>(path, { method: "POST" });
}

export type Stats = {
  temp_c: number | null;
  condition: string | null;
  last_check: string | null;
  campaigns_today: number;
  messages_sent_today: number;
  total_leads: number;
  next_check_seconds: number;
  trigger_active: boolean;
};

export type Campaign = {
  id: number;
  ts: string;
  temp_c: number;
  condition: string;
  target_segment: string;
  message: string;
  status: string;
  recipients: number;
};

export type TestCampaignResponse = {
  ok: boolean;
  status: "sent" | "failed";
  temp_c: number;
  message_id: number | null;
  telegram_message_id: number | null;
  recipients: number;
};

export const api = {
  stats: () => get<Stats>("/api/v1/stats"),
  campaigns: () => get<Campaign[]>("/api/v1/campaigns"),
  test: () => post<TestCampaignResponse>("/api/v1/campaigns/test"),
};
