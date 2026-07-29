"use client";
import Link from "next/link";
import { Search, FileCheck2, MessageCircleQuestion, ShieldCheck } from "lucide-react";
import { useLanguage } from "@/lib/i18n";

const CARDS_EN = [
  { href: "/schemes", title: "Scheme Finder", desc: "Discover welfare schemes matched to your profile.", icon: Search, color: "bg-maroon" },
  { href: "/chat", title: "Ask JanMitra", desc: "Chat with the AI assistant, sources always cited.", icon: MessageCircleQuestion, color: "bg-rose" },
  { href: "/checklist", title: "Document Checklist", desc: "Generate and download what you need for any process.", icon: FileCheck2, color: "bg-maroon" },
  { href: "/grievance", title: "Grievance Assistant", desc: "File and track a complaint with the right department.", icon: ShieldCheck, color: "bg-maroon-dark" },
];

const CARDS_HI = [
  { href: "/schemes", title: "योजना खोजकर्ता", desc: "अपनी प्रोफाइल से मेल खाती कल्याण योजनाएं खोजें।", icon: Search, color: "bg-maroon" },
  { href: "/chat", title: "JanMitra से पूछें", desc: "AI सहायक से चैट करें, स्रोत हमेशा बताए जाते हैं।", icon: MessageCircleQuestion, color: "bg-rose" },
  { href: "/checklist", title: "दस्तावेज़ चेकलिस्ट", desc: "किसी भी प्रक्रिया के लिए ज़रूरी चीज़ें बनाएं और डाउनलोड करें।", icon: FileCheck2, color: "bg-maroon" },
  { href: "/grievance", title: "शिकायत सहायक", desc: "सही विभाग के साथ शिकायत दर्ज करें और ट्रैक करें।", icon: ShieldCheck, color: "bg-maroon-dark" },
];

export default function DashboardPage() {
  const { lang } = useLanguage();
  const hi = lang === "hi";
  const CARDS = hi ? CARDS_HI : CARDS_EN;
  return (
    <div className="max-w-7xl mx-auto px-5 md:px-8 py-14">
      <h1 className="font-display text-3xl font-semibold">{hi ? "नागरिक डैशबोर्ड" : "Citizen Dashboard"}</h1>
      <p className="text-maroon-dark/60 mt-2">
        {hi
          ? "कल्याण और राशन सेवाओं में मदद के लिए हर ज़रूरी चीज़, एक ही जगह पर।"
          : "Everything you need to navigate welfare and ration services, in one place."}
      </p>

      <div className="grid md:grid-cols-2 gap-6 mt-10">
        {CARDS.map((c) => {
          const Icon = c.icon;
          return (
            <Link
              key={c.href}
              href={c.href}
              className="rounded-card p-6 flex items-start gap-4 bg-white/80 border border-blush/40 shadow-card hover:-translate-y-1 transition-transform"
            >
              <span className={`w-11 h-11 rounded-full ${c.color} text-white flex items-center justify-center shrink-0`}>
                <Icon size={18} />
              </span>
              <div>
                <h3 className="font-display text-lg font-semibold">{c.title}</h3>
                <p className="text-sm text-maroon-dark/60 mt-1">{c.desc}</p>
              </div>
            </Link>
          );
        })}
      </div>

      <div className="mt-12 rounded-card p-6 bg-gradient-primary text-white">
        <h3 className="font-display text-lg font-semibold">{hi ? "जिम्मेदार AI, शुरू से ही" : "Responsible AI, by design"}</h3>
        <p className="text-sm text-white/70 mt-2 max-w-2xl">
          {hi
            ? "हर JanMitra जवाब एक विश्वास स्तर और अपने स्रोत दस्तावेज़ दिखाता है। हम कभी भी आधिकारिक पात्रता की पुष्टि नहीं करते — अंतिम निर्णय हमेशा संबंधित सरकारी विभाग के पास रहता है।"
            : "Every JanMitra answer shows a confidence score and its source documents. We never confirm official eligibility — final decisions always rest with the concerned government department."}
        </p>
      </div>
    </div>
  );
}
