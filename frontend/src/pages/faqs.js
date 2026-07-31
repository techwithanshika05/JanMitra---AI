import { useEffect, useMemo, useState } from 'react'
import { HelpCircle, Search, ChevronDown } from 'lucide-react'
import { api } from '@/utils/api'
import { useLanguage } from '@/contexts/LanguageContext'

export default function FAQs() {
  const { t } = useLanguage()
  const [items, setItems] = useState([])
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(null)
  const [error, setError] = useState('')
  const [category, setCategory] = useState('')
  const [language, setLanguage] = useState('')

  useEffect(() => {
    setError('')
    api.faqs({ category, language }).then(setItems).catch(err => setError(err.message))
  }, [category, language])
  const filtered = useMemo(() => {
    const needle = query.toLowerCase()
    return items.filter(item => `${item.question} ${item.answer} ${item.category || ''}`.toLowerCase().includes(needle))
  }, [items, query])

  return (
    <main className="max-w-5xl mx-auto px-5 py-14">
      <section className="p-8 sm:p-12 rounded-[34px] bg-gradient-to-br from-[#09203f] to-[#096b72] text-white">
        <HelpCircle size={36} className="text-[#6ef0ca]" />
        <h1 className="mt-5 text-5xl font-extrabold tracking-[-0.05em]">{t('frequently_asked_questions')}</h1>
        <p className="mt-3 text-white/70">{t('faq_subtitle')}</p>
        <div className="mt-7 flex items-center gap-3 px-4 h-13 rounded-xl bg-white text-[#101828]">
          <Search size={18} /><input value={query} onChange={e => setQuery(e.target.value)} placeholder={t('search_questions')} className="flex-1 h-12 outline-none" />
        </div>
        <div className="mt-3 grid sm:grid-cols-2 gap-3">
          <select value={category} onChange={event => setCategory(event.target.value)} className="h-12 px-4 rounded-xl bg-white text-[#101828]">
            <option value="">{t('all_categories')}</option>
            <option value="ration">{t('ration')}</option>
            <option value="schemes">{t('schemes')}</option>
            <option value="documents">{t('documents')}</option>
            <option value="grievance">{t('grievance_label')}</option>
          </select>
          <select value={language} onChange={event => setLanguage(event.target.value)} className="h-12 px-4 rounded-xl bg-white text-[#101828]">
            <option value="">{t('all_languages')}</option>
            <option value="en">English</option>
            <option value="hi">Hindi</option>
            <option value="hinglish">Hinglish</option>
          </select>
        </div>
      </section>
      {error && <p className="mt-5 text-red-600">{error}</p>}
      <section className="mt-7 divide-y divide-[#e4e8ed] border border-[#e4e8ed] rounded-[28px] overflow-hidden bg-white dark:bg-[#17201f]">
        {filtered.map(item => (
          <article key={item.id}>
            <button onClick={() => setOpen(open === item.id ? null : item.id)} className="w-full p-6 flex items-center gap-5 text-left">
              <span className="text-xs font-black text-[#0d7c66]">{item.category || t('general')}</span>
              <strong className="flex-1">{item.question}</strong>
              <ChevronDown className={open === item.id ? 'rotate-180' : ''} />
            </button>
            {open === item.id && <div className="px-6 pb-6 text-[#667085] leading-relaxed"><p>{item.answer}</p>{item.source && <small className="block mt-3">{t('source')}: {item.source}</small>}</div>}
          </article>
        ))}
      </section>
    </main>
  )
}
