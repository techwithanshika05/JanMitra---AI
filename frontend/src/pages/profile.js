import { useEffect, useState } from 'react'
import Link from 'next/link'
import { User, History, Settings, LogOut, Merge, ListChecks } from 'lucide-react'
import { api } from '@/utils/api'
import { useAuth } from '@/contexts/AuthContext'
import { useLanguage } from '@/contexts/LanguageContext'

export default function Profile() {
  const { user: activeUser, logout: clearAuth } = useAuth()
  const { t } = useLanguage()
  const [user, setUser] = useState(null)
  const [history, setHistory] = useState(null)
  const [preferences, setPreferences] = useState({ language: 'en', state: '', preferences: {} })
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)
  const [migrationStatus, setMigrationStatus] = useState('')

  useEffect(() => {
    Promise.all([api.me(), api.identityHistory(), api.identityActivity(), api.preferences()])
      .then(([me, historyData, activityData, prefs]) => {
        setUser(me)
        setHistory({ ...historyData, items: [...(historyData.items || []), ...(activityData.items || [])].sort((a, b) => new Date(b.created_at) - new Date(a.created_at)) })
        setPreferences(prefs)
      })
      .catch(err => setError(err.message))
  }, [])
  const save = async event => {
    event.preventDefault(); setSaved(false)
    try { setPreferences(await api.updatePreferences({ language: preferences.language, state: preferences.state || null, preferences: preferences.preferences || {} })); setSaved(true) } catch (err) { setError(err.message) }
  }
  const logout = () => {
    clearAuth()
    location.href = '/'
  }
  const claimGuestData = async () => {
    setMigrationStatus('')
    try {
      const [identity, chat, checklists] = await Promise.all([
        api.claimGuestData(),
        api.migrateGuestChat(),
        api.importGuestChecklists(true)
      ])
      setMigrationStatus(`Imported guest activity, ${chat.migrated_sessions || 0} chats, and ${checklists.imported_count || 0} checklists.`)
    } catch (err) { setMigrationStatus(err.message) }
  }

  if (error && !user) return <main className="max-w-2xl mx-auto px-5 py-20"><p className="text-red-600">{error}</p><Link href="/login" className="font-bold text-[#0d7c66]">{t('sign_in')}</Link></main>
  return (
    <main className="max-w-6xl mx-auto px-5 py-14">
      <section className="p-9 rounded-[34px] bg-[#101828] text-white flex flex-wrap justify-between gap-6">
        <div className="flex gap-5">
          <span className="relative w-16 h-16 grid place-items-center rounded-2xl bg-white/10">
            <User size={30} />
            {activeUser && <i className="absolute -right-1 -bottom-1 w-4 h-4 rounded-full bg-[#12b76a] border-[3px] border-[#101828]" />}
          </span>
          <div>
            <span className="inline-flex items-center gap-2 text-xs font-bold text-[#6ef0ca]"><i className="w-2 h-2 rounded-full bg-[#12b76a]" />{t('active_account')}</span>
            <p className="mt-1 text-white/50 text-sm">{user?.public_id}</p>
            <h1 className="text-4xl font-extrabold">{user?.name || activeUser?.name || 'Loading...'}</h1>
            <p className="text-white/60">{[user?.email || activeUser?.email, user?.mobile || activeUser?.mobile].filter(Boolean).join(' · ')}</p>
          </div>
        </div>
        <button onClick={logout} className="h-11 px-5 flex items-center gap-2 rounded-xl bg-white/10"><LogOut size={17} />{t('logout')}</button>
      </section>
      <div className="grid lg:grid-cols-2 gap-6 mt-7 items-start">
        <form onSubmit={save} className="min-h-[430px] p-7 rounded-[28px] bg-white dark:bg-[#17201f] border border-[#e4e8ed]">
          <Settings className="text-[#0d7c66]" /><h2 className="mt-4 text-2xl font-extrabold">{t('preferences')}</h2>
          <label className="block mt-5"><span className="text-sm font-bold">{t('language')}</span><select value={preferences.language} onChange={e => setPreferences({ ...preferences, language: e.target.value })} className="w-full h-12 mt-2 px-4 border rounded-xl bg-transparent"><option value="en">English</option><option value="hi">हिन्दी</option><option value="hinglish">Hinglish</option></select></label>
          <label className="block mt-4"><span className="text-sm font-bold">{t('state')}</span><input value={preferences.state || ''} onChange={e => setPreferences({ ...preferences, state: e.target.value })} className="w-full h-12 mt-2 px-4 border rounded-xl bg-transparent" /></label>
          <button className="mt-5 h-11 px-6 rounded-xl bg-[#0d7c66] text-white font-bold">{t('save_preferences')}</button>{saved && <span className="ml-3 text-sm text-[#0d7c66]">{t('saved')}</span>}
        </form>
        <section className="h-[430px] min-h-0 p-7 flex flex-col overflow-hidden rounded-[28px] bg-white dark:bg-[#17201f] border border-[#e4e8ed]">
          <History className="text-[#ff6b35]" /><h2 className="mt-4 text-2xl font-extrabold">{t('recent_activity')}</h2>
          <div className="mt-5 flex-1 min-h-0 overflow-y-auto overscroll-contain pr-2 divide-y custom-scrollbar">
            {history?.items?.map(item => <div key={`${item.feature}-${item.record_id}-${item.created_at}`} className="py-4 first:pt-0"><strong>{item.title || item.feature}</strong><p className="text-sm text-[#667085]">{item.action} · {new Date(item.created_at).toLocaleString()}</p></div>)}
            {history?.items?.length === 0 && <p className="text-[#667085]">{t('no_account_activity')}</p>}
          </div>
        </section>
      </div>
      <section className="mt-6 p-7 rounded-[28px] bg-white dark:bg-[#17201f] border border-[#e4e8ed]">
        <Merge className="text-[#176bff]" />
        <h2 className="mt-4 text-2xl font-extrabold">{t('guest_data_import')}</h2>
        <p className="mt-2 text-sm text-[#667085]">{t('guest_data_import_desc')}</p>
        <button onClick={claimGuestData} className="mt-5 h-11 px-5 inline-flex items-center gap-2 rounded-xl bg-[#176bff] text-white font-bold"><ListChecks size={17} />{t('import_guest_data')}</button>
        {migrationStatus && <p className="mt-4 text-sm text-[#667085]">{migrationStatus}</p>}
      </section>
    </main>
  )
}
