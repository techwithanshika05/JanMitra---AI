"use client";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Search, FileCheck2, MessageCircleQuestion, ShieldCheck, ArrowRight,
  Sparkles, FileText, Phone, Mic, ShieldCheck as ShieldIcon,
} from "lucide-react";
import { useLanguage } from "@/lib/i18n";
import FeatureCard from "@/components/FeatureCard";
import StatCard from "@/components/StatCard";
import FAQAccordion from "@/components/FAQAccordion";

const JOURNEY = [
  { title: "Discover", desc: "Find schemes you may qualify for based on your profile.", icon: Search },
  { title: "Understand", desc: "Get plain-language explanations of PDS & welfare processes.", icon: MessageCircleQuestion },
  { title: "Prepare", desc: "Generate a document checklist, downloadable as PDF.", icon: FileCheck2 },
  { title: "Resolve", desc: "File and track grievances with a clear escalation path.", icon: ShieldCheck },
];

const FEATURES = [
  { href: "/schemes", icon: Search, title: "Smart Scheme Finder", desc: "Answer a few questions, get matched schemes with a plain-language reason for each match." },
  { href: "/chat", icon: MessageCircleQuestion, title: "Ask JanMitra", desc: "A grounded AI conversation — every answer cites its source and shows a confidence score." },
  { href: "/checklist", icon: FileCheck2, title: "Document Checklist", desc: "Generate exactly what you need for any process, downloadable as a clean PDF." },
  { href: "/grievance", icon: ShieldCheck, title: "Grievance Assistant", desc: "Know the right department and escalation path before you file a complaint." },
  { href: "/documents", icon: FileText, title: "My Documents", desc: "Upload your own notice or letter and ask questions about it directly." },
  { href: "/helpline", icon: Phone, title: "Helpline & PDS Help", desc: "Verified national helpline numbers, one tap away from a phone call." },
];

const FAQS = [
  { question: "Does JanMitra AI ever guarantee I'm eligible for a scheme?", answer: "No. JanMitra explains general criteria and shows how closely your profile matches a scheme, but final eligibility is always decided by the concerned government department — never by the AI." },
  { question: "Where do the answers come from?", answer: "Every answer is grounded in official scheme data and FAQs, retrieved and cited live. If the knowledge base doesn't cover something, JanMitra says so instead of guessing." },
  { question: "Can I use JanMitra in Hindi?", answer: "Yes — switch languages from the navbar. Chat, voice input/output, and UI labels all follow your selected language." },
  { question: "Is my uploaded document shared with anyone else?", answer: "No. Documents you upload under 'My Documents' are scoped only to your session and are never mixed into another citizen's answers." },
];

