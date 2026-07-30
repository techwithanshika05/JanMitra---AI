"use client";
import { motion } from "framer-motion";
import { CheckCircle2, ExternalLink } from "lucide-react";

export type Scheme = {
  id: number;
  name: string;
  category?: string;
  state?: string;
  description?: string;
  benefits?: string;
  required_documents?: string[];
  official_source?: string;
  match_reason?: string;
};

export default function SchemeCard({ scheme, index }: { scheme: Scheme; index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.35 }}
      className="rounded-card p-5 bg-white/80 dark:bg-white/5 border border-indigo-50 dark:border-white/10 shadow-card"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <span className="text-xs uppercase tracking-wide text-teal font-semibold">
            {scheme.category || "Welfare Scheme"}
          </span>
          <h3 className="font-display text-lg font-semibold mt-1">{scheme.name}</h3>
        </div>
        <span className="text-xs px-2 py-1 rounded-full bg-indigo-50 dark:bg-white/10 whitespace-nowrap">
          {scheme.state || "All India"}
        </span>
      </div>

      {scheme.description && (
        <p className="text-sm mt-3 text-indigo-900/80 dark:text-white/70">{scheme.description}</p>
      )}

      {scheme.match_reason && (
        <div className="mt-3 flex items-start gap-2 text-sm text-teal">
          <CheckCircle2 size={16} className="mt-0.5 shrink-0" />
          <span>Why this matched: {scheme.match_reason}</span>
        </div>
      )}

      {scheme.required_documents && scheme.required_documents.length > 0 && (
        <div className="mt-3">
          <p className="text-xs font-semibold text-indigo-900/60 dark:text-white/50 uppercase tracking-wide">
            Documents needed
          </p>
          <ul className="text-sm mt-1 list-disc list-inside space-y-0.5">
            {scheme.required_documents.slice(0, 3).map((d) => (
              <li key={d}>{d}</li>
            ))}
          </ul>
        </div>
      )}

      {scheme.official_source && (
        <div className="mt-4 flex items-center gap-1.5 text-xs text-indigo-900/50 dark:text-white/40">
          <ExternalLink size={12} />
          Source: {scheme.official_source}
        </div>
      )}
    </motion.div>
  );
}
