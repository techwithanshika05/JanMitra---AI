"use client";
import Link from "next/link";
import { Search, FileCheck2, MessageCircleQuestion, ShieldCheck } from "lucide-react";

const CARDS = [
  { href: "/schemes", title: "Scheme Finder", desc: "Discover welfare schemes matched to your profile.", icon: Search, color: "bg-maroon" },
  { href: "/chat", title: "Ask JanMitra", desc: "Chat with the AI assistant, sources always cited.", icon: MessageCircleQuestion, color: "bg-rose" },
  { href: "/checklist", title: "Document Checklist", desc: "Generate and download what you need for any process.", icon: FileCheck2, color: "bg-maroon" },
  { href: "/grievance", title: "Grievance Assistant", desc: "File and track a complaint with the right department.", icon: ShieldCheck, color: "bg-maroon-dark" },
];

export default function DashboardPage() {
  return (
    <div className="max-w-7xl mx-auto px-5 md:px-8 py-14">
      <h1 className="font-display text-3xl font-semibold">Citizen Dashboard</h1>
      <p className="text-maroon-dark/60 mt-2">
        Everything you need to navigate welfare and ration services, in one place.
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
        <h3 className="font-display text-lg font-semibold">Responsible AI, by design</h3>
        <p className="text-sm text-white/70 mt-2 max-w-2xl">
          Every JanMitra answer shows a confidence score and its source documents. We never confirm official
          eligibility — final decisions always rest with the concerned government department.
        </p>
      </div>
    </div>
  );
}
