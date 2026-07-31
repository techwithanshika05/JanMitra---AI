import { useEffect, useRef, useState } from 'react'
import { FileText, Upload, Send, ShieldCheck } from 'lucide-react'
import { api } from '@/utils/api'
import { useLanguage } from '@/contexts/LanguageContext'

export default function Documents() {
  const { t, language: interfaceLanguage } = useLanguage()
  const inputRef = useRef(null)
  const [document, setDocument] = useState(null)
  const [question, setQuestion] = useState('')
  const [answers, setAnswers] = useState([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [language, setLanguage] = useState('en')

  useEffect(() => {
    setLanguage(interfaceLanguage === 'hinglish' ? 'hi' : interfaceLanguage)
  }, [interfaceLanguage])

  const upload = async file => {
    setBusy(true); setError('')
    try { setDocument(await api.uploadDocument(file)); setAnswers([]) } catch (err) { setError(err.message) } finally { setBusy(false) }
  }
  const ask = async event => {
    event.preventDefault()
    if (!document || !question.trim()) return
    setBusy(true); setError('')
    try {
      const response = await api.askDocument({ doc_id: document.doc_id, question, language })
      setAnswers(previous => [...previous, { question, ...response }])
      setQuestion('')
    } catch (err) { setError(err.message) } finally { setBusy(false) }
  }

  return (
    <main className="max-w-5xl mx-auto px-5 py-14">
      <section className="p-9 sm:p-12 rounded-[34px] bg-[#101828] text-white">
        <FileText size={38} className="text-[#ffb16c]" />
        <h1 className="mt-5 text-5xl font-extrabold tracking-[-0.05em]">{t('ask_your_document')}</h1>
        <p className="mt-3 text-white/65">{t('document_upload_desc')}</p>
      </section>
      <button onClick={() => inputRef.current?.click()} className="w-full mt-7 p-10 border-2 border-dashed border-[#d0d5dd] rounded-[28px] bg-white dark:bg-[#17201f]">
        <Upload className="mx-auto text-[#0d7c66]" /><strong className="block mt-3">{busy ? t('working') : document ? document.filename : t('select_text_document')}</strong>
      </button>
      <input ref={inputRef} type="file" accept=".txt,text/plain" hidden onChange={e => e.target.files?.[0] && upload(e.target.files[0])} />
      {error && <p className="mt-4 text-red-600">{error}</p>}
      {document && <form onSubmit={ask} className="mt-7 grid sm:grid-cols-[150px_1fr_48px] gap-3"><select value={language} onChange={event => setLanguage(event.target.value)} className="h-12 px-3 rounded-xl border border-[#d0d5dd] bg-white dark:bg-[#17201f]"><option value="en">English</option><option value="hi">हिन्दी</option></select><input value={question} onChange={e => setQuestion(e.target.value)} placeholder={t('ask_document_placeholder')} className="h-12 px-4 rounded-xl border border-[#d0d5dd] bg-white dark:bg-[#17201f]" /><button disabled={busy} className="h-12 grid place-items-center rounded-xl bg-[#0d7c66] text-white"><Send size={19} /></button></form>}
      <section className="mt-6 space-y-4">{answers.map((answer, index) => <article key={index} className="p-6 rounded-2xl bg-white dark:bg-[#17201f] border border-[#e4e8ed]"><strong>{answer.question}</strong><p className="mt-3 text-[#667085]">{answer.answer}</p><div className="mt-4 flex gap-2 text-xs"><ShieldCheck size={15} className="text-[#0d7c66]" />{t('grounded')}: {answer.is_grounded ? t('yes') : t('no')} · {t('confidence')}: {Math.round(answer.confidence * 100)}%</div>{answer.sources?.length > 0 && <div className="mt-3 text-xs text-[#667085]">{t('source')}: {answer.sources.map(source => `${source.title} (${Math.round(source.score * 100)}%)`).join(', ')}</div>}</article>)}</section>
    </main>
  )
}
