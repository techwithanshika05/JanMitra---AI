"use client";
import { useState } from "react";
import { api, API_URL } from "@/lib/api";
import { Download, Loader2, FileCheck } from "lucide-react";
import { useLanguage } from "@/lib/i18n";

const SERVICES_EN = [
  { key: "new_ration_card", label: "New Ration Card" },
  { key: "duplicate_ration_card", label: "Duplicate Ration Card" },
  { key: "address_update", label: "Ration Card — Address Update" },
  { key: "add_member", label: "Ration Card — Add Member" },
  { key: "delete_member", label: "Ration Card — Delete Member" },
  { key: "migration_transfer", label: "Ration Card — Migration/Transfer" },
  { key: "pmay_housing", label: "PMAY Housing Assistance" },
  { key: "scholarship", label: "Student Scholarship" },
];

const SERVICES_HI = [
  { key: "new_ration_card", label: "नया राशन कार्ड" },
  { key: "duplicate_ration_card", label: "डुप्लीकेट राशन कार्ड" },
  { key: "address_update", label: "राशन कार्ड — पता अपडेट" },
  { key: "add_member", label: "राशन कार्ड — सदस्य जोड़ें" },
  { key: "delete_member", label: "राशन कार्ड — सदस्य हटाएं" },
  { key: "migration_transfer", label: "राशन कार्ड — स्थानांतरण" },
  { key: "pmay_housing", label: "PMAY आवास सहायता" },
  { key: "scholarship", label: "छात्र छात्रवृत्ति" },
];

type ChecklistResult = {
  documents: string[];
  steps: string[];
  estimated_time: string;
  notes: string;
};

export default function ChecklistPage() {
  const { lang } = useLanguage();
  const hi = lang === "hi";
  const SERVICES = hi ? SERVICES_HI : SERVICES_EN;
  const [service, setService] = useState(SERVICES_EN[0].key);
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
      <h1 className="font-display text-3xl font-semibold">{hi ? "दस्तावेज़ चेकलिस्ट जनरेटर" : "Document Checklist Generator"}</h1>
      <p className="text-maroon-dark/60 mt-2">
        {hi ? "आपको ज़रूरी दस्तावेज़ों व चरणों को जानने के लिए एक सेवा चुनें।" : "Select a service to get exactly which documents and steps you need."}
      </p>

      <div className="mt-8 flex flex-col md:flex-row gap-3">
        <select
          className="flex-1 border border-blush/60 rounded-lg px-4 py-3 text-sm bg-transparent"
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
          className="bg-maroon text-white rounded-lg px-6 py-3 font-medium hover:bg-maroon-dark transition-colors flex items-center justify-center gap-2 disabled:opacity-60"
        >
          {loading ? <Loader2 size={16} className="animate-spin" /> : <FileCheck size={16} />}
          {hi ? "चेकलिस्ट बनाएं" : "Generate checklist"}
        </button>
      </div>

      {result && (
        <div className="mt-10 rounded-card p-6 bg-white/80 border border-blush/40 shadow-card">
          <div className="flex items-center justify-between">
            <h2 className="font-display text-xl font-semibold">
              {SERVICES.find((s) => s.key === service)?.label}
            </h2>
            <button
              onClick={downloadPdf}
              className="text-sm flex items-center gap-1.5 text-rose font-medium hover:underline"
            >
              <Download size={14} /> {hi ? "PDF डाउनलोड करें" : "Download PDF"}
            </button>
          </div>
          <p className="text-xs text-maroon-dark/50 mt-1">
            {hi ? "अनुमानित प्रक्रिया समय: " : "Estimated processing time: "}{result.estimated_time}
          </p>

          <div className="grid md:grid-cols-2 gap-8 mt-6">
            <div>
              <h3 className="text-sm font-semibold uppercase tracking-wide text-rose">{hi ? "आवश्यक दस्तावेज़" : "Required documents"}</h3>
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
              <h3 className="text-sm font-semibold uppercase tracking-wide text-rose">{hi ? "आवेदन के चरण" : "Application steps"}</h3>
              <ol className="mt-3 space-y-2 text-sm list-decimal list-inside">
                {result.steps.map((s) => (
                  <li key={s}>{s}</li>
                ))}
              </ol>
            </div>
          </div>

          <p className="text-xs text-maroon-dark/50 mt-6 border-t border-blush/40 pt-4">
            {result.notes}
          </p>
        </div>
      )}
    </div>
  );
}
