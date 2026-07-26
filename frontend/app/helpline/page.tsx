"use client";
import { Phone, ShieldAlert, Wheat, Users, HeartHandshake, Baby } from "lucide-react";
import { useLanguage } from "@/lib/i18n";

type HelplineEntry = {
  name: string;
  number: string;
  desc: string;
  icon: React.ElementType;
};

// Real, publicly published Government of India national helpline numbers.
// State-specific ration/PDS toll-free numbers vary; citizens should confirm
// their state's number via the official NFSA/state PDS portal, linked below.
const HELPLINES: HelplineEntry[] = [
  {
    name: "National Food Security Helpline (PDS/Ration)",
    number: "1967 / 1800-XXX-XXXX (state toll-free)",
    desc: "For ration card issues, PDS shop complaints, foodgrain quantity/quality issues. Exact toll-free number varies by state — check your state's Food & Civil Supplies Department portal.",
    icon: Wheat,
  },
  {
    name: "CPGRAMS — Centralized Public Grievance Portal",
    number: "pgportal.gov.in",
    desc: "File and track grievances against any central government department online, free of cost.",
    icon: ShieldAlert,
  },
  {
    name: "PM-KISAN Helpline",
    number: "155261 / 1800-115-526",
    desc: "For PM-KISAN income support scheme queries, payment status, and registration issues.",
    icon: Wheat,
  },
  {
    name: "Women Helpline (All India)",
    number: "181",
    desc: "24x7 helpline for women facing violence or in distress; also assists with welfare scheme access.",
    icon: HeartHandshake,
  },
  {
    name: "Child Helpline",
    number: "1098",
    desc: "24x7 helpline for children in need of care and protection.",
    icon: Baby,
  },
  {
    name: "Senior Citizens Helpline",
    number: "14567 (Elder Line)",
    desc: "National helpline for senior citizens — pension queries, elder abuse, and welfare scheme guidance.",
    icon: Users,
  },
  {
    name: "National Consumer Helpline",
    number: "1915",
    desc: "For consumer grievances, including issues with ration shop dealers or subsidized goods.",
    icon: ShieldAlert,
  },
];

export default function HelplinePage() {
  const { lang } = useLanguage();
  return (
    <div className="max-w-5xl mx-auto px-5 md:px-8 py-14">
      <h1 className="font-display text-3xl font-semibold">
        {lang === "hi" ? "हेल्पलाइन व PDS सहायता" : "Helpline & PDS Help"}
      </h1>
      <p className="text-maroon-dark/60 mt-2 max-w-2xl">
        {lang === "hi"
          ? "राशन, कल्याण योजनाओं और शिकायतों से जुड़ी आधिकारिक हेल्पलाइन नंबर यहां दिए गए हैं। ये सार्वजनिक रूप से प्रकाशित सरकारी हेल्पलाइन हैं।"
          : "Official helpline numbers for ration/PDS issues, welfare scheme queries, and grievances. These are publicly published government helplines."}
      </p>

      <div className="mt-6 rounded-card p-5 bg-gradient-primary text-white">
        <div className="flex items-center gap-2 font-display font-semibold">
          <Wheat size={18} /> {lang === "hi" ? "PDS / राशन सहायता प्राथमिकता" : "PDS / Ration Help — Priority Line"}
        </div>
        <p className="text-sm text-white/80 mt-2">
          {lang === "hi"
            ? "राशन न मिलने, गलत मात्रा, या दुकानदार की शिकायत के लिए राष्ट्रीय खाद्य सुरक्षा हेल्पलाइन 1967 पर कॉल करें, या अपने राज्य के खाद्य विभाग पोर्टल पर शिकायत दर्ज करें।"
            : "For ration not received, wrong quantity, or dealer complaints, call the National Food Security Helpline 1967, or file a complaint on your state Food Department portal."}
        </p>
        <a
          href="https://nfsa.gov.in/"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block mt-3 text-sm font-medium bg-white text-maroon px-4 py-2 rounded-full hover:bg-white/90 transition-colors"
        >
          {lang === "hi" ? "आधिकारिक NFSA पोर्टल खोलें" : "Open official NFSA portal"}
        </a>
      </div>

      <div className="grid md:grid-cols-2 gap-5 mt-8">
        {HELPLINES.map((h) => {
          const Icon = h.icon;
          return (
            <div
              key={h.name}
              className="rounded-card p-5 bg-white/80 border border-blush/40 shadow-card flex gap-4"
            >
              <span className="w-11 h-11 rounded-full bg-blush/30 text-maroon flex items-center justify-center shrink-0">
                <Icon size={18} />
              </span>
              <div>
                <h3 className="font-semibold text-sm">{h.name}</h3>
                <a href={`tel:${h.number.split(" ")[0].replace(/[^0-9]/g, "")}`} className="flex items-center gap-1.5 text-rose font-semibold mt-1 text-sm">
                  <Phone size={14} /> {h.number}
                </a>
                <p className="text-xs text-maroon-dark/60 mt-1.5">{h.desc}</p>
              </div>
            </div>
          );
        })}
      </div>

      <p className="text-xs text-maroon-dark/40 mt-8">
        {lang === "hi"
          ? "नोट: राज्य-विशिष्ट राशन हेल्पलाइन नंबर अलग-अलग होते हैं। कृपया अपने राज्य के खाद्य एवं आपूर्ति विभाग की वेबसाइट पर सटीक नंबर जांचें।"
          : "Note: state-specific ration helpline numbers vary. Please verify the exact number on your state's Food & Civil Supplies Department website."}
      </p>
    </div>
  );
}
