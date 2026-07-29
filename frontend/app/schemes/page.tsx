"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import SchemeCard, { Scheme } from "@/components/SchemeCard";
import { Loader2 } from "lucide-react";
import { useLanguage } from "@/lib/i18n";

export default function SchemesPage() {
  const { lang } = useLanguage();
  const hi = lang === "hi";
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
      <h1 className="font-display text-3xl font-semibold">{hi ? "स्मार्ट योजना खोजकर्ता" : "Smart Scheme Finder"}</h1>
      <p className="text-maroon-dark/60 mt-2 max-w-2xl">
        {hi
          ? "अपने बारे में थोड़ा बताएं। हम योजनाओं का मिलान करेंगे और बताएंगे कि हर एक क्यों फिट बैठती है — यह केवल मार्गदर्शन है, आधिकारिक पात्रता की पुष्टि नहीं।"
          : "Tell us a bit about yourself. We'll match schemes and explain exactly why each one fits — this is guidance only, not an official eligibility confirmation."}
      </p>

      <div className="grid md:grid-cols-3 gap-4 mt-8 rounded-card p-6 bg-white/80 border border-blush/40 shadow-card">
        <Field label={hi ? "राज्य" : "State"}>
          <input className="input" placeholder={hi ? "जैसे उत्तर प्रदेश" : "e.g. Uttar Pradesh"} value={form.state} onChange={(e) => update("state", e.target.value)} />
        </Field>
        <Field label={hi ? "आयु" : "Age"}>
          <input className="input" type="number" placeholder={hi ? "जैसे 32" : "e.g. 32"} value={form.age} onChange={(e) => update("age", e.target.value)} />
        </Field>
        <Field label={hi ? "लिंग" : "Gender"}>
          <select className="input" value={form.gender} onChange={(e) => update("gender", e.target.value)}>
            <option value="">{hi ? "कोई भी" : "Any"}</option>
            <option value="Male">{hi ? "पुरुष" : "Male"}</option>
            <option value="Female">{hi ? "महिला" : "Female"}</option>
            <option value="Other">{hi ? "अन्य" : "Other"}</option>
          </select>
        </Field>
        <Field label={hi ? "वार्षिक आय (₹)" : "Annual income (₹)"}>
          <input className="input" type="number" placeholder={hi ? "जैसे 150000" : "e.g. 150000"} value={form.income} onChange={(e) => update("income", e.target.value)} />
        </Field>
        <Field label={hi ? "व्यवसाय" : "Occupation"}>
          <select className="input" value={form.occupation} onChange={(e) => update("occupation", e.target.value)}>
            <option value="">{hi ? "कोई भी" : "Any"}</option>
            <option value="farmer">{hi ? "किसान" : "Farmer"}</option>
            <option value="student">{hi ? "छात्र" : "Student"}</option>
            <option value="laborer">{hi ? "मज़दूर" : "Laborer"}</option>
            <option value="self-employed">{hi ? "स्व-नियोजित" : "Self-employed"}</option>
          </select>
        </Field>
        <Field label={hi ? "श्रेणी" : "Category"}>
          <select className="input" value={form.category} onChange={(e) => update("category", e.target.value)}>
            <option value="">{hi ? "कोई भी" : "Any"}</option>
            <option value="Food Security">{hi ? "खाद्य सुरक्षा" : "Food Security"}</option>
            <option value="Housing">{hi ? "आवास" : "Housing"}</option>
            <option value="Education">{hi ? "शिक्षा" : "Education"}</option>
            <option value="Farmer Welfare">{hi ? "किसान कल्याण" : "Farmer Welfare"}</option>
            <option value="Disability Welfare">{hi ? "दिव्यांग कल्याण" : "Disability Welfare"}</option>
            <option value="Maternal & Child Welfare">{hi ? "मातृ एवं शिशु कल्याण" : "Maternal & Child Welfare"}</option>
          </select>
        </Field>

        <label className="flex items-center gap-2 text-sm md:col-span-3">
          <input type="checkbox" checked={form.disability} onChange={(e) => update("disability", e.target.checked)} />
          {hi ? "मेरे पास दिव्यांगता प्रमाण पत्र है (80%+)" : "I have a disability certificate (80%+)"}
        </label>

        <button
          onClick={search}
          disabled={loading}
          className="md:col-span-3 mt-2 bg-rose text-white rounded-full py-3 font-medium hover:brightness-110 transition-colors flex items-center justify-center gap-2 disabled:opacity-60"
        >
          {loading && <Loader2 size={16} className="animate-spin" />}
          {hi ? "मिलती-जुलती योजनाएं खोजें" : "Find matching schemes"}
        </button>
      </div>

      {results && (
        <div className="mt-10">
          <h2 className="font-display text-xl font-semibold mb-4">
            {hi ? `${results.length} योजना${results.length !== 1 ? "एं" : ""} मेल खाई` : `${results.length} scheme${results.length !== 1 ? "s" : ""} matched`}
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
            {results.map((s, i) => (
              <SchemeCard key={s.id} scheme={s} index={i} />
            ))}
          </div>
          {results.length === 0 && (
            <p className="text-sm text-maroon-dark/60">
              {hi
                ? "कोई सटीक मेल नहीं मिला। अपने मानदंड व्यापक करें, या सीधे चैट में JanMitra AI से पूछें।"
                : "No exact matches found. Try widening your criteria, or ask JanMitra AI directly in the chat."}
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
