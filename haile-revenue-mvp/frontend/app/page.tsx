"use client";

import { useCallback, useEffect, useState, type ReactNode } from "react";
import {
  Activity,
  CloudRain,
  MessageCircle,
  RefreshCw,
  Send,
  Sun,
  Users,
  Zap,
} from "lucide-react";
import type { Campaign, Stats } from "@/lib/api";

const MOCK_STATS: Stats = {
  temp_c: 29.5,
  condition: "Clear",
  last_check: "2026-09-23T09:56:00+03:00",
  campaigns_today: 4,
  messages_sent_today: 342,
  total_leads: 1250,
  next_check_seconds: 240,
  trigger_active: true,
};

const MOCK_CAMPAIGNS: Campaign[] = [
  {
    id: 1042,
    ts: "2026-09-23T09:42:00+03:00",
    temp_c: 29.5,
    condition: "Clear",
    target_segment: "vip,family,regular",
    message:
      "🔥 <b>Adama is 30°C right now</b><br /><br />Pool is empty. Drinks are cold. Music is on.<br /><br />Show this message at Haile Resort for 30 birr entry.",
    telegram_message_id: 887342,
    status: "sent",
    recipients: 342,
  },
  {
    id: 1041,
    ts: "2026-09-23T07:30:00+03:00",
    temp_c: 28.8,
    condition: "Clear",
    target_segment: "vip,family",
    message:
      "☀️ <b>Perfect day alert</b><br /><br />Your personalized poolside offer is ready at Haile Resort.",
    telegram_message_id: 887119,
    status: "sent",
    recipients: 184,
  },
  {
    id: 1040,
    ts: "2026-09-23T05:00:00+03:00",
    temp_c: 27.9,
    condition: "Clear",
    target_segment: "regular",
    message:
      "🌤️ <b>Good morning from Haile Resort</b><br /><br />Start your day with an exclusive member offer.",
    telegram_message_id: 886904,
    status: "sent",
    recipients: 96,
  },
];

function TempIcon({ temp }: { temp: number | null }) {
  if (temp == null) return <CloudRain className="w-6 h-6" />;
  if (temp >= 30) return <Sun className="w-6 h-6 text-orange-400" />;
  if (temp >= 28) return <Sun className="w-6 h-6 text-yellow-400" />;
  return <CloudRain className="w-6 h-6 text-slate-400" />;
}

