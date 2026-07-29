"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Users, MessageSquare, Gauge, AlertOctagon, FileStack } from "lucide-react";
import type { ChecklistAnalytics } from "@/lib/checklists/types";
import { checklistsApi } from "@/lib/checklists/api";

type Summary = {
  total_users: number;
  total_chats: number;
  avg_confidence: number;
  low_confidence_rate: number;
  top_questions: { question: string; count: number }[];
  total_documents: number;
  total_schemes: number;
};

export default function AdminPage() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [error, setError] = useState("");
  const [checklistAnalytics, setChecklistAnalytics] = useState<ChecklistAnalytics | null>(null);

  useEffect(() => {
    api.adminSummary()
      .then(setSummary)
      .catch(() =>
        setError("Log in as an admin to view analytics (admin@janmitra.gov.in / Admin@123 by default).")
      );
    checklistsApi.analytics().then(setChecklistAnalytics).catch(() => undefined);
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-5 md:px-8 py-14">
      <h1 className="font-display text-3xl font-semibold">Admin Dashboard</h1>
      <p className="text-maroon-dark/60 mt-2">
        Monitor AI usage, response quality, and knowledge gaps.
      </p>

      {error && (
        <div className="mt-6 rounded-card p-4 bg-gold/30 border border-rose/30 text-sm">
          {error}
        </div>
      )}

      {summary && (
        <>
          <div className="grid md:grid-cols-4 gap-5 mt-8">
            <Stat icon={Users} label="Total citizens" value={summary.total_users} />
            <Stat icon={MessageSquare} label="Total conversations" value={summary.total_chats} />
            <Stat icon={Gauge} label="Avg. confidence" value={`${Math.round(summary.avg_confidence * 100)}%`} />
            <Stat icon={AlertOctagon} label="Low-confidence rate" value={`${Math.round(summary.low_confidence_rate * 100)}%`} />
          </div>

          <div className="grid md:grid-cols-2 gap-6 mt-10">
            <div className="rounded-card p-6 bg-white/80 border border-blush/40 shadow-card">
              <h3 className="font-display font-semibold flex items-center gap-2">
                <FileStack size={16} /> Knowledge base
              </h3>
              <p className="text-sm mt-2 text-maroon-dark/60">
                {summary.total_schemes} schemes · {summary.total_documents} uploaded documents indexed
              </p>
            </div>

            <div className="rounded-card p-6 bg-white/80 border border-blush/40 shadow-card">
              <h3 className="font-display font-semibold">Most asked questions</h3>
              <ol className="mt-3 space-y-1.5 text-sm list-decimal list-inside">
                {summary.top_questions.slice(0, 6).map((q, i) => (
                  <li key={i}>{q.question} <span className="text-maroon-dark/40">({q.count})</span></li>
                ))}
                {summary.top_questions.length === 0 && (
                  <p className="text-maroon-dark/50">No queries logged yet.</p>
                )}
              </ol>
            </div>
          </div>

          {checklistAnalytics && (
            <section className="mt-10">
              <h2 className="font-display text-xl font-semibold">Saved checklist analytics</h2>
              <p className="mt-1 text-xs text-maroon-dark/50">
                Aggregate statistics only · active storage: {checklistAnalytics.active_storage_mode}
              </p>
              <div className="mt-5 grid gap-4 md:grid-cols-4">
                <Stat icon={FileStack} label="Saved checklists" value={checklistAnalytics.total_checklists} />
                <Stat icon={Gauge} label="Completion rate" value={`${Math.round(checklistAnalytics.completion_rate * 100)}%`} />
                <Stat icon={AlertOctagon} label="Abandonment rate" value={`${Math.round(checklistAnalytics.abandonment_rate * 100)}%`} />
                <Stat icon={AlertOctagon} label="Outdated checklists" value={checklistAnalytics.outdated_count} />
              </div>
              <div className="mt-6 grid gap-6 md:grid-cols-2">
                <div className="rounded-card border border-blush/40 bg-white/80 p-6 shadow-card">
                  <h3 className="font-display font-semibold">Most saved checklists</h3>
                  <ol className="mt-3 list-decimal space-y-1.5 pl-5 text-sm">
                    {checklistAnalytics.most_saved_checklists.map((item) => (
                      <li key={item.service_id}>{item.service_name} ({item.count})</li>
                    ))}
                  </ol>
                </div>
                <div className="rounded-card border border-blush/40 bg-white/80 p-6 shadow-card">
                  <h3 className="font-display font-semibold">Frequently incomplete steps</h3>
                  <ol className="mt-3 list-decimal space-y-1.5 pl-5 text-sm">
                    {checklistAnalytics.frequently_incomplete_steps.map((item) => (
                      <li key={item.title}>{item.title} ({item.count})</li>
                    ))}
                  </ol>
                  <p className="mt-4 text-xs text-maroon-dark/50">
                    Average completion time: {checklistAnalytics.average_completion_hours} hours ·
                    PostgreSQL: {checklistAnalytics.storage_usage.postgresql} ·
                    SQLite fallback: {checklistAnalytics.storage_usage.sqlite}
                  </p>
                </div>
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}

function Stat({ icon: Icon, label, value }: { icon: React.ElementType; label: string; value: string | number }) {
  return (
    <div className="rounded-card p-5 bg-white/80 border border-blush/40 shadow-card">
      <Icon size={18} className="text-rose" />
      <p className="text-2xl font-display font-semibold mt-2">{value}</p>
      <p className="text-xs text-maroon-dark/50">{label}</p>
    </div>
  );
}
