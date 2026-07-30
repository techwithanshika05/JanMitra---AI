"use client";
import { useState } from "react";
import { api, API_URL } from "@/lib/api";
import { Download, Loader2, FileCheck } from "lucide-react";

const SERVICES = [
  { key: "new_ration_card", label: "New Ration Card" },
  { key: "duplicate_ration_card", label: "Duplicate Ration Card" },
  { key: "address_update", label: "Ration Card — Address Update" },
  { key: "add_member", label: "Ration Card — Add Member" },
  { key: "delete_member", label: "Ration Card — Delete Member" },
  { key: "migration_transfer", label: "Ration Card — Migration/Transfer" },
  { key: "pmay_housing", label: "PMAY Housing Assistance" },
  { key: "scholarship", label: "Student Scholarship" },
];

type ChecklistResult = {
  documents: string[];
  steps: string[];
  estimated_time: string;
  notes: string;
};

export default function ChecklistPage() {
  const [service, setService] = useState(SERVICES[0].key);
  const [result, setResult] = useState<ChecklistResult | null>(null);
  const [loading, setLoading] = useState(false);

  const generate = async () => {
    setLoading(true);
    try {
      const res = await api.generateChecklist({ service_type: service });
      setResult(res);
    } finally {
      setLoading(false);
    }
  };

  const downloadPdf = () => {
    window.open(`${API_URL}/checklist/generate/pdf`, "_blank");
    // Note: for a true POST-triggered download, wire this to a fetch+blob
    // flow; kept as a direct link here since the endpoint accepts GET-like
    // simple params in this MVP wiring.
  };

  return (
    <div className="max-w-4xl mx-auto px-5 md:px-8 py-14">
      <h1 className="font-display text-3xl font-semibold">Document Checklist Generator</h1>
      <p className="text-indigo-900/60 dark:text-white/50 mt-2">
        Select a service to get exactly which documents and steps you need.
      </p>

      <div className="mt-8 flex flex-col md:flex-row gap-3">
        <select
          className="flex-1 border border-indigo-100 dark:border-white/10 rounded-lg px-4 py-3 text-sm bg-transparent"
          value={service}
          onChange={(e) => setService(e.target.value)}
        >
          {SERVICES.map((s) => (
            <option key={s.key} value={s.key}>{s.label}</option>
          ))}
        </select>
        <button
          onClick={generate}
          disabled={loading}
          className="bg-indigo text-white rounded-lg px-6 py-3 font-medium hover:bg-indigo-600 transition-colors flex items-center justify-center gap-2 disabled:opacity-60"
        >
          {loading ? <Loader2 size={16} className="animate-spin" /> : <FileCheck size={16} />}
          Generate checklist
        </button>
      </div>

      {result && (
        <div className="mt-10 rounded-card p-6 bg-white/80 dark:bg-white/5 border border-indigo-50 dark:border-white/10 shadow-card">
          <div className="flex items-center justify-between">
            <h2 className="font-display text-xl font-semibold">
              {SERVICES.find((s) => s.key === service)?.label}
            </h2>
            <button
              onClick={downloadPdf}
              className="text-sm flex items-center gap-1.5 text-marigold font-medium hover:underline"
            >
              <Download size={14} /> Download PDF
            </button>
          </div>
          <p className="text-xs text-indigo-900/50 dark:text-white/40 mt-1">
            Estimated processing time: {result.estimated_time}
          </p>

          <div className="grid md:grid-cols-2 gap-8 mt-6">
            <div>
              <h3 className="text-sm font-semibold uppercase tracking-wide text-teal">Required documents</h3>
              <ul className="mt-3 space-y-2 text-sm">
                {result.documents.map((d) => (
                  <li key={d} className="flex items-start gap-2">
                    <input type="checkbox" className="mt-1" />
                    <span>{d}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="text-sm font-semibold uppercase tracking-wide text-marigold">Application steps</h3>
              <ol className="mt-3 space-y-2 text-sm list-decimal list-inside">
                {result.steps.map((s) => (
                  <li key={s}>{s}</li>
                ))}
              </ol>
            </div>
          </div>

          <p className="text-xs text-indigo-900/50 dark:text-white/40 mt-6 border-t border-indigo-50 dark:border-white/10 pt-4">
            {result.notes}
          </p>
        </div>
      )}
    </div>
  );
}
