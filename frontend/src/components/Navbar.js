import Link from 'next/link'
import Image from 'next/image'
import { Menu, Sparkles, ArrowUpRight, LogIn } from 'lucide-react'
import { useLanguage } from '@/contexts/LanguageContext'
import { useState, useRef, useEffect } from 'react'

export default function Navbar({ onMenuClick }) {
  const { language, changeLanguage } = useLanguage()
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

  const handleSearch = async (q) => {
    setSearchQuery(q)
    if (q.length < 2) {
      setShowResults(false)
      return
    }
    try {
      const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`)
      const data = await res.json()
      setSearchResults(data.results || [])
      setShowResults(true)
    } catch (e) {
      // silent
    }
  }

  return (
    <header className="sticky top-[18px] z-[500] w-[calc(100%-48px)] max-w-[1420px] min-h-[76px] mx-auto mt-[18px] px-3 py-2.5 grid grid-cols-[auto_1fr_auto] items-center gap-3 bg-white/90 dark:bg-[rgba(18,31,25,0.90)] border border-[rgba(206,215,207,0.8)] dark:border-white/10 rounded-[25px] shadow-[0_10px_40px_rgba(28,44,35,0.08)] backdrop-blur-[20px]">
      {/* LEFT - Menu + JanMitra AI */}
      <div className="flex items-center gap-3">
        <button onClick={onMenuClick} className="w-[48px] h-[48px] grid place-items-center border-0 rounded-[16px] text-white bg-[#101828] hover:bg-[#0d7c66] hover:-rotate-[5deg] hover:scale-105 transition-all">
          <Menu size={21} />
        </button>
        <Link href="/" className="flex items-center gap-2.5">
          <span className="w-[37px] h-[37px] grid place-items-center rounded-[12px] bg-[#dff5ec] text-[#0d7c66]">
            <Sparkles size={19} />
          </span>
          <span className="font-heading text-[21px] font-extrabold tracking-[-1px]">
            JanMitra <span className="text-[#0d7c66]">AI</span>
          </span>
        </Link>
      </div>

      {/* CENTER - Empty (Logo right side shift) */}
      <div className="flex-1"></div>

      {/* RIGHT - Language + Ask AI + Login + HCLTech Logo */}
      <div className="flex items-center gap-2.5">
        {/* Language Toggle */}
        <div className="flex p-1 border border-[#dde2dc] dark:border-[#2c3a37] rounded-[13px] bg-[#f0f1eb] dark:bg-[#0e1914]">
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
          <span data-i18n="ask_janmitra_btn">JanMitra AI</span>
          <ArrowUpRight size={16} />
        </Link>

        {/* Login Button */}
        <Link href="/login" className="min-h-[44px] px-4 flex items-center gap-2 rounded-[14px] border border-[#dde2dc] dark:border-[#2c3a37] bg-white dark:bg-[#14231c] text-[#101828] dark:text-white font-bold text-sm hover:border-[#ff6b35] hover:text-[#ff6b35] transition-all">
          <LogIn size={16} />
          <span>Login</span>
        </Link>

         {/* HCLTech Logo - Small and to the right */}
        <div className="flex items-center px-3 py-1.5 rounded-[10px] bg-[#f0f1eb] dark:bg-[#0e1914] border border-[#dde2dc] dark:border-[#2c3a37]">
          <Image 
            src="/hcl_logo.jpg" 
            alt="HCLTech"
            width={180}
            height={60}
            className="object-contain"
          />
        </div>
      </div>
    </header>
  )
}