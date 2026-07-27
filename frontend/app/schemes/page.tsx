"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import SchemeCard, { Scheme } from "@/components/SchemeCard";
import { Loader2 } from "lucide-react";

export default function SchemesPage() {
  const [form, setForm] = useState({
    state: "", age: "", gender: "", income: "", occupation: "", category: "", disability: false,
  });
  const [results, setResults] = useState<Scheme[] | null>(null);
  const [loading, setLoading] = useState(false);

  const update = (k: string, v: string | boolean) => setForm((f) => ({ ...f, [k]: v }));

  const search = async () => {
    setLoading(true);
    try {
      const payload = {
        state: form.state || undefined,
        age: form.age ? Number(form.age) : undefined,
        gender: form.gender || undefined,
        income: form.income ? Number(form.income) : undefined,
        occupation: form.occupation || undefined,
        category: form.category || undefined,
        disability: form.disability,
      };
      const res = await api.findSchemes(payload);
      setResults(res);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-5 md:px-8 py-14">
      <h1 className="font-display text-3xl font-semibold">Smart Scheme Finder</h1>
      <p className="text-maroon-dark/60 mt-2 max-w-2xl">
        Tell us a bit about yourself. We'll match schemes and explain exactly why each one fits —
        this is guidance only, not an official eligibility confirmation.
      </p>

      <div className="grid md:grid-cols-3 gap-4 mt-8 rounded-card p-6 bg-white/80 border border-blush/40 shadow-card">
        <Field label="State">
          <input className="input" placeholder="e.g. Uttar Pradesh" value={form.state} onChange={(e) => update("state", e.target.value)} />
        </Field>
        <Field label="Age">
          <input className="input" type="number" placeholder="e.g. 32" value={form.age} onChange={(e) => update("age", e.target.value)} />
        </Field>
        <Field label="Gender">
          <select className="input" value={form.gender} onChange={(e) => update("gender", e.target.value)}>
            <option value="">Any</option>
            <option value="Male">Male</option>
            <option value="Female">Female</option>
            <option value="Other">Other</option>
          </select>
        </Field>
        <Field label="Annual income (₹)">
          <input className="input" type="number" placeholder="e.g. 150000" value={form.income} onChange={(e) => update("income", e.target.value)} />
        </Field>
        <Field label="Occupation">
          <select className="input" value={form.occupation} onChange={(e) => update("occupation", e.target.value)}>
            <option value="">Any</option>
            <option value="farmer">Farmer</option>
            <option value="student">Student</option>
            <option value="laborer">Laborer</option>
            <option value="self-employed">Self-employed</option>
          </select>
        </Field>
        <Field label="Category">
          <select className="input" value={form.category} onChange={(e) => update("category", e.target.value)}>
            <option value="">Any</option>
            <option value="Food Security">Food Security</option>
            <option value="Housing">Housing</option>
            <option value="Education">Education</option>
            <option value="Farmer Welfare">Farmer Welfare</option>
            <option value="Disability Welfare">Disability Welfare</option>
            <option value="Maternal & Child Welfare">Maternal & Child Welfare</option>
          </select>
        </Field>

        <label className="flex items-center gap-2 text-sm md:col-span-3">
          <input type="checkbox" checked={form.disability} onChange={(e) => update("disability", e.target.checked)} />
          I have a disability certificate (80%+)
        </label>

        <button
          onClick={search}
          disabled={loading}
          className="md:col-span-3 mt-2 bg-rose text-white rounded-full py-3 font-medium hover:brightness-110 transition-colors flex items-center justify-center gap-2 disabled:opacity-60"
        >
          {loading && <Loader2 size={16} className="animate-spin" />}
          Find matching schemes
        </button>
      </div>

      {results && (
        <div className="mt-10">
          <h2 className="font-display text-xl font-semibold mb-4">
            {results.length} scheme{results.length !== 1 ? "s" : ""} matched
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
            {results.map((s, i) => (
              <SchemeCard key={s.id} scheme={s} index={i} />
            ))}
          </div>
          {results.length === 0 && (
            <p className="text-sm text-maroon-dark/60">
              No exact matches found. Try widening your criteria, or ask JanMitra AI directly in the chat.
            </p>
          )}
        </div>
      )}

      <style jsx global>{`
        .input {
          @apply w-full border border-blush/60 rounded-lg px-3 py-2 text-sm bg-transparent outline-none focus-visible:border-rose;
        }
      `}</style>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="text-sm">
      <span className="block mb-1 text-maroon-dark/70">{label}</span>
      {children}
    </label>
  );
}
