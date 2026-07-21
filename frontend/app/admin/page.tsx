"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Users, MessageSquare, Gauge, AlertOctagon, FileStack } from "lucide-react";

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

  useEffect(() => {
    api.adminSummary().then(setSummary).catch(() =>
      setError("Log in as an admin to view analytics (admin@janmitra.gov.in / Admin@123 by default).")
    );
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-5 md:px-8 py-14">
      <h1 className="font-display text-3xl font-semibold">Admin Dashboard</h1>
      <p className="text-indigo-900/60 dark:text-white/50 mt-2">
        Monitor AI usage, response quality, and knowledge gaps.
      </p>

      {error && (
        <div className="mt-6 rounded-card p-4 bg-marigold-50 dark:bg-white/5 border border-marigold/30 text-sm">
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
            <div className="rounded-card p-6 bg-white/80 dark:bg-white/5 border border-indigo-50 dark:border-white/10 shadow-card">
              <h3 className="font-display font-semibold flex items-center gap-2">
                <FileStack size={16} /> Knowledge base
              </h3>
              <p className="text-sm mt-2 text-indigo-900/60 dark:text-white/50">
                {summary.total_schemes} schemes · {summary.total_documents} uploaded documents indexed
              </p>
            </div>

            <div className="rounded-card p-6 bg-white/80 dark:bg-white/5 border border-indigo-50 dark:border-white/10 shadow-card">
              <h3 className="font-display font-semibold">Most asked questions</h3>
              <ol className="mt-3 space-y-1.5 text-sm list-decimal list-inside">
                {summary.top_questions.slice(0, 6).map((q, i) => (
                  <li key={i}>{q.question} <span className="text-indigo-900/40 dark:text-white/30">({q.count})</span></li>
                ))}
                {summary.top_questions.length === 0 && (
                  <p className="text-indigo-900/50 dark:text-white/40">No queries logged yet.</p>
                )}
              </ol>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function Stat({ icon: Icon, label, value }: { icon: React.ElementType; label: string; value: string | number }) {
  return (
    <div className="rounded-card p-5 bg-white/80 dark:bg-white/5 border border-indigo-50 dark:border-white/10 shadow-card">
      <Icon size={18} className="text-marigold" />
      <p className="text-2xl font-display font-semibold mt-2">{value}</p>
      <p className="text-xs text-indigo-900/50 dark:text-white/40">{label}</p>
    </div>
  );
}
