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
  official_url?: string;
  match_reason?: string;
};

export default function SchemeCard({ scheme, index }: { scheme: Scheme; index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.35 }}
      className="premium-card rounded-card p-5 bg-white/80 border border-blush/40 shadow-card"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <span className="text-xs uppercase tracking-wide text-rose font-semibold">
            {scheme.category || "Welfare Scheme"}
          </span>
          <h3 className="font-display text-lg font-semibold mt-1">{scheme.name}</h3>
        </div>
        <span className="text-xs px-2 py-1 rounded-full bg-blush/30 whitespace-nowrap">
          {scheme.state || "All India"}
        </span>
      </div>

      {scheme.description && (
        <p className="text-sm mt-3 text-maroon-dark/80">{scheme.description}</p>
      )}

      {scheme.match_reason && (
        <div className="mt-3 flex items-start gap-2 text-sm text-rose">
          <CheckCircle2 size={16} className="mt-0.5 shrink-0" />
          <span>Why this matched: {scheme.match_reason}</span>
        </div>
      )}

      {scheme.required_documents && scheme.required_documents.length > 0 && (
        <div className="mt-3">
          <p className="text-xs font-semibold text-maroon-dark/60 uppercase tracking-wide">
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
        <div className="mt-4 flex items-center gap-1.5 text-xs text-maroon-dark/50">
          <ExternalLink size={12} />
          Source: {scheme.official_source}
        </div>
      )}

      {scheme.official_url && (
        <a
          href={scheme.official_url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-3 inline-flex items-center gap-1.5 text-sm font-medium text-white bg-maroon px-4 py-2 rounded-full hover:bg-maroon-dark transition-colors"
        >
          Visit official page <ExternalLink size={14} />
        </a>
      )}
    </motion.div>
  );
}
