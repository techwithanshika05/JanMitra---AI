"use client";
import Link from "next/link";
import { Landmark, Phone, Mail, Github } from "lucide-react";
import { useLanguage } from "@/lib/i18n";

const COLUMNS = [
  {
    title: "Product",
    links: [
      { href: "/dashboard", label: "Dashboard" },
      { href: "/schemes", label: "Scheme Finder" },
      { href: "/chat", label: "Ask JanMitra" },
      { href: "/checklist", label: "Checklist" },
    ],
  },
  {
    title: "Support",
    links: [
      { href: "/grievance", label: "Grievance" },
      { href: "/helpline", label: "Helpline" },
      { href: "/documents", label: "My Documents" },
    ],
  },
];

export default function Footer() {
  const { lang } = useLanguage();
  return (
    <footer className="relative mt-24 glow-field overflow-hidden">
      <div className="blob blob-pink w-72 h-72 -top-10 left-10" />
      <div className="blob blob-gold w-72 h-72 bottom-0 right-10" />

      <div className="bg-gradient-primary text-white rounded-t-[40px] mt-10">
        <div className="max-w-7xl mx-auto px-6 md:px-10 py-14 grid md:grid-cols-4 gap-10">
          <div>
            <div className="flex items-center gap-2 font-display text-lg font-bold">
              <span className="w-9 h-9 rounded-full bg-white/15 flex items-center justify-center">
                <Landmark size={16} />
              </span>
              JanMitra AI
            </div>
            <p className="text-sm text-white/70 mt-3 max-w-xs">
              {lang === "hi"
                ? "कल्याण और राशन सेवाओं के लिए एक विश्वसनीय, स्रोत-आधारित सहायक।"
                : "A trustworthy, source-grounded assistant for welfare and ration services."}
            </p>
          </div>

          {COLUMNS.map((col) => (
            <div key={col.title}>
              <h4 className="font-display font-semibold text-sm text-gold">{col.title}</h4>
              <ul className="mt-4 space-y-2.5 text-sm text-white/75">
                {col.links.map((l) => (
                  <li key={l.href}>
                    <Link href={l.href} className="hover:text-white transition-colors">
                      {l.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}

          <div>
            <h4 className="font-display font-semibold text-sm text-gold">
              {lang === "hi" ? "संपर्क" : "Reach us"}
            </h4>
            <ul className="mt-4 space-y-2.5 text-sm text-white/75">
              <li className="flex items-center gap-2">
                <Phone size={14} /> 1967 (PDS Helpline)
              </li>
              <li className="flex items-center gap-2">
                <Mail size={14} /> support@janmitra.gov.in
              </li>
              <li className="flex items-center gap-2">
                <Github size={14} /> Open source project
              </li>
            </ul>
          </div>
        </div>

        <div className="border-t border-white/15 py-5 text-center text-xs text-white/60">
          © {new Date().getFullYear()} JanMitra AI. {lang === "hi" ? "सभी अधिकार सुरक्षित।" : "All rights reserved."}
        </div>
      </div>
    </footer>
  );
}
