"use client";

import { useEffect, useState } from "react";
import { api, Stats, Campaign } from "@/lib/api";
import { Sun, CloudRain, Wind, Zap, Send, Activity, Users, MessageCircle, RefreshCw } from "lucide-react";

function TempIcon({ temp }: { temp: number | null }) {
  if (temp == null) return <CloudRain className="w-6 h-6" />;
  if (temp >= 30) return <Sun className="w-6 h-6 text-orange-400" />;
  if (temp >= 28) return <Sun className="w-6 h-6 text-yellow-400" />;
  return <CloudRain className="w-6 h-6 text-slate-400" />;
}

export default function Home() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [testing, setTesting] = useState(false);
  const [testMsg, setTestMsg] = useState<string>("");

  const refresh = async () => {
    try {
      const [s, c] = await Promise.all([api.stats(), api.campaigns()]);
      setStats(s);
      setCampaigns(c);
    } catch (e) {
      // API might not be configured yet
    }
  };

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 30_000);
    return () => clearInterval(t);
  }, []);

  const trigger = async () => {
    setTesting(true);
    setTestMsg("");
    try {
      const r = await api.test();
      setTestMsg(`✅ Sent! Temp ${r.temp_c}°C, ${r.recipients} leads reached, msg id ${r.message_id ?? "n/a"}`);
      refresh();
    } catch (e) {
      setTestMsg(`❌ ${(e as Error).message}`);
    }
    setTesting(false);
  };

  return (
    <main className="min-h-screen p-6 md:p-10 max-w-6xl mx-auto">
      {/* Header */}
      <header className="flex items-center justify-between mb-10">
        <div>
          <h1 className="text-3xl md:text-4xl font-bold tracking-tight">Haile Revenue OS</h1>
          <p className="text-sm text-slate-400 mt-1">Autonomous AI Revenue System · Adama, Ethiopia</p>
        </div>
        <button onClick={refresh} className="p-2 rounded-lg border border-slate-800 hover:bg-slate-900">
          <RefreshCw className="w-4 h-4" />
        </button>
      </header>

      {/* Top row: live weather + status */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="md:col-span-2 rounded-2xl border border-slate-800 bg-gradient-to-br from-slate-900 to-black p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <TempIcon temp={stats?.temp_c ?? null} />
              <span className="text-sm text-slate-400">Adama live</span>
            </div>
            {stats?.trigger_active && (
              <span className="px-2 py-1 text-xs font-semibold rounded-full bg-orange-500/20 text-orange-300 border border-orange-500/30">
                🔥 TRIGGER ACTIVE
              </span>
            )}
          </div>
          <div className="mt-4 flex items-end gap-2">
            <span className="text-7xl font-bold tracking-tighter">
              {stats?.temp_c != null ? Math.round(stats.temp_c) : "—"}
            </span>
            <span className="text-2xl text-slate-400 mb-2">°C</span>
          </div>
          <div className="mt-1 text-slate-300 capitalize">{stats?.condition ?? "—"}</div>
          <div className="mt-4 text-xs text-slate-500">
            Last check: {stats?.last_check ? new Date(stats.last_check).toLocaleString() : "—"}
          </div>
        </div>

        <button
          onClick={trigger}
          disabled={testing}
          className="rounded-2xl border border-orange-500/30 bg-orange-500/10 hover:bg-orange-500/20 p-6 text-left transition disabled:opacity-50"
        >
          <Send className="w-6 h-6 text-orange-400 mb-3" />
          <div className="font-semibold">{testing ? "Sending…" : "Fire test campaign"}</div>
          <div className="text-xs text-slate-400 mt-1">Send to all leads on Telegram now</div>
        </button>
      </section>

      {testMsg && (
        <div className="mb-6 p-3 rounded-lg border border-slate-800 bg-slate-900 text-sm">{testMsg}</div>
      )}

      {/* Stats grid */}
      <section className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
        <StatCard icon={<MessageCircle className="w-4 h-4" />} label="Campaigns today" value={stats?.campaigns_today ?? 0} />
        <StatCard icon={<Send className="w-4 h-4" />} label="Messages sent" value={stats?.messages_sent_today ?? 0} />
        <StatCard icon={<Users className="w-4 h-4" />} label="Total leads" value={stats?.total_leads ?? 0} />
        <StatCard icon={<Activity className="w-4 h-4" />} label="Trigger" value={stats?.trigger_active ? "ACTIVE" : "idle"} highlight={stats?.trigger_active} />
      </section>

      {/* Campaign history */}
      <section>
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Zap className="w-4 h-4" />
          Recent campaigns
        </h2>
        <div className="space-y-3">
          {campaigns.length === 0 && (
            <div className="text-slate-500 text-sm p-6 rounded-xl border border-dashed border-slate-800 text-center">
              No campaigns yet. Wait for a 28°C day, or hit the test button above.
            </div>
          )}
          {campaigns.map((c) => (
            <div key={c.id} className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2 text-sm text-slate-400">
                  <span>{new Date(c.ts).toLocaleString()}</span>
                  <span>·</span>
                  <span>{c.temp_c.toFixed(1)}°C {c.condition}</span>
                  <span>·</span>
                  <span>→ {c.recipients} leads</span>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full ${c.status === "sent" ? "bg-emerald-500/20 text-emerald-300" : "bg-slate-700 text-slate-300"}`}>
                  {c.status}
                </span>
              </div>
              <div className="text-sm whitespace-pre-wrap text-slate-200" dangerouslySetInnerHTML={{ __html: c.message }} />
            </div>
          ))}
        </div>
      </section>

      <footer className="mt-16 text-center text-xs text-slate-600">
        Haile Revenue OS · v0.1 · 60-second autonomous weather → revenue loop
      </footer>
    </main>
  );
}

function StatCard({
  icon,
  label,
  value,
  highlight,
}: {
  icon: React.ReactNode;
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
