import Link from 'next/link'
import { useRouter } from 'next/router'
import { House, Sparkles, Radar, ClipboardCheck, MessageSquare } from 'lucide-react'
import { useLanguage } from '@/contexts/LanguageContext'

export default function QuickDock() {
  const router = useRouter()
  const { t } = useLanguage()
// Chat page pe hide karo
  if (router.pathname === '/chat') {
    return null
  }
  const items = [
    { href: '/', icon: House, label: 'home' },
    { href: '/chat', icon: Sparkles, label: 'ask_ai' },
    { href: '/schemes', icon: Radar, label: 'schemes' },
    { href: '/checklist', icon: ClipboardCheck, label: 'checklist' },
    { href: '/grievance', icon: MessageSquare, label: 'grievance' },
  ]

  return (
    <nav className="fixed z-[1000] left-1/2 bottom-3 sm:bottom-6 -translate-x-1/2 w-[calc(100%-20px)] sm:w-auto max-w-[620px] p-[7px] flex items-center justify-between sm:justify-center gap-1 overflow-x-auto bg-[#13221c] border border-white/10 rounded-[21px] shadow-[0_20px_60px_rgba(10,28,20,0.25)]">
      {items.map((item) => {
        const Icon = item.icon
        return (
          <Link
            key={item.href}
            href={item.href}
            className={`min-w-[52px] sm:min-w-[70px] h-[50px] sm:h-[54px] px-2 sm:px-3 flex items-center justify-center gap-2 rounded-[15px] text-white/55 text-[11px] font-bold hover:text-white hover:-translate-y-1 transition-all ${
              router.pathname === item.href ? 'text-[#13221c] bg-[#f4c95d]' : ''
            }`}
          >
            <Icon size={18} />
            <span className="hidden sm:inline">{t(item.label)}</span>
          </Link>
        )
      })}
    </nav>
  )
}
