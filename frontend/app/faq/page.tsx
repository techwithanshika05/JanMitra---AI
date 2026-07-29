"use client";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Search, MessageCircleQuestion } from "lucide-react";
import { api } from "@/lib/api";
import FAQAccordion, { FAQItem } from "@/components/FAQAccordion";
import { useLanguage } from "@/lib/i18n";

const CATEGORIES_EN = [
  { key: "", label: "All" },
  { key: "ration", label: "Ration" },
  { key: "scheme", label: "Schemes" },
  { key: "grievance", label: "Grievance" },
  { key: "general", label: "General" },
];

const CATEGORIES_HI = [
  { key: "", label: "सभी" },
  { key: "ration", label: "राशन" },
  { key: "scheme", label: "योजनाएं" },
  { key: "grievance", label: "शिकायत" },
  { key: "general", label: "सामान्य" },
];

export default function FAQPage() {
  const { lang } = useLanguage();
  const hi = lang === "hi";
  const CATEGORIES = hi ? CATEGORIES_HI : CATEGORIES_EN;
  const [faqs, setFaqs] = useState<FAQItem[]>([]);
  const [category, setCategory] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .listFaqs(category ? { category } : undefined)
      .then((data) => setFaqs(data.map((d: any) => ({ question: d.question, answer: d.answer }))))
      .catch(() => setFaqs([]))
      .finally(() => setLoading(false));
  }, [category]);

  const filtered = faqs.filter(
    (f) =>
      f.question.toLowerCase().includes(search.toLowerCase()) ||
      f.answer.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="max-w-3xl mx-auto px-5 md:px-8 py-14">
      <div className="flex items-center gap-2 text-rose">
        <MessageCircleQuestion size={20} />
        <span className="text-xs font-bold uppercase tracking-wide">{hi ? "FAQ सहायक" : "FAQ Assistant"}</span>
      </div>
      <h1 className="font-display text-3xl font-bold mt-2 text-maroon-dark">{hi ? "अक्सर पूछे जाने वाले प्रश्न" : "Frequently Asked Questions"}</h1>
      <p className="text-maroon-dark/60 mt-2">
        {hi
          ? "राशन कार्ड, कल्याण योजनाओं और शिकायतों से जुड़े सामान्य सवाल देखें।"
          : "Browse common questions about ration cards, welfare schemes, and grievances."}
      </p>

      <div className="mt-6 flex flex-col md:flex-row gap-3">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-maroon-dark/40" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={hi ? "FAQ खोजें..." : "Search FAQs..."}
            className="w-full pl-9 pr-4 py-2.5 rounded-pill border border-blush/60 text-sm outline-none focus-visible:border-rose bg-white"
          />
        </div>
        <div className="flex gap-2 flex-wrap">
          {CATEGORIES.map((c) => (
            <button
              key={c.key}
              onClick={() => setCategory(c.key)}
              className={`px-4 py-2 rounded-pill text-xs font-semibold transition-colors ${
                category === c.key ? "bg-maroon text-white" : "bg-blush/40 text-maroon-dark hover:bg-blush/60"
              }`}
            >
              {c.label}
            </button>
          ))}
        </div>
      </div>

      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3 }} className="mt-8">
        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="skeleton h-16 w-full" />
            ))}
          </div>
        ) : filtered.length > 0 ? (
          <FAQAccordion items={filtered} />
        ) : (
          <p className="text-sm text-maroon-dark/50 text-center py-10">
            {hi
              ? "कोई FAQ नहीं मिला। कोई और खोज या श्रेणी आज़माएं, या सीधे चैट में JanMitra AI से पूछें।"
              : "No FAQs found. Try a different search or category, or ask JanMitra AI directly in chat."}
          </p>
        )}
      </motion.div>
    </div>
  );
}
