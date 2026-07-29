"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Users, MessageSquare, Gauge, AlertOctagon, FileStack } from "lucide-react";
import { useLanguage } from "@/lib/i18n";

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
  const { lang } = useLanguage();
  const hi = lang === "hi";
  const [summary, setSummary] = useState<Summary | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.adminSummary().then(setSummary).catch(() =>
      setError(
        hi
          ? "एनालिटिक्स देखने के लिए एडमिन के रूप में लॉगिन करें (डिफ़ॉल्ट: admin@janmitra.gov.in / Admin@123)।"
          : "Log in as an admin to view analytics (admin@janmitra.gov.in / Admin@123 by default)."
      )
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-5 md:px-8 py-14">
      <h1 className="font-display text-3xl font-semibold">{hi ? "एडमिन डैशबोर्ड" : "Admin Dashboard"}</h1>
      <p className="text-maroon-dark/60 mt-2">
        {hi ? "AI उपयोग, जवाब गुणवत्ता, और नॉलेज गैप की निगरानी करें।" : "Monitor AI usage, response quality, and knowledge gaps."}
      </p>

      {error && (
        <div className="mt-6 rounded-card p-4 bg-gold/30 border border-rose/30 text-sm">
          {error}
        </div>
      )}

      {summary && (
        <>
          <div className="grid md:grid-cols-4 gap-5 mt-8">
            <Stat icon={Users} label={hi ? "कुल नागरिक" : "Total citizens"} value={summary.total_users} />
            <Stat icon={MessageSquare} label={hi ? "कुल बातचीत" : "Total conversations"} value={summary.total_chats} />
            <Stat icon={Gauge} label={hi ? "औसत विश्वास" : "Avg. confidence"} value={`${Math.round(summary.avg_confidence * 100)}%`} />
            <Stat icon={AlertOctagon} label={hi ? "निम्न-विश्वास दर" : "Low-confidence rate"} value={`${Math.round(summary.low_confidence_rate * 100)}%`} />
          </div>

          <div className="grid md:grid-cols-2 gap-6 mt-10">
            <div className="rounded-card p-6 bg-white/80 border border-blush/40 shadow-card">
              <h3 className="font-display font-semibold flex items-center gap-2">
                <FileStack size={16} /> {hi ? "नॉलेज बेस" : "Knowledge base"}
              </h3>
              <p className="text-sm mt-2 text-maroon-dark/60">
                {hi
                  ? `${summary.total_schemes} योजनाएं · ${summary.total_documents} अपलोड किए दस्तावेज़ इंडेक्स किए गए`
                  : `${summary.total_schemes} schemes · ${summary.total_documents} uploaded documents indexed`}
              </p>
            </div>

            <div className="rounded-card p-6 bg-white/80 border border-blush/40 shadow-card">
              <h3 className="font-display font-semibold">{hi ? "सबसे ज़्यादा पूछे गए सवाल" : "Most asked questions"}</h3>
              <ol className="mt-3 space-y-1.5 text-sm list-decimal list-inside">
                {summary.top_questions.slice(0, 6).map((q, i) => (
                  <li key={i}>{q.question} <span className="text-maroon-dark/40">({q.count})</span></li>
                ))}
                {summary.top_questions.length === 0 && (
                  <p className="text-maroon-dark/50">{hi ? "अभी तक कोई प्रश्न लॉग नहीं किया गया।" : "No queries logged yet."}</p>
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
    <div className="rounded-card p-5 bg-white/80 border border-blush/40 shadow-card">
      <Icon size={18} className="text-rose" />
      <p className="text-2xl font-display font-semibold mt-2">{value}</p>
      <p className="text-xs text-maroon-dark/50">{label}</p>
    </div>
  );
}
