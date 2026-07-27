"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Menu, X, Landmark, Languages, LogIn, LogOut, ChevronDown,
  Search, MessageCircleQuestion, ShieldCheck, ShieldAlert,
} from "lucide-react";
import { useLanguage } from "@/lib/i18n";

const TOP_LINK_KEYS = [
  { href: "/dashboard", key: "nav.dashboard" as const },
  { href: "/checklist", key: "nav.checklist" as const },
  { href: "/documents", key: "nav.documents" as const },
  { href: "/faq", key: "nav.faq" as const },
  { href: "/helpline", key: "nav.helpline" as const },
];

const DROPDOWN_LINKS = [
  { href: "/schemes", key: "nav.schemes" as const, icon: Search },
  { href: "/chat", key: "nav.chat" as const, icon: MessageCircleQuestion },
  { href: "/grievance", key: "nav.grievance" as const, icon: ShieldAlert },
  { href: "/admin", key: "nav.admin" as const, icon: ShieldCheck },
];

export default function Navbar() {
  const [open, setOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [loggedIn, setLoggedIn] = useState(false);
  const { lang, setLang, t } = useLanguage();
  const pathname = usePathname();
  const router = useRouter();
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setLoggedIn(!!window.localStorage.getItem("janmitra_token"));
    setMenuOpen(false);
  }, [pathname]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMenuOpen(false);
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const logout = () => {
    window.localStorage.removeItem("janmitra_token");
    setLoggedIn(false);
    setMenuOpen(false);
    router.push("/");
  };

  return (
    <header className="sticky top-4 z-50 px-4">
      <div className="max-w-7xl mx-auto glass rounded-pill shadow-card h-16 flex items-center justify-between px-5 md:px-6">
        <Link href="/" className="flex items-center gap-2 font-display text-lg font-bold text-maroon">
          <span className="w-9 h-9 rounded-full bg-gradient-primary flex items-center justify-center text-white shadow-glow">
            <Landmark size={16} />
          </span>
          JanMitra <span className="text-rose">AI</span>
        </Link>

        <nav className="hidden lg:flex items-center gap-1 text-sm font-semibold">
          {TOP_LINK_KEYS.map((l) => {
            const active = pathname === l.href;
            return (
              <Link
                key={l.href}
                href={l.href}
                className={`relative px-3 py-2 rounded-pill transition-colors ${
                  active ? "text-white bg-maroon" : "text-maroon-dark hover:bg-blush/40"
                }`}
              >
                {t(l.key)}
              </Link>
            );
          })}

          {/* Dropdown: Scheme Finder, Ask JanMitra, Grievance, Admin, Login/Logout */}
          <div className="relative" ref={menuRef}>
            <button
              onClick={() => setMenuOpen((o) => !o)}
              className={`flex items-center gap-1 px-3 py-2 rounded-pill transition-colors ${
                menuOpen ? "text-white bg-maroon" : "text-maroon-dark hover:bg-blush/40"
              }`}
            >
              Menu
              <ChevronDown size={14} className={`transition-transform ${menuOpen ? "rotate-180" : ""}`} />
            </button>

            <AnimatePresence>
              {menuOpen && (
                <motion.div
                  initial={{ opacity: 0, y: -6, scale: 0.97 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -6, scale: 0.97 }}
                  transition={{ duration: 0.15 }}
                  className="absolute right-0 mt-2 w-56 rounded-card glass-card shadow-card p-2 origin-top-right"
                >
                  {DROPDOWN_LINKS.map((l) => {
                    const Icon = l.icon;
                    const active = pathname === l.href;
                    return (
                      <Link
                        key={l.href}
                        href={l.href}
                        onClick={() => setMenuOpen(false)}
                        className={`flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                          active ? "bg-maroon text-white" : "text-maroon-dark hover:bg-blush/40"
                        }`}
                      >
                        <Icon size={15} />
                        {t(l.key)}
                      </Link>
                    );
                  })}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </nav>

        <div className="flex items-center gap-2">
          {loggedIn ? (
            <button
              onClick={logout}
              aria-label="Log out"
              className="hidden sm:flex h-10 px-4 rounded-pill items-center gap-1.5 text-xs font-bold text-maroon-dark hover:bg-blush/40 transition-colors"
            >
              <LogOut size={14} /> Logout
            </button>
          ) : (
            <Link
              href="/login"
              className="hidden sm:flex h-10 px-4 rounded-pill items-center gap-1.5 text-xs font-bold bg-maroon text-white hover:bg-maroon-dark transition-colors"
            >
              <LogIn size={14} /> Login
            </Link>
          )}

          <button
            aria-label="Switch language"
            onClick={() => setLang(lang === "en" ? "hi" : lang === "hi" ? "hinglish" : "en")}
            className="h-10 px-4 rounded-pill flex items-center gap-1.5 text-xs font-bold text-maroon border-2 border-rose/40 hover:bg-blush/40 transition-colors"
          >
            <Languages size={14} />
            {lang === "en" ? "EN" : lang === "hi" ? "हिं" : "HG"}
          </button>

          <button
            className="lg:hidden w-10 h-10 flex items-center justify-center rounded-full hover:bg-blush/40 text-maroon"
            aria-label="Toggle menu"
            onClick={() => setOpen((o) => !o)}
          >
            {open ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      {/* Mobile menu: everything flat, including the dropdown items */}
      <AnimatePresence>
        {open && (
          <motion.nav
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
            className="lg:hidden max-w-7xl mx-auto mt-2 glass rounded-card shadow-card p-4 flex flex-col gap-1 text-sm font-semibold"
          >
            {TOP_LINK_KEYS.map((l) => (
              <Link key={l.href} href={l.href} onClick={() => setOpen(false)} className="px-3 py-2.5 rounded-lg text-maroon-dark hover:bg-blush/40">
                {t(l.key)}
              </Link>
            ))}
            <div className="border-t border-blush/50 my-1 pt-1">
              {DROPDOWN_LINKS.map((l) => (
                <Link key={l.href} href={l.href} onClick={() => setOpen(false)} className="px-3 py-2.5 rounded-lg text-maroon-dark hover:bg-blush/40 flex items-center gap-2">
                  <l.icon size={15} /> {t(l.key)}
                </Link>
              ))}
            </div>
            <div className="border-t border-blush/50 pt-1">
              {loggedIn ? (
                <button onClick={logout} className="px-3 py-2.5 rounded-lg text-maroon-dark hover:bg-blush/40 w-full text-left">
                  Logout
                </button>
              ) : (
                <Link href="/login" onClick={() => setOpen(false)} className="px-3 py-2.5 rounded-lg text-maroon-dark hover:bg-blush/40 block">
                  Login
                </Link>
              )}
            </div>
          </motion.nav>
        )}
      </AnimatePresence>
    </header>
  );
}