export default function LandingPage() {
  const { t } = useLanguage();
  return (
    <div>
      {/* ---------------- Hero ---------------- */}
      <section className="glow-field overflow-hidden pt-16 pb-28">
        <div className="blob blob-pink w-96 h-96 -top-20 -left-20 animate-blob" />
        <div className="blob blob-gold w-96 h-96 top-40 -right-20 animate-blob" />

        <div className="max-w-7xl mx-auto px-5 md:px-8 grid md:grid-cols-2 gap-14 items-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          >
            <span className="inline-flex items-center gap-1.5 text-xs font-bold tracking-wide uppercase text-maroon bg-gold px-3 py-1.5 rounded-pill">
              <Sparkles size={12} /> {t("hero.tag")}
            </span>
            <h1 className="font-display text-4xl md:text-6xl font-extrabold mt-6 leading-[1.08] text-maroon-dark">
              {t("hero.title1")}{" "}
              <span className="bg-gradient-primary bg-clip-text text-transparent">{t("hero.title2")}</span>{" "}
              {t("hero.title3")}
            </h1>
            <p className="mt-6 text-maroon-dark/65 text-lg max-w-xl leading-relaxed">
              {t("hero.desc")}
            </p>
            <div className="mt-9 flex flex-wrap gap-4">
              <Link href="/chat" className="btn-primary inline-flex items-center gap-2 px-7 py-3.5">
                {t("hero.cta1")} <ArrowRight size={16} />
              </Link>
              <Link href="/schemes" className="btn-secondary inline-flex items-center gap-2 px-7 py-3.5">
                {t("hero.cta2")}
              </Link>
            </div>
          </motion.div>

          {/* Signature element: floating glass "scheme match" card, tied to the
              product itself rather than a generic dashboard mockup. */}
          <motion.div
            initial={{ opacity: 0, scale: 0.94 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.7, delay: 0.15, ease: [0.16, 1, 0.3, 1] }}
            className="relative flex justify-center"
          >
            <div className="animate-float glass-card rounded-card p-7 w-full max-w-sm shadow-glowLg">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wide text-rose">Scheme Match</span>
                <span className="w-8 h-8 rounded-full bg-gradient-primary flex items-center justify-center text-white">
                  <Sparkles size={14} />
                </span>
              </div>
              <p className="font-display text-xl font-bold mt-3 text-maroon-dark">
                Antyodaya Anna Yojana
              </p>
              <p className="text-sm text-maroon-dark/60 mt-1">
                Matches your income &amp; state profile
              </p>
              <div className="mt-5 h-2 rounded-pill bg-blush/50 overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: "91%" }}
                  transition={{ duration: 1.2, delay: 0.6, ease: [0.16, 1, 0.3, 1] }}
                  className="h-full bg-gradient-warm"
                />
              </div>
              <p className="text-xs text-maroon-dark/50 mt-2">91% match · Source: Dept. of Food &amp; Public Distribution</p>

              <div className="mt-5 pt-5 border-t border-blush/50 flex items-center gap-2 text-xs text-maroon-dark/60">
                <Mic size={13} className="text-rose" /> Ask by voice, in Hindi or English
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ---------------- Stats ---------------- */}
      <section className="max-w-7xl mx-auto px-5 md:px-8 -mt-14 relative z-10">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6">
          <StatCard value="7+" label="Welfare schemes indexed" index={0} />
          <StatCard value="2" label="Languages: English & Hindi" index={1} />
          <StatCard value="100%" label="Answers show their source" index={2} />
          <StatCard value="0" label="Eligibility promises made" index={3} />
        </div>
      </section>

      {/* ---------------- Citizen Journey Timeline ---------------- */}
      <section className="max-w-7xl mx-auto px-5 md:px-8 py-24">
        <div className="text-center max-w-xl mx-auto">
          <span className="text-xs font-bold uppercase tracking-wide text-rose">The citizen journey</span>
          <h2 className="font-display text-3xl font-extrabold mt-2 text-maroon-dark">
            One path, four stages
          </h2>
          <p className="text-maroon-dark/60 mt-3">
            The same sequence most citizens walk through when dealing with welfare services.
          </p>
        </div>

        <div className="relative mt-16">
          <svg className="hidden md:block absolute top-8 left-0 w-full h-4" viewBox="0 0 1000 20" preserveAspectRatio="none">
            <path d="M0,10 L1000,10" stroke="#F62477" strokeWidth="2" strokeDasharray="8 8" fill="none" opacity="0.4" />
          </svg>
          <div className="grid md:grid-cols-4 gap-10 relative">
            {JOURNEY.map((step, i) => {
              const Icon = step.icon;
              return (
                <motion.div
                  key={step.title}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.12, duration: 0.45 }}
                  className="text-center"
                >
                  <div className="w-16 h-16 mx-auto rounded-full bg-white border-2 border-rose flex items-center justify-center relative z-10 shadow-glow">
                    <Icon size={22} className="text-rose" />
                  </div>
                  <h3 className="font-display font-bold mt-5 text-maroon-dark">{`${i + 1}. ${step.title}`}</h3>
                  <p className="text-sm text-maroon-dark/60 mt-1.5">{step.desc}</p>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ---------------- Feature cards ---------------- */}
      <section className="max-w-7xl mx-auto px-5 md:px-8 pb-24">
        <div className="text-center max-w-xl mx-auto mb-14">
          <span className="text-xs font-bold uppercase tracking-wide text-rose">Everything in one place</span>
          <h2 className="font-display text-3xl font-extrabold mt-2 text-maroon-dark">Built for real government processes</h2>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {FEATURES.map((f, i) => (
            <FeatureCard key={f.href} {...f} index={i} />
          ))}
        </div>
      </section>

      {/* ---------------- Testimonials ---------------- */}
      <section className="glow-field py-24 overflow-hidden">
        <div className="blob blob-gold w-96 h-96 top-0 left-1/3 animate-blob" />
        <div className="max-w-7xl mx-auto px-5 md:px-8">
          <div className="text-center max-w-xl mx-auto mb-14">
            <span className="text-xs font-bold uppercase tracking-wide text-rose">What citizens say</span>
            <h2 className="font-display text-3xl font-extrabold mt-2 text-maroon-dark">Real questions, clear answers</h2>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {[
              { name: "Priya, Uttar Pradesh", text: "I finally understood which documents I actually needed for my ration card update — no more guessing at the office." },
              { name: "Ramesh, Bihar", text: "The scheme finder explained why PM-KISAN matched my profile in plain language, not government jargon." },
              { name: "Fatima, Telangana", text: "Being able to ask in Hindi and get a spoken answer made this so much easier for my parents to use too." },
            ].map((tst, i) => (
              <motion.div
                key={tst.name}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1, duration: 0.4 }}
                className="glass-card rounded-card p-6 shadow-card"
              >
                <p className="text-sm text-maroon-dark/75 leading-relaxed">&ldquo;{tst.text}&rdquo;</p>
                <p className="mt-4 text-sm font-bold text-maroon">{tst.name}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ---------------- FAQ ---------------- */}
      <section className="max-w-3xl mx-auto px-5 md:px-8 pb-28">
        <div className="text-center mb-12">
          <span className="text-xs font-bold uppercase tracking-wide text-rose">Good to know</span>
          <h2 className="font-display text-3xl font-extrabold mt-2 text-maroon-dark">Frequently asked questions</h2>
        </div>
        <FAQAccordion items={FAQS} />
      </section>

      {/* ---------------- Closing CTA ---------------- */}
      <section className="max-w-5xl mx-auto px-5 md:px-8 pb-28">
        <div className="bg-gradient-primary rounded-card p-10 md:p-14 text-center text-white shadow-glowLg">
          <ShieldIcon size={28} className="mx-auto text-gold" />
          <h2 className="font-display text-2xl md:text-3xl font-extrabold mt-4">
            Ready to find what you qualify for?
          </h2>
          <p className="text-white/75 mt-3 max-w-md mx-auto">
            Start a conversation or run the scheme finder — both take less than two minutes.
          </p>
          <div className="mt-7 flex flex-wrap justify-center gap-4">
            <Link href="/chat" className="btn-highlight inline-flex items-center gap-2 px-7 py-3.5">
              Ask JanMitra <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
