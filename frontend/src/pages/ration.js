import { useEffect, useState } from 'react'
import { Wheat, ArrowRight, CheckCircle2 } from 'lucide-react'
import { api } from '@/utils/api'
import { useLanguage } from '@/contexts/LanguageContext'

export default function RationGuides() {
  const { t } = useLanguage()
  const [processes, setProcesses] = useState([])
  const [selected, setSelected] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => { api.rationProcesses().then(setProcesses).catch(err => setError(err.message)) }, [])
  const choose = async key => {
    try { setSelected(await api.rationProcess(key)) } catch (err) { setError(err.message) }
  }

  return (
    <main className="max-w-6xl mx-auto px-5 py-14">
      <section className="p-9 sm:p-14 rounded-[34px] bg-[#0b6847] text-white">
        <Wheat size={40} className="text-[#dff45f]" />
        <h1 className="mt-5 text-5xl font-extrabold tracking-[-0.05em]">{t('ration_process_guides')}</h1>
        <p className="mt-3 text-white/70">{t('ration_process_subtitle')}</p>
      </section>
      {error && <p className="mt-5 text-red-600">{error}</p>}
      <div className="grid lg:grid-cols-[360px_1fr] gap-6 mt-7">
        <aside className="space-y-3">
          {processes.map(item => <button key={item.key} onClick={() => choose(item.key)} className="w-full p-5 flex items-center gap-3 rounded-2xl border border-[#d0d5dd] bg-white dark:bg-[#17201f] text-left hover:border-[#0b6847]"><span className="flex-1 font-bold">{item.title}</span><ArrowRight size={18} /></button>)}
        </aside>
        <section className="min-h-[430px] p-8 rounded-[28px] bg-white dark:bg-[#17201f] border border-[#e4e8ed]">
          {!selected ? <p className="text-[#667085]">{t('select_ration_service')}</p> : <>
            <h2 className="text-3xl font-extrabold">{selected.title}</h2>
            <p className="mt-4 text-[#667085] leading-relaxed">{selected.explanation}</p>
            <div className="mt-7 space-y-4">{selected.steps.map((step, index) => <div key={step} className="flex gap-4"><CheckCircle2 className="text-[#0b6847] shrink-0" /><div><strong>{t('step_number', { number: index + 1 })}</strong><p className="text-[#667085]">{step}</p></div></div>)}</div>
          </>}
        </section>
      </div>
    </main>
  )
}
