import Link from 'next/link'
import { Menu, Sparkles, Search, Sun, Moon, ArrowUpRight } from 'lucide-react'
import { useTheme } from '@/hooks/useTheme'
import { useLanguage } from '@/contexts/LanguageContext'
import { useState, useRef, useEffect } from 'react'

export default function Navbar({ onMenuClick }) {
  const { theme, toggleTheme } = useTheme()
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
    <header className="sticky top-[18px] z-[500] w-[calc(100%-48px)] max-w-[1420px] min-h-[76px] mx-auto mt-[18px] px-3 py-2.5 grid grid-cols-[auto_1fr_auto] items-center gap-5 bg-white/90 dark:bg-[rgba(18,31,25,0.90)] border border-[rgba(206,215,207,0.8)] dark:border-white/10 rounded-[25px] shadow-[0_10px_40px_rgba(28,44,35,0.08)] backdrop-blur-[20px]">
      {/* Left */}
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

      {/* Search */}
      <div ref={searchRef} className="relative w-full">
        <div className="flex items-center h-[50px] px-4 border border-[#dde2dc] dark:border-[#2c3a37] rounded-[16px] bg-[#f0f1eb] dark:bg-[#0e1914] focus-within:bg-white dark:focus-within:bg-[#14231c] focus-within:border-[#0d7c66] focus-within:shadow-[0_0_0_4px_rgba(13,124,102,0.09)] transition-all">
          <Search size={19} className="text-[#5f6c65] dark:text-[#94a3b8]" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder="Search schemes, services or questions..."
            className="w-full px-3 py-0 border-0 outline-none bg-transparent text-[#15201b] dark:text-[#edf5f2] text-[15px] font-medium placeholder:text-[#8b9690] dark:placeholder:text-[#64748b]"
          />
          <span className="flex-shrink-0 px-2 py-1 border border-[#dde2dc] dark:border-[#2c3a37] rounded-[7px] bg-white dark:bg-[#14231c] text-[#8b9690] dark:text-[#94a3b8] text-[11px] font-bold">Search</span>
        </div>
        {showResults && searchResults.length > 0 && (
          <div className="absolute top-full mt-3 left-0 right-0 max-h-[400px] p-2 overflow-y-auto bg-white dark:bg-[#14231c] border border-[#dde2dc] dark:border-[#2c3a37] rounded-[18px] shadow-md custom-scrollbar">
            {searchResults.slice(0, 6).map((result, i) => (
              <div key={i} className="p-3 flex items-center gap-3 rounded-[12px] hover:bg-[#f0f1eb] dark:hover:bg-[#1a2a22] cursor-pointer">
                <span className="px-2 py-0.5 rounded-[6px] bg-[#dff5ec] dark:bg-[#1a3a2e] text-[#075c4d] dark:text-[#6ef0ca] text-[10px] font-extrabold uppercase">{result.type || 'Result'}</span>
                <span className="text-[14px] font-semibold text-[#15201b] dark:text-[#edf5f2]">{result.title || result.question || result.name || ''}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Right */}
      <div className="flex items-center gap-2.5">
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
        <button onClick={toggleTheme} className="w-[44px] h-[44px] grid place-items-center border border-[#dde2dc] dark:border-[#2c3a37] rounded-[14px] bg-white dark:bg-[#14231c] text-[#15201b] dark:text-[#edf5f2] hover:text-[#ff6b35] hover:rotate-[8deg] transition-all">
          {theme === 'light' ? <Sun size={19} /> : <Moon size={19} />}
        </button>
        <Link href="/chat" className="min-h-[44px] px-4 flex items-center gap-2 rounded-[14px] bg-[#ff6b35] text-white font-extrabold text-sm shadow-[0_8px_22px_rgba(255,107,53,0.22)] hover:-translate-y-0.5 hover:shadow-[0_12px_28px_rgba(255,107,53,0.30)] transition-all">
          <span className="w-[7px] h-[7px] rounded-full bg-white shadow-[0_0_0_4px_rgba(255,255,255,0.18)]"></span>
          <span>Ask AI</span>
          <ArrowUpRight size={16} />
        </Link>
      </div>
    </header>
  )
}