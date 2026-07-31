import { useEffect, useState } from 'react'
import {
  Archive, ArchiveRestore, Bell, Check, Lightbulb, ListChecks,
  RefreshCw, Save, Trash2
} from 'lucide-react'
import { api } from '@/utils/api'
import { useLanguage } from '@/contexts/LanguageContext'

export default function SavedChecklists() {
  const { t } = useLanguage()
  const [data, setData] = useState(null)
  const [guidance, setGuidance] = useState({})
  const [notes, setNotes] = useState({})
  const [reminders, setReminders] = useState({})
  const [showArchived, setShowArchived] = useState(false)
  const [error, setError] = useState('')
  const [status, setStatus] = useState('')
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    setError('')
    try { setData(await api.savedChecklists(showArchived)) }
    catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [showArchived])

  const toggle = async (checklist, item) => {
    try {
      await api.updateChecklistItem(checklist.id, item.id, { is_completed: !item.is_completed })
      await load()
    } catch (err) { setError(err.message) }
  }

  const showGuidance = async id => {
    try {
      const result = await api.checklistGuidance(id, Boolean(reminders[id]))
      setGuidance(previous => ({ ...previous, [id]: result }))
    } catch (err) { setError(err.message) }
  }

  const refresh = async id => {
    setStatus('Refreshing verified checklist knowledge...')
    try {
      const result = await api.refreshChecklist(id)
      setStatus(`Updated: ${result.new_items} new, ${result.changed_items} changed, ${result.removed_items} removed.`)
      await load()
    } catch (err) { setError(err.message); setStatus('') }
  }

  const changeLanguage = async (id, language) => {
    try { await api.updateSavedChecklist(id, { language }); await load() }
    catch (err) { setError(err.message) }
  }

  const saveNote = async (checklistId, item) => {
    try {
      await api.updateChecklistItem(checklistId, item.id, {
        user_note: notes[item.id] ?? item.user_note ?? ''
      })
      setStatus('Private checklist note saved.')
      await load()
    } catch (err) { setError(err.message) }
  }

  const archive = async id => {
    try { await api.archiveChecklist(id); await load() }
    catch (err) { setError(err.message) }
  }

  const restore = async id => {
    try { await api.restoreChecklist(id); await load() }
    catch (err) { setError(err.message) }
  }

  const remove = async id => {
    if (!confirm(t('delete_checklist_confirm'))) return
    try { await api.deleteChecklist(id); await load() }
    catch (err) { setError(err.message) }
  }

  return (
    <main className="max-w-6xl mx-auto px-5 py-14">
      <section className="p-9 sm:p-12 rounded-[34px] bg-[#17211b] text-white">
        <ListChecks size={38} className="text-[#dff45f]" />
        <h1 className="mt-5 text-5xl font-extrabold tracking-[-0.05em]">{t('saved_checklists')}</h1>
        <p className="mt-3 text-white/65">
          {t('storage_sync', { storage: data?.storage_mode || '—', sync: data?.sync_status || '—' })}
        </p>
        <div className="mt-6 flex gap-3">
          <button onClick={() => setShowArchived(false)} className={`h-10 px-4 rounded-xl font-bold ${!showArchived ? 'bg-[#dff45f] text-[#17211b]' : 'bg-white/10'}`}>{t('active')}</button>
          <button onClick={() => setShowArchived(true)} className={`h-10 px-4 rounded-xl font-bold ${showArchived ? 'bg-[#dff45f] text-[#17211b]' : 'bg-white/10'}`}>{t('archived')}</button>
        </div>
      </section>

      {loading && <p className="mt-6">{t('loading_checklists')}</p>}
      {error && <p className="mt-6 p-4 rounded-xl bg-red-50 text-red-700">{error}</p>}
      {status && <p className="mt-6 p-4 rounded-xl bg-[#edf5e6] text-[#0b6847]">{status}</p>}

      <section className="mt-7 space-y-6">
        {data?.checklists?.map(checklist => (
          <article key={checklist.id} className="p-7 rounded-[28px] bg-white dark:bg-[#17201f] border border-[#e4e8ed]">
            <div className="flex flex-wrap justify-between gap-5">
              <div>
                <span className="text-xs font-black text-[#0b6847]">{checklist.status}</span>
                <h2 className="mt-1 text-2xl font-extrabold">{checklist.service_name}</h2>
                <p className="text-sm text-[#667085]">{t('complete_percent', { percent: Math.round(checklist.progress_percentage) })} · {checklist.storage_origin} · {checklist.source_version}</p>
              </div>
              <div className="flex gap-2">
                <button title={t('guidance')} onClick={() => showGuidance(checklist.id)} className="w-11 h-11 grid place-items-center rounded-xl bg-[#edf5e6] text-[#0b6847]"><Lightbulb size={18} /></button>
                <button title={t('refresh_knowledge')} onClick={() => refresh(checklist.id)} className="w-11 h-11 grid place-items-center rounded-xl bg-blue-50 text-blue-700"><RefreshCw size={18} /></button>
                {showArchived
                  ? <button title={t('restore')} onClick={() => restore(checklist.id)} className="w-11 h-11 grid place-items-center rounded-xl bg-[#fff7e7] text-[#74501e]"><ArchiveRestore size={18} /></button>
                  : <button title={t('archive')} onClick={() => archive(checklist.id)} className="w-11 h-11 grid place-items-center rounded-xl bg-[#fff7e7] text-[#74501e]"><Archive size={18} /></button>}
                <button title={t('delete')} onClick={() => remove(checklist.id)} className="w-11 h-11 grid place-items-center rounded-xl bg-red-50 text-red-600"><Trash2 size={18} /></button>
              </div>
            </div>

            <div className="mt-5 flex flex-wrap items-center gap-4 text-sm">
              <label className="font-bold">{t('language')}
                <select value={checklist.language} onChange={event => changeLanguage(checklist.id, event.target.value)} className="ml-2 h-9 px-3 rounded-lg border bg-transparent">
                  <option value="en">English</option>
                  <option value="hi">Hindi</option>
                  <option value="hinglish">Hinglish</option>
                </select>
              </label>
              <label className="inline-flex items-center gap-2">
                <input type="checkbox" checked={Boolean(reminders[checklist.id])} onChange={event => setReminders(previous => ({ ...previous, [checklist.id]: event.target.checked }))} />
                <Bell size={15} /> {t('reminder_guidance')}
              </label>
            </div>

            <div className="mt-6 divide-y divide-[#e4e8ed]">
              {checklist.items.map(item => (
                <div key={item.id} className="py-4 flex gap-4">
                  <button onClick={() => toggle(checklist, item)} className={`w-7 h-7 shrink-0 grid place-items-center border-2 ${item.is_completed ? 'bg-[#0b6847] border-[#0b6847] text-white' : 'border-[#98a2b3]'}`}>{item.is_completed && <Check size={15} />}</button>
                  <div className="flex-1">
                    <strong className={item.is_completed ? 'line-through text-[#98a2b3]' : ''}>{item.title}</strong>
                    {item.description && <p className="text-sm text-[#667085]">{item.description}</p>}
                    <div className="mt-3 flex gap-2">
                      <input value={notes[item.id] ?? item.user_note ?? ''} onChange={event => setNotes(previous => ({ ...previous, [item.id]: event.target.value }))} maxLength={1000} placeholder={t('add_private_note')} className="flex-1 h-9 px-3 rounded-lg border bg-transparent text-sm" />
                      <button title={t('save_note')} onClick={() => saveNote(checklist.id, item)} className="w-9 grid place-items-center rounded-lg bg-[#edf5e6] text-[#0b6847]"><Save size={15} /></button>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {guidance[checklist.id] && (
              <div className="mt-5 p-5 rounded-xl bg-[#f4f7f6] dark:bg-[#101817]">
                <strong>{guidance[checklist.id].progress_summary}</strong>
                <ul className="mt-2 list-disc pl-5 text-sm text-[#667085]">{guidance[checklist.id].next_steps.map(step => <li key={step}>{step}</li>)}</ul>
                {guidance[checklist.id].reminders?.length > 0 && <div className="mt-3 text-sm"><strong>{t('reminders')}</strong><ul className="list-disc pl-5">{guidance[checklist.id].reminders.map(item => <li key={item}>{item}</li>)}</ul></div>}
              </div>
            )}
          </article>
        ))}
        {!loading && data?.checklists?.length === 0 && <p className="p-8 text-center text-[#667085]">{t('no_checklists', { status: t(showArchived ? 'archived_lower' : 'active_lower') })}</p>}
      </section>
    </main>
  )
}
