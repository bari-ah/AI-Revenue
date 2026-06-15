"use client";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`, { cache: "no-store" });
  if (!r.ok) throw new Error(`${path} → ${r.status}`);
  return r.json();
}

async function post<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`, { method: "POST", cache: "no-store" });
  if (!r.ok) throw new Error(`${path} → ${r.status}`);
  return r.json();
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

export const api = {
  stats: () => get<Stats>("/api/v1/stats"),
  campaigns: () => get<Campaign[]>("/api/v1/campaigns"),
  test: () => post<{ ok: boolean; temp_c: number; message_id: number | null; recipients: number }>("/api/v1/campaigns/test"),
};
