"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import { Loader2, Building2, ListChecks, ArrowUpCircle } from "lucide-react";

type GrievanceResult = {
  department: string;
  steps: string[];
  expected_resolution_days: number;
  escalation_path: string[];
  reference_note: string;
};

export default function GrievancePage() {
  const [category, setCategory] = useState("ration");
  const [description, setDescription] = useState("");
  const [result, setResult] = useState<GrievanceResult | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    if (!description.trim()) return;
    setLoading(true);
    try {
      const res = await api.guideGrievance({ category, description });
      setResult(res);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-5 md:px-8 py-14">
      <h1 className="font-display text-3xl font-semibold">Grievance Assistant</h1>
      <p className="text-maroon-dark/60 mt-2">
        Describe the issue — we'll point you to the right department and the exact escalation path.
      </p>

      <div className="mt-8 space-y-4">
        <select
          className="w-full border border-blush/60 rounded-lg px-4 py-3 text-sm bg-transparent"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        >
          <option value="ration">Ration / PDS issue</option>
          <option value="scheme">Welfare scheme issue</option>
          <option value="pension">Pension issue</option>
          <option value="other">Other</option>
        </select>
        <textarea
          className="w-full border border-blush/60 rounded-lg px-4 py-3 text-sm bg-transparent min-h-[120px]"
          placeholder="Describe what happened — e.g. 'My ration shop denied entitled quantity this month.'"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
        <button
          onClick={submit}
          disabled={loading}
          className="bg-rose text-white rounded-full px-6 py-3 font-medium hover:brightness-110 transition-colors flex items-center gap-2 disabled:opacity-60"
        >
          {loading && <Loader2 size={16} className="animate-spin" />}
          Get guidance
        </button>
      </div>

      {result && (
        <div className="mt-10 space-y-6">
          <div className="rounded-card p-5 bg-white/80 border border-blush/40 shadow-card">
            <div className="flex items-center gap-2 text-rose font-semibold">
              <Building2 size={16} /> Department to contact
            </div>
            <p className="mt-1 text-sm">{result.department}</p>
            <p className="text-xs text-maroon-dark/50 mt-1">
              Expected resolution: ~{result.expected_resolution_days} days
            </p>
          </div>

          <div className="rounded-card p-5 bg-white/80 border border-blush/40 shadow-card">
            <div className="flex items-center gap-2 text-rose font-semibold">
              <ListChecks size={16} /> Steps to file
            </div>
            <ol className="mt-3 space-y-1.5 text-sm list-decimal list-inside">
              {result.steps.map((s) => <li key={s}>{s}</li>)}
            </ol>
          </div>

          <div className="rounded-card p-5 bg-white/80 border border-blush/40 shadow-card">
            <div className="flex items-center gap-2 text-maroon font-semibold">
              <ArrowUpCircle size={16} /> If unresolved: escalation path
            </div>
            <ol className="mt-3 space-y-1.5 text-sm list-decimal list-inside">
              {result.escalation_path.map((s) => <li key={s}>{s}</li>)}
            </ol>
          </div>

          <p className="text-xs text-maroon-dark/50">{result.reference_note}</p>
        </div>
      )}
    </div>
  );
}