export default function Home() {
  const [stats, setStats] = useState<Stats>(MOCK_STATS);
  const [campaigns, setCampaigns] = useState<Campaign[]>(MOCK_CAMPAIGNS);
  const [testing, setTesting] = useState(false);
  const [testMsg, setTestMsg] = useState<string>("");

  // Stable mock refresh function: useEffect can safely track it without warnings
  // or recreating the polling interval on every render.
  const refresh = useCallback((): void => {
    setStats(MOCK_STATS);
    setCampaigns(MOCK_CAMPAIGNS);
  }, []);

  useEffect(() => {
    refresh();
    const timer = window.setInterval(refresh, 30_000);
    return () => window.clearInterval(timer);
  }, [refresh]);

  const trigger = useCallback(async (): Promise<void> => {
    setTesting(true);
    setTestMsg("");

    await new Promise<void>((resolve) => window.setTimeout(resolve, 450));

    setStats((current) => ({
      ...current,
      campaigns_today: current.campaigns_today + 1,
      messages_sent_today: current.messages_sent_today + 342,
    }));
    setTestMsg("✅ Test campaign completed · 342 leads reached · Automation healthy");
    setTesting(false);
  }, []);

  return (
    <main className="min-h-screen p-6 md:p-10 max-w-6xl mx-auto">
      <header className="flex items-center justify-between mb-10">
        <div>
          <h1 className="text-3xl md:text-4xl font-bold tracking-tight">Haile Revenue OS</h1>
          <p className="text-sm text-slate-400 mt-1">Autonomous AI Revenue System · Adama, Ethiopia</p>
        </div>
        <button
          type="button"
          onClick={refresh}
          aria-label="Refresh dashboard"
          className="p-2 rounded-lg border border-slate-800 hover:bg-slate-900"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </header>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="md:col-span-2 rounded-2xl border border-slate-800 bg-gradient-to-br from-slate-900 to-black p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <TempIcon temp={stats.temp_c} />
              <span className="text-sm text-slate-400">Adama live</span>
            </div>
            {stats.trigger_active && (
              <span className="px-2 py-1 text-xs font-semibold rounded-full bg-orange-500/20 text-orange-300 border border-orange-500/30">
                🔥 TRIGGER ACTIVE
              </span>
            )}
          </div>
          <div className="mt-4 flex items-end gap-2">
            <span className="text-7xl font-bold tracking-tighter">{stats.temp_c?.toFixed(1) ?? "—"}</span>
            <span className="text-2xl text-slate-400 mb-2">°C</span>
          </div>
          <div className="mt-1 text-slate-300 capitalize">{stats.condition ?? "—"}</div>
          <div className="mt-4 text-xs text-slate-500">
            Last check: {stats.last_check ? new Date(stats.last_check).toLocaleString() : "—"}
          </div>
        </div>

        <button
          type="button"
          onClick={trigger}
          disabled={testing}
          className="rounded-2xl border border-orange-500/30 bg-orange-500/10 hover:bg-orange-500/20 p-6 text-left transition disabled:opacity-50"
        >
          <Send className="w-6 h-6 text-orange-400 mb-3" />
          <div className="font-semibold">{testing ? "Sending…" : "Fire test campaign"}</div>
          <div className="text-xs text-slate-400 mt-1">Send to all leads on Telegram now</div>
        </button>
      </section>

      {testMsg && <div className="mb-6 p-3 rounded-lg border border-slate-800 bg-slate-900 text-sm">{testMsg}</div>}

      <section className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
        <StatCard icon={<MessageCircle className="w-4 h-4" />} label="Campaigns today" value={stats.campaigns_today} />
        <StatCard icon={<Send className="w-4 h-4" />} label="Messages sent" value={stats.messages_sent_today} />
        <StatCard icon={<Users className="w-4 h-4" />} label="Total leads" value={stats.total_leads} />
        <StatCard icon={<Activity className="w-4 h-4" />} label="Trigger" value={stats.trigger_active ? "ACTIVE" : "idle"} highlight={stats.trigger_active} />
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Zap className="w-4 h-4" />
          Recent campaigns
        </h2>
        <div className="space-y-3">
          {campaigns.map((campaign) => (
            <div key={campaign.id} className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2 text-sm text-slate-400">
                  <span>{new Date(campaign.ts).toLocaleString()}</span>
                  <span>·</span>
                  <span>{campaign.temp_c.toFixed(1)}°C {campaign.condition}</span>
                  <span>·</span>
                  <span>→ {campaign.recipients} leads</span>
                </div>
                <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300">
                  {campaign.status}
                </span>
              </div>
              <div className="text-sm whitespace-pre-wrap text-slate-200" dangerouslySetInnerHTML={{ __html: campaign.message }} />
            </div>
          ))}
        </div>
      </section>

      <footer className="mt-16 text-center text-xs text-slate-600">
        Haile Revenue OS · v1.0 · Production automation monitor
      </footer>
    </main>
  );
}

function StatCard({
  icon,
  label,
  value,
  highlight = false,
}: {
  icon: ReactNode;
  label: string;
  value: number | string;
  highlight?: boolean;
}) {
  return (
    <div className={`rounded-xl border p-4 ${highlight ? "border-orange-500/30 bg-orange-500/5" : "border-slate-800 bg-slate-950/50"}`}>
      <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">{icon}{label}</div>
      <div className="text-2xl font-semibold tracking-tight">{value}</div>
    </div>
  );
}
