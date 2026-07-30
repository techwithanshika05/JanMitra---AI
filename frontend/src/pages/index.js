import { useEffect } from 'react'
import Link from 'next/link'
import { Sparkles, ArrowUpRight, Search, ClipboardCheck, FileWarning, PhoneCall, Bot, ShieldCheck, Languages, Landmark } from 'lucide-react'
import { useLanguage } from '@/contexts/LanguageContext'

export default function Home() {
  const { language, t } = useLanguage()

  // Debug: Log current language
  useEffect(() => {
    console.log('Current language in Home:', language)
  }, [language])

  return (
    <div className="setu-home animate-fade-in max-w-[1480px] mx-auto px-4 sm:px-8 py-7 sm:py-10">
      {/* HERO */}
      <section className="relative min-h-[500px] sm:min-h-[650px] grid grid-cols-1 lg:grid-cols-[1.05fr_.95fr] items-center gap-10 p-8 sm:p-16 lg:p-[70px] rounded-[38px] overflow-hidden bg-gradient-to-br from-[#fff8ed] via-white to-[#eef5ff] dark:from-[#161c29] dark:via-[#111827] dark:to-[#111827] border border-black/5 dark:border-white/5">
        <div className="relative z-10">
          <div className="inline-flex items-center gap-2.5 px-3.5 py-2 rounded-full border border-black/10 dark:border-white/10 bg-white/70 dark:bg-[#182131] text-sm font-extrabold uppercase tracking-wide">
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse shadow-[0_0_0_5px_rgba(18,183,106,0.12)]"></span>
            {t('hero_badge')}
          </div>
          <h1 className="mt-8 mb-5 text-[clamp(52px,5.6vw,88px)] leading-[0.98] tracking-[-0.065em] font-extrabold text-[#101828] dark:text-white whitespace-pre-line">
            {t('hero_title')}
          </h1>
          <p className="max-w-[620px] text-[#667085] dark:text-[#94a3b8] text-lg leading-[1.8]">
            {t('hero_sub')}
          </p>
          <div className="flex flex-wrap items-center gap-3.5 mt-9">
            <Link href="/chat" className="min-w-[225px] flex items-center justify-between px-4 py-4 bg-[#101828] dark:bg-white text-white dark:text-[#101828] rounded-[18px] transition-all hover:-translate-y-1 hover:shadow-lg">
              <span className="flex flex-col text-[17px] font-extrabold">
                <small className="text-[10px] tracking-[0.14em] text-[#98a2b3] dark:text-[#667085]">{t('start_here_btn')}</small>
                {t('ask_janmitra_btn')}
              </span>
              <span className="w-[46px] h-[46px] grid place-items-center rounded-[13px] bg-[#ff6b35]">
                <ArrowUpRight size={18} />
              </span>
            </Link>
            <Link href="/schemes" className="inline-flex items-center gap-2.5 px-5 py-[18px] rounded-[16px] border border-[#e5e7eb] dark:border-[#273244] bg-white dark:bg-[#182131] text-[#101828] dark:text-white font-bold transition-all hover:-translate-y-1 hover:border-[#176bff]">
              <Sparkles size={18} />
              <span>{t('discover_schemes')}</span>
            </Link>
          </div>
        </div>
        <div className="relative min-h-[400px] lg:min-h-[500px] flex items-center justify-center">
          <div className="absolute w-[470px] h-[470px] border border-dashed border-blue-400/25 rounded-full animate-spin-slow"></div>
          <div className="absolute w-[570px] h-[570px] border border-dashed border-blue-400/25 rounded-full animate-spin-slow [animation-direction:reverse]"></div>
          <div className="relative z-10 w-[min(390px,90%)] p-9 rounded-[35px] bg-[#101828] text-white shadow-2xl rotate-[2deg] transition-all hover:rotate-0 hover:-translate-y-2">
            <div className="inline-flex items-center gap-2 text-[11px] font-extrabold tracking-[0.12em] text-[#a7f3d0]">
              <span className="w-2 h-2 rounded-full bg-[#32d583] shadow-[0_0_16px_#32d583]"></span>
              AI ONLINE
            </div>
            <div className="w-[72px] h-[72px] grid place-items-center mt-8 mb-6 rounded-[23px] bg-gradient-to-br from-[#176bff] to-[#7c3aed] shadow-[0_15px_40px_rgba(23,107,255,0.35)]">
              <Bot size={34} />
            </div>
            <h3 className="text-[34px] font-bold tracking-[-0.04em]">Namaste 👋</h3>
            <p className="text-[#98a2b3] text-base leading-relaxed">Tell me what government service you need help with.</p>
            <Link href="/chat" className="flex items-center justify-between mt-7 px-[18px] py-4 rounded-[15px] bg-white/5 border border-white/10 text-[#d0d5dd] hover:bg-white/10 transition-all">
              <span>{t('ask_anything') || 'Ask your question...'}</span>
              <ArrowUpRight className="text-[#ffd166]" size={18} />
            </Link>
          </div>
          <div className="absolute left-0 top-[105px] z-20 flex items-center gap-3 px-4 py-[14px] border border-black/10 dark:border-white/10 rounded-[16px] bg-white/90 dark:bg-[#182131] shadow-lg animate-float">
            <ShieldCheck className="text-[#176bff]" size={18} />
            <div>
              <strong className="text-[13px]">Simple guidance</strong>
              <span className="block text-[11px] text-[#667085] dark:text-[#94a3b8]">No confusing language</span>
            </div>
          </div>
          <div className="absolute -right-2 bottom-[90px] z-20 flex items-center gap-3 px-4 py-[14px] border border-black/10 dark:border-white/10 rounded-[16px] bg-white/90 dark:bg-[#182131] shadow-lg animate-float [animation-delay:-2s]">
            <Languages size={18} className="text-[#176bff]" />
            <div>
              <strong className="text-[13px]">Multilingual</strong>
              <span className="block text-[11px] text-[#667085] dark:text-[#94a3b8]">English · Hindi · Hinglish</span>
            </div>
          </div>
        </div>
      </section>

      {/* QUICK SERVICES */}
      <section className="py-[100px] px-2.5">
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-end gap-4 mb-11">
          <div>
            <span className="text-[#ff6b35] font-mono text-sm font-extrabold">01</span>
            <p className="mt-2 text-xs font-extrabold tracking-[0.13em] text-[#667085] dark:text-[#94a3b8]">{t('what_need')}</p>
          </div>
          <h2 className="text-[clamp(38px,4vw,60px)] leading-[1.05] tracking-[-0.05em] text-[#101828] dark:text-white max-w-[600px] whitespace-pre-line">{t('choose_task')}</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-[1.35fr_1fr_1fr] gap-3.5">
          <Link href="/schemes" className="md:row-span-2 min-h-[584px] p-7 rounded-[24px] bg-[#176bff] text-white flex flex-col justify-between transition-all hover:-translate-y-2 hover:shadow-[0_30px_60px_rgba(23,107,255,0.25)]">
            <div className="flex items-center justify-between">
              <span className="w-[54px] h-[54px] grid place-items-center rounded-[16px] bg-white/15">
                <Search size={24} />
              </span>
              <ArrowUpRight size={20} />
            </div>
            <div>
              <span className="block font-mono text-xs opacity-55 mb-3">01</span>
              <h3 className="text-[48px] font-bold tracking-[-0.035em]">{t('find_schemes')}</h3>
              <p className="max-w-[430px] text-white/75 text-[17px] leading-relaxed">{t('find_schemes_desc')}</p>
            </div>
          </Link>
          <Link href="/checklist" className="min-h-[285px] p-7 rounded-[24px] border border-[#e5e7eb] dark:border-[#273244] bg-white dark:bg-[#182131] text-[#101828] dark:text-white flex flex-col transition-all hover:-translate-y-2 hover:shadow-md hover:border-blue-400/40">
            <div className="flex items-center justify-between">
              <span className="w-[54px] h-[54px] grid place-items-center rounded-[16px] bg-[#f2f4f7] dark:bg-[#273244]">
                <ClipboardCheck size={24} />
              </span>
              <ArrowUpRight size={20} className="text-[#667085] dark:text-[#94a3b8]" />
            </div>
            <div className="mt-auto">
              <span className="block font-mono text-xs opacity-55 mb-3">02</span>
              <h3 className="text-[26px] font-bold tracking-[-0.035em]">{t('documents')}</h3>
              <p className="text-[15px] leading-relaxed text-[#667085] dark:text-[#94a3b8]">{t('documents_desc')}</p>
            </div>
          </Link>
          <Link href="/grievance" className="min-h-[285px] p-7 rounded-[24px] border border-[#e5e7eb] dark:border-[#273244] bg-white dark:bg-[#182131] text-[#101828] dark:text-white flex flex-col transition-all hover:-translate-y-2 hover:shadow-md hover:border-blue-400/40">
            <div className="flex items-center justify-between">
              <span className="w-[54px] h-[54px] grid place-items-center rounded-[16px] bg-[#f2f4f7] dark:bg-[#273244]">
                <FileWarning size={24} />
              </span>
              <ArrowUpRight size={20} className="text-[#667085] dark:text-[#94a3b8]" />
            </div>
            <div className="mt-auto">
              <span className="block font-mono text-xs opacity-55 mb-3">03</span>
              <h3 className="text-[26px] font-bold tracking-[-0.035em]">{t('raise_grievance')}</h3>
              <p className="text-[15px] leading-relaxed text-[#667085] dark:text-[#94a3b8]">{t('raise_grievance_desc')}</p>
            </div>
          </Link>
        </div>
      </section>

      {/* IMPACT */}
      <section className="grid grid-cols-1 lg:grid-cols-[.85fr_1.15fr] gap-12 p-8 sm:p-[75px] rounded-[32px] bg-[#101828] text-white">
        <div>
          <span className="text-[#ff6b35] font-mono text-sm font-extrabold">02</span>
          <h2 className="mt-4 mb-4 text-[43px] leading-[1.08] tracking-[-0.045em]">{t('built_to')}</h2>
          <p className="max-w-[440px] text-[#98a2b3] text-base leading-relaxed">{t('built_desc')}</p>
        </div>
        <div className="grid grid-cols-2 border-l border-white/10">
          <div className="p-[30px_38px] border-r border-b border-white/10">
            <strong className="block text-[clamp(40px,4vw,64px)] tracking-[-0.06em]">80<span className="text-[#ffd166]">Cr+</span></strong>
            <p className="mt-1.5 text-[#98a2b3]">{t('beneficiaries')}</p>
          </div>
          <div className="p-[30px_38px] border-b border-white/10">
            <strong className="block text-[clamp(40px,4vw,64px)] tracking-[-0.06em]">10<span className="text-[#ffd166]">+</span></strong>
            <p className="mt-1.5 text-[#98a2b3]">{t('welfare_schemes')}</p>
          </div>
          <div className="p-[30px_38px] border-r border-white/10">
            <strong className="block text-[clamp(40px,4vw,64px)] tracking-[-0.06em]">24<span className="text-[#ffd166]">/7</span></strong>
            <p className="mt-1.5 text-[#98a2b3]">{t('ai_assistance')}</p>
          </div>
          <div className="p-[30px_38px]">
            <strong className="block text-[clamp(40px,4vw,64px)] tracking-[-0.06em]">UP</strong>
            <p className="mt-1.5 text-[#98a2b3]">{t('uttar_pradesh')}</p>
          </div>
        </div>
      </section>

      {/* HELPLINES */}
      <section className="mt-7 grid grid-cols-1 md:grid-cols-[280px_1fr] gap-7 p-8 rounded-[28px] bg-[#fff3d6] dark:bg-[#292316]">
        <div className="flex items-center gap-4">
          <span className="w-[55px] h-[55px] grid place-items-center rounded-full bg-[#ff6b35] text-white">
            <PhoneCall size={24} />
          </span>
          <div>
            <span className="text-[10px] font-extrabold tracking-[0.12em] text-[#b54708] dark:text-[#fbbf24]">{t('need_human_help')}</span>
            <h2 className="text-xl font-bold mt-1 text-[#101828] dark:text-white">{t('important_helplines')}</h2>
          </div>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-0">
          <a href="tel:1967" className="flex flex-col px-5 py-2 border-l border-black/10 dark:border-white/10 text-[#101828] dark:text-white hover:bg-white/5 transition-all">
            <span className="text-[10px] font-extrabold tracking-[0.08em] text-[#667085] dark:text-[#94a3b8]">UP FOOD & PDS</span>
            <strong className="mt-1.5 text-xl tracking-[-0.03em]">1967</strong>
          </a>
          <a href="tel:1076" className="flex flex-col px-5 py-2 border-l border-black/10 dark:border-white/10 text-[#101828] dark:text-white hover:bg-white/5 transition-all">
            <span className="text-[10px] font-extrabold tracking-[0.08em] text-[#667085] dark:text-[#94a3b8]">CM HELPLINE</span>
            <strong className="mt-1.5 text-xl tracking-[-0.03em]">1076</strong>
          </a>
          <a href="tel:155261" className="flex flex-col px-5 py-2 border-l border-black/10 dark:border-white/10 text-[#101828] dark:text-white hover:bg-white/5 transition-all">
            <span className="text-[10px] font-extrabold tracking-[0.08em] text-[#667085] dark:text-[#94a3b8]">PM KISAN</span>
            <strong className="mt-1.5 text-xl tracking-[-0.03em]">155261</strong>
          </a>
          <a href="tel:14555" className="flex flex-col px-5 py-2 border-l border-black/10 dark:border-white/10 text-[#101828] dark:text-white hover:bg-white/5 transition-all">
            <span className="text-[10px] font-extrabold tracking-[0.08em] text-[#667085] dark:text-[#94a3b8]">AYUSHMAN</span>
            <strong className="mt-1.5 text-xl tracking-[-0.03em]">14555</strong>
          </a>
          <a href="tel:18001114000" className="flex flex-col px-5 py-2 border-l border-black/10 dark:border-white/10 text-[#101828] dark:text-white hover:bg-white/5 transition-all">
            <span className="text-[10px] font-extrabold tracking-[0.08em] text-[#667085] dark:text-[#94a3b8]">CONSUMER</span>
            <strong className="mt-1.5 text-xl tracking-[-0.03em]">1800-11-4000</strong>
          </a>
        </div>
      </section>
    </div>
  )
}