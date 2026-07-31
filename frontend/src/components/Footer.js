import Link from 'next/link'
import { Sparkles, Info } from 'lucide-react'
import { useLanguage } from '@/contexts/LanguageContext'

export default function Footer() {
  const { t } = useLanguage()
  return (
    <footer className="w-[min(1440px,calc(100%-48px))] mx-auto mb-5 sm:mb-7 pt-8 border-t border-[#dde2dc] dark:border-[#2c3a37]">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-7">
        <div className="flex items-center gap-3">
          <span className="w-[46px] h-[46px] grid place-items-center rounded-[14px] bg-[#dff5ec] dark:bg-[#1a3a2e] text-[#0d7c66]">
            <Sparkles size={22} />
          </span>
          <div>
            <strong className="font-heading text-xl">JanMitra <span className="text-[#0d7c66]">AI</span></strong>
            <p className="mt-0.5 text-[#5f6c65] dark:text-[#94a3b8] text-xs">{t('footer_tagline')}</p>
          </div>
        </div>
        <div className="flex flex-wrap gap-5">
          <Link href="/chat" className="text-[#5f6c65] dark:text-[#94a3b8] text-xs font-bold hover:text-[#0d7c66] transition-colors">{t('ask_ai')}</Link>
          <Link href="/schemes" className="text-[#5f6c65] dark:text-[#94a3b8] text-xs font-bold hover:text-[#0d7c66] transition-colors">{t('find_schemes_link')}</Link>
          <Link href="/disclaimer" className="text-[#5f6c65] dark:text-[#94a3b8] text-xs font-bold hover:text-[#0d7c66] transition-colors">{t('responsible_ai')}</Link>
          <Link href="/feedback" className="text-[#5f6c65] dark:text-[#94a3b8] text-xs font-bold hover:text-[#0d7c66] transition-colors">{t('feedback')}</Link>
        </div>
      </div>
      <div className="mt-6 pt-4 flex flex-col sm:flex-row justify-between border-t border-dashed border-[#dde2dc] dark:border-[#2c3a37] text-[#8b9690] dark:text-[#94a3b8] text-[11px]">
        <p>{t('copyright')}</p>
        <p className="flex items-center gap-1.5">
          <Info size={13} />
          {t('not_official_long')}
        </p>
      </div>
    </footer>
  )
}
