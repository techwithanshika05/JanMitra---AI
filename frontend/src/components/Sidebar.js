import Link from 'next/link'
import { useRouter } from 'next/router'
import { 
  Sparkles, X, House, MessageCircleMore, Radar, ListChecks, 
  MessagesSquare, Star, ShieldCheck, Activity 
} from 'lucide-react'

export default function Sidebar({ isOpen, onClose }) {
  const router = useRouter()

  const navItems = [
    { href: '/', icon: House, label: 'home', description: 'home_desc' },
    { href: '/chat', icon: MessageCircleMore, label: 'ask_janmitra', description: 'ask_desc', badge: 'AI', featured: true },
  ]

  const services = [
    { href: '/schemes', icon: Radar, label: 'scheme_finder', description: 'scheme_desc' },
    { href: '/checklist', icon: ListChecks, label: 'checklist', description: 'checklist_desc' },
    { href: '/grievance', icon: MessagesSquare, label: 'grievance', description: 'grievance_desc' },
  ]

  const secondary = [
    { href: '/feedback', icon: Star, label: 'feedback' },
    { href: '/disclaimer', icon: ShieldCheck, label: 'responsible_ai' },
    { href: '/admin', icon: Activity, label: 'admin' },
  ]

  return (
    <aside className={`fixed top-0 left-0 bottom-0 w-[min(540px,94vw)] p-6 z-[3000] flex flex-col bg-[#12231c] text-white overflow-y-auto transition-transform duration-[380ms] ease-[cubic-bezier(.22,.8,.25,1)] shadow-[30px_0_100px_rgba(0,0,0,0.25)] ${isOpen ? 'translate-x-0' : '-translate-x-[105%]'}`}>
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
            <small className="block -mt-0.5 text-white/45 text-[11px]">Citizen Welfare Assistant</small>
          </div>
        </Link>
        <button onClick={onClose} className="w-[45px] h-[45px] flex-shrink-0 grid place-items-center border border-white/15 rounded-[14px] bg-white/5 text-white hover:bg-[#ff6b35] hover:border-[#ff6b35] hover:rotate-[6deg] transition-all">
          <X size={20} />
        </button>
      </div>

      {/* Intro */}
      <div className="pb-7 border-b border-white/10">
        <span className="inline-flex mb-2.5 text-[#62dfbd] text-[11px] font-extrabold tracking-[1.5px] uppercase" data-i18n="explore">Explore JanMitra AI</span>
        <h2 className="text-[clamp(29px,4vw,42px)] leading-[1.08] tracking-[-1.8px] font-heading" data-i18n="what_help">What can we help<br />you with today?</h2>
        <p className="max-w-[380px] mt-3 text-white/55 text-sm" data-i18n="choose_service">Choose a service or ask the AI assistant directly.</p>
      </div>

      {/* Navigation */}
      <nav className="py-7 flex flex-col gap-7">
        {/* Primary */}
        <div className="flex flex-col gap-2.5">
          <span className="mb-1 text-white/35 text-[10px] font-extrabold tracking-[1.6px] uppercase" data-i18n="start_here">Start here</span>
          {navItems.map((item) => {
            const Icon = item.icon
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`relative min-h-[66px] p-2.5 flex items-center gap-3 border border-transparent rounded-[17px] text-white/80 hover:text-white hover:bg-white/10 hover:border-white/10 hover:translate-x-1 transition-all ${router.pathname === item.href ? 'text-white bg-gradient-to-br from-[rgba(77,214,177,0.18)] to-[rgba(77,214,177,0.07)] border-[rgba(92,225,189,0.18)]' : ''} ${item.featured ? 'bg-[#ff6b35] text-white hover:bg-[#ff7848]' : ''}`}
              >
                <span className="w-[43px] h-[43px] flex-shrink-0 grid place-items-center rounded-[13px] bg-white/10">
                  <Icon size={19} />
                </span>
                <span className="flex-1 min-w-0 flex flex-col">
                  <strong className="text-sm font-bold" data-i18n={item.label}>{item.label}</strong>
                  {item.description && <small className="mt-0.5 text-white/40 text-[11px]" data-i18n={item.description}>{item.description}</small>}
                </span>
                {item.badge && <span className="px-2 py-1 rounded-[7px] bg-[#f4c95d] text-[#142019] text-[9px] font-black">{item.badge}</span>}
              </Link>
            )
          })}
        </div>

        {/* Services */}
        <div className="flex flex-col gap-2.5">
          <span className="mb-1 text-white/35 text-[10px] font-extrabold tracking-[1.6px] uppercase" data-i18n="citizen_tools">Citizen tools</span>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {services.map((item) => {
              const Icon = item.icon
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`min-h-[95px] p-2.5 flex items-start gap-3 border border-transparent rounded-[17px] text-white/80 hover:text-white hover:bg-white/10 hover:border-white/10 hover:translate-x-1 transition-all ${router.pathname === item.href ? 'text-white bg-gradient-to-br from-[rgba(77,214,177,0.18)] to-[rgba(77,214,177,0.07)] border-[rgba(92,225,189,0.18)]' : ''}`}
                >
                  <span className="w-[38px] h-[38px] flex-shrink-0 grid place-items-center rounded-[13px] bg-white/10">
                    <Icon size={18} />
                  </span>
                  <span className="flex-1 min-w-0 flex flex-col">
                    <strong className="text-sm font-bold" data-i18n={item.label}>{item.label}</strong>
                    <small className="mt-0.5 text-white/40 text-[11px]" data-i18n={item.description}>{item.description}</small>
                  </span>
                </Link>
              )
            })}
          </div>
        </div>

        {/* Secondary */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
          <span className="mb-1 col-span-full text-white/35 text-[10px] font-extrabold tracking-[1.6px] uppercase">JanMitra AI</span>
          {secondary.map((item) => {
            const Icon = item.icon
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`min-h-[50px] p-2.5 flex items-center gap-3 border border-transparent rounded-[17px] text-white/80 hover:text-white hover:bg-white/10 hover:border-white/10 hover:translate-x-1 transition-all ${router.pathname === item.href ? 'text-white bg-gradient-to-br from-[rgba(77,214,177,0.18)] to-[rgba(77,214,177,0.07)] border-[rgba(92,225,189,0.18)]' : ''}`}
              >
                <span className="w-[38px] h-[38px] flex-shrink-0 grid place-items-center rounded-[13px] bg-white/10">
                  <Icon size={18} />
                </span>
                <strong className="text-sm font-bold" data-i18n={item.label}>{item.label}</strong>
              </Link>
            )
          })}
        </div>
      </nav>

      {/* Footer */}
      <div className="mt-auto">
        <div className="p-4 flex gap-3 rounded-[17px] bg-white/5 border border-white/10 text-white/65">
          <ShieldCheck size={18} className="flex-shrink-0 text-[#f4c95d]" />
          <div>
            <strong className="text-white text-xs" data-i18n="independent_tool">Independent assistance tool</strong>
            <span className="block text-[10px]" data-i18n="not_official">Not an official Government service.</span>
          </div>
        </div>
      </div>
    </aside>
  )
}