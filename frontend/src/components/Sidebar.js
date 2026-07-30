import Link from "next/link";
import { useLanguage } from "@/contexts/LanguageContext";
import { useRouter } from "next/router";
import {
  Sparkles,
  X,
  Home,
  MessageCircle,
  Search,
  ClipboardCheck,
  MessageSquare,
  Star,
  Shield,
  Settings,
} from "lucide-react";

export default function Sidebar({ isOpen, onClose }) {
  const router = useRouter();
  const { t } = useLanguage()

  const navItems = [
    {
      href: "/",
      icon: Home,
      label: "Home",
      description: "Your starting point",
    },
    {
      href: "/chat",
      icon: MessageCircle,
      label: "Ask JanMitra AI",
      description: "Get instant welfare guidance",
      badge: "AI",
      featured: true,
    },
  ];

  const services = [
    {
      href: "/schemes",
      icon: Search,
      label: "Scheme Finder",
      description: "Discover benefits",
    },
    {
      href: "/checklist",
      icon: ClipboardCheck,
      label: "Checklist",
      description: "Prepare documents",
    },
    {
      href: "/grievance",
      icon: MessageSquare,
      label: "Grievance",
      description: "Resolve an issue",
    },
  ];

  const secondary = [
    {
      href: "/feedback",
      icon: Star,
      label: "Feedback",
    },
    {
      href: "/disclaimer",
      icon: Shield,
      label: "Responsible AI",
    },
    {
      href: "/admin",
      icon: Settings,
      label: "Admin",
    },
  ];

  return (
        <aside
      className={`fixed top-0 left-0 bottom-0 w-[min(540px,94vw)] p-6 z-[3000] flex flex-col bg-[#12231c] text-white overflow-y-auto transition-transform duration-[380ms] ease-[cubic-bezier(.22,.8,.25,1)] shadow-[30px_0_100px_rgba(0,0,0,0.25)] ${
        isOpen ? "translate-x-0" : "-translate-x-[105%]"
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between gap-5 mb-10">
        <Link href="/" className="flex items-center gap-3 text-white">
          <span className="w-[52px] h-[52px] flex-shrink-0 grid place-items-center rounded-[17px] bg-[#f4c95d] text-[#16211c]">
            <Sparkles size={23} />
          </span>

          <div>
            <strong className="font-heading text-[23px] font-extrabold tracking-[-1px]">
              JanMitra <span className="text-[#59dab9]">AI</span>
            </strong>

            <small className="block -mt-0.5 text-white/45 text-[11px]">
              Citizen Welfare Assistant
            </small>
          </div>
        </Link>

        <button
          onClick={onClose}
          className="w-[45px] h-[45px] grid place-items-center border border-white/15 rounded-[14px] bg-white/5 hover:bg-[#ff6b35] transition"
        >
          <X size={20} />
        </button>
      </div>

      {/* Intro */}
      <div className="pb-7 border-b border-white/10">
        <span className="inline-flex mb-2.5 text-[#62dfbd] text-[11px] font-extrabold tracking-[1.5px] uppercase">
          Explore JanMitra AI
        </span>

        <h2 className="text-[32px] font-bold leading-tight">
          What can we help
          <br />
          you with today?
        </h2>

        <p className="mt-3 text-white/60 text-sm">
          Choose a service or ask the AI assistant directly.
        </p>
      </div>

      {/* Navigation */}
      <nav className="py-7 flex flex-col gap-7">
        <div className="flex flex-col gap-3">
          {navItems.map((item) => {
            const Icon = item.icon;

            return (
              <Link
                key={item.href}
                href={item.href}
                className="flex items-center gap-3 rounded-xl p-3 hover:bg-white/10 transition"
              >
                <Icon size={20} />

                <div className="flex-1">
                  <div className="font-semibold">{item.label}</div>

                  <div className="text-xs text-white/50">
                    {item.description}
                  </div>
                </div>

                {item.badge && (
                  <span className="px-2 py-1 rounded bg-yellow-300 text-black text-[10px] font-bold">
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </div>

        <div className="flex flex-col gap-3">
          {services.map((item) => {
            const Icon = item.icon;

            return (
              <Link
                key={item.href}
                href={item.href}
                className="flex items-center gap-3 rounded-xl p-3 hover:bg-white/10 transition"
              >
                <Icon size={20} />

                <div>
                  <div className="font-semibold">{item.label}</div>

                  <div className="text-xs text-white/50">
                    {item.description}
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
                <div className="flex flex-col gap-3">
          <span className="text-white/40 text-xs uppercase tracking-wider">
            JanMitra AI
          </span>

          {secondary.map((item) => {
            const Icon = item.icon;

            return (
              <Link
                key={item.href}
                href={item.href}
                className="flex items-center gap-3 rounded-xl p-3 hover:bg-white/10 transition"
              >
                <Icon size={20} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </div>
      </nav>

      {/* Footer */}
      <div className="mt-auto">
        <div className="p-4 flex gap-3 rounded-xl bg-white/5 border border-white/10">
          <Shield size={18} className="text-yellow-300 flex-shrink-0" />

          <div>
            <strong className="block text-sm">
              Independent assistance tool
            </strong>

            <span className="text-xs text-white/60">
              Not an official Government service.
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
}