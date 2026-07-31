import Link from 'next/link'
import Image from 'next/image'
import { Menu, Sparkles, ArrowUpRight, LogIn, Search } from 'lucide-react'
import { useLanguage } from '@/contexts/LanguageContext'
import { useState, useRef, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'

export default function Navbar({ onMenuClick }) {
  const { language, changeLanguage, t } = useLanguage()
  const { user, authenticated, loading: authLoading } = useAuth()
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [showResults, setShowResults] = useState(false)
  const searchRef = useRef(null)

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (searchRef.current && !searchRef.current.contains(e.target)) {
        setShowResults(false)
      }
    }
    document.addEventListener('click', handleClickOutside)
    return () => document.removeEventListener('click', handleClickOutside)
  }, [])

  const initials = user?.name
    ? user.name.split(/\s+/).slice(0, 2).map(part => part[0]).join('').toUpperCase()
    : 'U'

  const handleSearch = async (q) => {
    setSearchQuery(q)
    if (q.length < 2) {
      setShowResults(false)
      return
    }
    try {
      const [schemesRes, faqsRes] = await Promise.all([
        fetch('/api/schemes', { credentials: 'include' }),
        fetch('/api/faqs', { credentials: 'include' })
      ])
      const schemes = schemesRes.ok ? await schemesRes.json() : []
      const faqs = faqsRes.ok ? await faqsRes.json() : []
      const needle = q.toLowerCase()
      const results = [
        ...schemes.map(item => ({
          title: item.name,
          description: item.description,
          url: '/schemes'
        })),
        ...faqs.map(item => ({
          title: item.question,
          description: item.answer,
          url: '/chat'
        }))
      ].filter(item =>
        `${item.title || ''} ${item.description || ''}`.toLowerCase().includes(needle)
      ).slice(0, 8)
      setSearchResults(results)
      setShowResults(true)
    } catch (e) {
      // silent
    }
  }

  return (
    <header className="sticky top-2 sm:top-[18px] z-[500] w-[calc(100%-20px)] sm:w-[calc(100%-40px)] max-w-[1536px] min-h-[68px] sm:min-h-[76px] mx-auto mt-2 sm:mt-[18px] px-2 sm:px-3 py-2 grid grid-cols-[auto_1fr_auto] items-center gap-2 sm:gap-3 bg-white/90 dark:bg-[rgba(18,31,25,0.90)] border border-[rgba(206,215,207,0.8)] dark:border-white/10 rounded-[20px] sm:rounded-[25px] shadow-[0_10px_40px_rgba(28,44,35,0.08)] backdrop-blur-[20px]">
      {/* LEFT - Menu + JanMitra AI */}
      <div className="flex items-center gap-3">
        <button onClick={onMenuClick} className="w-[48px] h-[48px] grid place-items-center border-0 rounded-[16px] text-white bg-[#101828] hover:bg-[#0d7c66] hover:-rotate-[5deg] hover:scale-105 transition-all">
          <Menu size={21} />
        </button>
        <Link href="/" className="flex items-center gap-2.5">
          <span className="w-[37px] h-[37px] grid place-items-center rounded-[12px] bg-[#dff5ec] text-[#0d7c66]">
            <Sparkles size={19} />
          </span>
          <span className="hidden sm:inline font-heading text-[21px] font-extrabold tracking-[-1px]">
            JanMitra <span className="text-[#0d7c66]">AI</span>
          </span>
        </Link>
      </div>

      <div ref={searchRef} className="relative hidden lg:block max-w-md w-full justify-self-center">
        <div className="h-11 px-4 flex items-center gap-2 rounded-xl border border-[#dde2dc] bg-[#f7f8f5] dark:bg-[#0e1914]">
          <Search size={16} className="text-[#667085]" />
          <input value={searchQuery} onChange={event => handleSearch(event.target.value)} placeholder={t('search_schemes_faqs')} className="w-full bg-transparent outline-none text-sm" />
        </div>
        {showResults && <div className="absolute top-12 left-0 right-0 max-h-80 overflow-y-auto rounded-2xl border border-[#dde2dc] bg-white dark:bg-[#14231c] shadow-xl">
          {searchResults.length === 0 ? <p className="p-4 text-sm text-[#667085]">{t('no_matching_results')}</p> : searchResults.map((result, index) => <Link key={`${result.title}-${index}`} href={result.url} onClick={() => setShowResults(false)} className="block p-4 border-b border-[#eef0ed] hover:bg-[#f4f7f6] dark:hover:bg-[#1d2d26]"><strong className="text-sm">{result.title}</strong><p className="mt-1 text-xs text-[#667085] line-clamp-2">{result.description}</p></Link>)}
        </div>}
      </div>

      {/* RIGHT - Language + Ask AI + Login + HCLTech Logo */}
      <div className="flex items-center gap-2.5">
        {/* Language Toggle */}
        <div className="hidden md:flex p-1 border border-[#dde2dc] dark:border-[#2c3a37] rounded-[13px] bg-[#f0f1eb] dark:bg-[#0e1914]">
          {['en', 'hi', 'hinglish'].map((lang) => (
            <button
              key={lang}
              onClick={() => changeLanguage(lang)}
              className={`min-w-[37px] h-[34px] px-2 border-0 rounded-[9px] text-[12px] font-extrabold transition-all ${
                language === lang 
                  ? 'text-white bg-[#101828] dark:bg-white dark:text-[#101828] shadow-[0_5px_12px_rgba(16,24,40,0.15)]' 
                  : 'text-[#5f6c65] dark:text-[#94a3b8] bg-transparent'
              }`}
            >
              {lang === 'en' ? 'EN' : lang === 'hi' ? 'हिं' : 'HG'}
            </button>
          ))}
        </div>

        
        {/* Ask JanMitra AI Button */}
        <Link href="/chat" className="min-h-[44px] px-4 flex items-center gap-2 rounded-[14px] bg-[#ff6b35] text-white font-extrabold text-sm shadow-[0_8px_22px_rgba(255,107,53,0.22)] hover:-translate-y-0.5 hover:shadow-[0_12px_28px_rgba(255,107,53,0.30)] transition-all">
          <span className="w-[7px] h-[7px] rounded-full bg-white shadow-[0_0_0_4px_rgba(255,255,255,0.18)]"></span>
          <span className="hidden xl:inline" data-i18n="ask_janmitra_btn">JanMitra AI</span>
          <ArrowUpRight size={16} />
        </Link>

        {authenticated ? (
          <Link
            href="/profile"
            className="min-h-[48px] px-2.5 sm:pr-4 flex items-center gap-2.5 rounded-[15px] border border-[#b9e7d8] dark:border-[#285949] bg-[#eefaf6] dark:bg-[#15332b] text-[#10271f] dark:text-white transition-all hover:border-[#0d7c66]"
            aria-label={`Signed in as ${user.name}`}
          >
            <span className="relative w-9 h-9 grid place-items-center rounded-full bg-[#0d7c66] text-white text-xs font-black">
              {initials}
              <i className="absolute -right-0.5 -bottom-0.5 w-3 h-3 rounded-full bg-[#12b76a] border-2 border-white dark:border-[#15332b]" />
            </span>
            <span className="hidden lg:block min-w-0 text-left">
              <strong className="block max-w-[120px] truncate text-xs">{user.name}</strong>
              <small className="block text-[10px] font-bold text-[#0d7c66] dark:text-[#6ef0ca]">{t('signed_in')}</small>
            </span>
          </Link>
        ) : authLoading ? (
          <span className="w-24 h-11 rounded-[14px] bg-[#eef0ed] dark:bg-[#1b2a24] animate-pulse" />
        ) : (
          <Link href="/login" className="min-h-[44px] px-4 flex items-center gap-2 rounded-[14px] border border-[#dde2dc] dark:border-[#2c3a37] bg-white dark:bg-[#14231c] text-[#101828] dark:text-white font-bold text-sm hover:border-[#ff6b35] hover:text-[#ff6b35] transition-all">
            <LogIn size={16} />
            <span className="hidden sm:inline">{t('login')}</span>
          </Link>
        )}

         {/* HCLTech Logo - Small and to the right */}
        <div className="hidden 2xl:flex items-center px-3 py-1.5 rounded-[10px] bg-[#f0f1eb] dark:bg-[#0e1914] border border-[#dde2dc] dark:border-[#2c3a37]">
          <Image 
            src="/hcl_logo.jpg" 
            alt="HCLTech"
            width={180}
            height={60}
            className="object-contain w-[180px] h-auto"
          />
        </div>
      </div>
    </header>
  )
}
