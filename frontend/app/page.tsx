"use client";
import Link from "next/link";
import { motion } from "framer-motion";
import { Search, FileCheck2, MessageCircleQuestion, ShieldCheck, ArrowRight } from "lucide-react";
import { useLanguage } from "@/lib/i18n";

const JOURNEY = [
  { title: "Discover", desc: "Find schemes you may qualify for based on your profile.", icon: Search },
  { title: "Understand", desc: "Get plain-language explanations of PDS & welfare processes.", icon: MessageCircleQuestion },
  { title: "Prepare", desc: "Generate a document checklist, downloadable as PDF.", icon: FileCheck2 },
  { title: "Resolve", desc: "File and track grievances with a clear escalation path.", icon: ShieldCheck },
];

export default function LandingPage() {
  const { t } = useLanguage();
  return (
    <div>
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-5 md:px-8 pt-20 pb-24 grid md:grid-cols-2 gap-12 items-center">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <span className="inline-block text-xs font-semibold tracking-wide uppercase text-teal bg-teal-50 dark:bg-teal/10 px-3 py-1 rounded-full">
              {t("hero.tag")}
            </span>
            <h1 className="font-display text-4xl md:text-5xl font-semibold mt-5 leading-tight">
              {t("hero.title1")} <span className="text-marigold">{t("hero.title2")}</span> {t("hero.title3")}
            </h1>
            <p className="mt-5 text-indigo-900/70 dark:text-white/60 text-lg max-w-xl">
              {t("hero.desc")}
            </p>
            <div className="mt-8 flex flex-wrap gap-4">
              <Link
                href="/chat"
                className="inline-flex items-center gap-2 bg-indigo text-white px-6 py-3 rounded-full font-medium hover:bg-indigo-600 transition-colors"
              >
                {t("hero.cta1")} <ArrowRight size={16} />
              </Link>
              <Link
                href="/schemes"
                className="inline-flex items-center gap-2 border border-indigo-100 dark:border-white/15 px-6 py-3 rounded-full font-medium hover:border-marigold transition-colors"
              >
                {t("hero.cta2")}
              </Link>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="relative"
          >
            <div className="gradient-card rounded-card p-8 text-white shadow-card">
              <p className="text-sm text-white/70">Sample answer</p>
              <p className="font-display text-xl mt-2">
                "Based on PMGKAY guidelines, AAY cardholders get 5kg free foodgrain monthly."
              </p>
              <div className="mt-5 h-1.5 rounded-full bg-white/20 overflow-hidden">
                <div className="h-full bg-marigold w-[86%]" />
              </div>
              <p className="text-xs text-white/60 mt-2">86% confidence · Source: Dept. of Food & Public Distribution</p>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Citizen journey timeline — signature element */}
      <section className="max-w-7xl mx-auto px-5 md:px-8 py-16">
        <h2 className="font-display text-2xl md:text-3xl font-semibold text-center">The citizen journey</h2>
        <p className="text-center text-indigo-900/60 dark:text-white/50 mt-2 max-w-xl mx-auto">
          One thread, four stages — the same path most citizens walk when dealing with welfare services.
        </p>

        <div className="relative mt-14">
          <svg className="hidden md:block absolute top-8 left-0 w-full h-4" viewBox="0 0 1000 20" preserveAspectRatio="none">
            <path d="M0,10 L1000,10" className="thread-line" />
          </svg>
          <div className="grid md:grid-cols-4 gap-8 relative">
            {JOURNEY.map((step, i) => {
              const Icon = step.icon;
              return (
                <motion.div
                  key={step.title}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.1, duration: 0.4 }}
                  className="text-center"
                >
                  <div className="w-16 h-16 mx-auto rounded-full bg-white dark:bg-indigo-900 border-2 border-marigold flex items-center justify-center relative z-10">
                    <Icon size={22} className="text-marigold" />
                  </div>
                  <h3 className="font-display font-semibold mt-4">{step.title}</h3>
                  <p className="text-sm text-indigo-900/60 dark:text-white/50 mt-1">{step.desc}</p>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Quick action cards */}
      <section className="max-w-7xl mx-auto px-5 md:px-8 pb-24">
        <div className="grid md:grid-cols-3 gap-6">
          {[
            { href: "/schemes", title: "Smart Scheme Finder", desc: "Answer a few questions, get matched schemes with explanations." },
            { href: "/checklist", title: "Document Checklist", desc: "Generate and download exactly what you need for any process." },
            { href: "/grievance", title: "Grievance Assistant", desc: "Understand the right department and escalation path." },
          ].map((c) => (
            <Link
              key={c.href}
              href={c.href}
              className="rounded-card p-6 bg-white/80 dark:bg-white/5 border border-indigo-50 dark:border-white/10 shadow-card hover:-translate-y-1 transition-transform"
            >
              <h3 className="font-display text-lg font-semibold">{c.title}</h3>
              <p className="text-sm text-indigo-900/60 dark:text-white/50 mt-2">{c.desc}</p>
              <span className="inline-flex items-center gap-1 text-sm text-marigold mt-4 font-medium">
                Open <ArrowRight size={14} />
              </span>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
