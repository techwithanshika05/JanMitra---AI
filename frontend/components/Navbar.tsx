"use client";
import Link from "next/link";
import { useState, useEffect } from "react";
import { Moon, Sun, Menu, X, Landmark, Languages } from "lucide-react";
import { useLanguage } from "@/lib/i18n";

const LINK_KEYS = [
  { href: "/dashboard", key: "nav.dashboard" as const },
  { href: "/schemes", key: "nav.schemes" as const },
  { href: "/chat", key: "nav.chat" as const },
  { href: "/checklist", key: "nav.checklist" as const },
  { href: "/grievance", key: "nav.grievance" as const },
  { href: "/admin", key: "nav.admin" as const },
];

export default function Navbar() {
  const [dark, setDark] = useState(false);
  const [open, setOpen] = useState(false);
  const { lang, setLang, t } = useLanguage();

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
  }, [dark]);

  return (
    <header className="sticky top-0 z-50 glass">
      <div className="max-w-7xl mx-auto px-5 md:px-8 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 font-display text-lg font-semibold">
          <span className="w-8 h-8 rounded-full bg-indigo flex items-center justify-center text-white">
            <Landmark size={16} />
          </span>
          JanMitra <span className="text-marigold">AI</span>
        </Link>

        <nav className="hidden md:flex items-center gap-6 text-sm font-medium">
          {LINK_KEYS.map((l) => (
            <Link key={l.href} href={l.href} className="hover:text-marigold transition-colors">
              {t(l.key)}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          <button
            aria-label="Switch language"
            onClick={() => setLang(lang === "en" ? "hi" : "en")}
            className="h-9 px-3 rounded-full flex items-center gap-1.5 text-xs font-semibold border border-indigo-100 dark:border-white/10 hover:border-marigold transition-colors"
          >
            <Languages size={14} />
            {lang === "en" ? "हिं" : "EN"}
          </button>
          <button
            aria-label="Toggle dark mode"
            onClick={() => setDark((d) => !d)}
            className="w-9 h-9 rounded-full flex items-center justify-center border border-indigo-100 dark:border-white/10 hover:border-marigold transition-colors"
          >
            {dark ? <Sun size={16} /> : <Moon size={16} />}
          </button>
          <button
            className="md:hidden w-9 h-9 flex items-center justify-center"
            aria-label="Toggle menu"
            onClick={() => setOpen((o) => !o)}
          >
            {open ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      {open && (
        <nav className="md:hidden px-5 pb-4 flex flex-col gap-3 text-sm font-medium">
          {LINK_KEYS.map((l) => (
            <Link key={l.href} href={l.href} onClick={() => setOpen(false)}>
              {t(l.key)}
            </Link>
          ))}
        </nav>
      )}
    </header>
  );
}
