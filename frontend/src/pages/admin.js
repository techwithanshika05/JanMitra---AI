import { useState, useEffect } from 'react'
import { RefreshCw, MessagesSquare, ThumbsUp, ThumbsDown, Sparkles, TrendingUp, ShieldCheck, Search, MessageCircleHeart, Upload, FileText, AlertTriangle, LockKeyhole, LogIn } from 'lucide-react'
import { useLanguage } from '@/contexts/LanguageContext'
import { api } from '@/utils/api'
import { useAuth } from '@/contexts/AuthContext'

export default function Admin() {
  const { t } = useLanguage()
  const { user, loading: authLoading, completeAuth } = useAuth()
  const [loading, setLoading] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loginError, setLoginError] = useState('')
  const [loginBusy, setLoginBusy] = useState(false)
  const [stats, setStats] = useState(null)
  const [documents, setDocuments] = useState([])
  const [missing, setMissing] = useState([])
  const [checklistStats, setChecklistStats] = useState(null)
  const [adminError, setAdminError] = useState('')
  const [events, setEvents] = useState([])
  const isAdmin = user?.role === 'admin'

  const loadStats = async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('janmitra_token')
      const headers = token ? { Authorization: `Bearer ${token}` } : {}
      const [summaryRes, feedbackRes, missingData, documentData, checklistData, eventData] = await Promise.all([
        fetch('/api/admin/summary', { headers, credentials: 'include' }),
        fetch('/api/admin/feedback', { headers, credentials: 'include' }),
        api.missingKnowledge(),
        api.knowledgeDocuments(),
        api.checklistAnalytics(),
        api.eventsByType()
      ])
      if (!summaryRes.ok) throw new Error('Admin login required')
      const summary = await summaryRes.json()
      const recent = feedbackRes.ok ? await feedbackRes.json() : []
      setMissing(missingData)
      setDocuments(documentData)
      setChecklistStats(checklistData)
      setEvents(eventData)
      setAdminError('')
      const positive = recent.filter(item => item.rating >= 4).length
      const negative = recent.filter(item => item.rating <= 2).length
      setStats({
        total_queries: summary.total_chats,
        feedback: {
          total_feedback: recent.length,
          thumbs_up: positive,
          thumbs_down: negative,
          satisfaction_rate: recent.length ? Math.round((positive / recent.length) * 100) : null,
          top_queries: (summary.top_questions || []).map(item => ({
            query: item.question,
            count: item.count
          })),
          recent: recent.map(item => ({
            type: item.rating >= 4 ? 'thumbs_up' : item.rating <= 2 ? 'thumbs_down' : 'general',
            rating: item.rating,
            comment: item.comment,
            timestamp: item.created_at
          }))
        }
      })
    } catch (e) {
      console.error('Failed to load stats:', e)
      setAdminError(e.message)
      setStats({
        total_queries: 0,
        feedback: { total_feedback: 0, thumbs_up: 0, thumbs_down: 0, satisfaction_rate: null, top_queries: [], recent: [] }
      })
    }
    setLoading(false)
  }

  useEffect(() => {
    if (isAdmin) loadStats()
  }, [isAdmin])

  const loginAdmin = async event => {
    event.preventDefault()
    setLoginBusy(true)
    setLoginError('')
    try {
      const data = await api.adminLogin({ email, password })
      if (data.user?.role !== 'admin') throw new Error('Admin access required')
      completeAuth(data, 'Admin login successful')
      setPassword('')
    } catch (error) {
      setLoginError(error.message || 'Invalid admin credentials')
    } finally {
      setLoginBusy(false)
    }
  }

  const uploadKnowledge = async event => {
    const file = event.target.files?.[0]
    if (!file) return
    setLoading(true)
    try { await api.uploadKnowledgeDocument(file); await loadStats() } catch (error) { setAdminError(error.message); setLoading(false) }
  }

  const fb = stats?.feedback || {}

  if (authLoading) {
    return <div className="min-h-[70vh] grid place-items-center"><RefreshCw className="animate-spin text-[#0d7c66]" /></div>
  }

  if (!isAdmin) {
    return (
      <main className="min-h-[calc(100vh-90px)] grid place-items-center px-4 py-12 bg-[#f7faf9] dark:bg-[#0b1210]">
        <section className="w-full max-w-md p-8 sm:p-10 rounded-[30px] border border-[#dfe8e4] dark:border-white/10 bg-white dark:bg-[#14231c] shadow-[0_24px_70px_rgba(16,39,31,.12)]">
          <span className="w-14 h-14 grid place-items-center rounded-2xl bg-[#e5f7f1] text-[#0d7c66]">
            <LockKeyhole size={26} />
          </span>
          <h1 className="mt-6 text-4xl font-black tracking-[-.04em] text-[#10271f] dark:text-white">Admin login</h1>
          <p className="mt-2 text-sm leading-relaxed text-[#667085]">Sign in with the authorized JanMitra administrator account to view analytics.</p>
          {user && <p className="mt-4 p-3 rounded-xl bg-amber-50 text-amber-800 text-sm">The current account is not an administrator.</p>}
          <form onSubmit={loginAdmin} className="mt-7 space-y-5">
            <label className="block">
              <span className="block mb-2 text-sm font-bold">Admin email</span>
              <input type="email" required autoComplete="username" value={email} onChange={event => setEmail(event.target.value)} className="w-full h-12 px-4 rounded-xl border border-[#d8e1dd] dark:border-white/10 bg-white dark:bg-[#0e1914] outline-none focus:border-[#0d7c66]" />
            </label>
            <label className="block">
              <span className="block mb-2 text-sm font-bold">Password</span>
              <input type="password" required autoComplete="current-password" value={password} onChange={event => setPassword(event.target.value)} className="w-full h-12 px-4 rounded-xl border border-[#d8e1dd] dark:border-white/10 bg-white dark:bg-[#0e1914] outline-none focus:border-[#0d7c66]" />
            </label>
            {loginError && <p role="alert" className="p-3 rounded-xl bg-red-50 text-red-700 text-sm">{loginError}</p>}
            <button type="submit" disabled={loginBusy} className="w-full h-12 flex items-center justify-center gap-2 rounded-xl bg-[#0d7c66] text-white font-extrabold disabled:opacity-60">
              {loginBusy ? <RefreshCw size={18} className="animate-spin" /> : <LogIn size={18} />}
              {loginBusy ? 'Signing in...' : 'Open analytics'}
            </button>
          </form>
        </section>
      </main>
    )
  }

  return (
    <div className="admin-workspace max-w-[1500px] mx-auto px-4 sm:px-8 py-8 sm:py-12">
      {/* Intro */}
      <section className="relative min-h-[340px] flex flex-col sm:flex-row items-end justify-between gap-12 p-8 sm:p-14 rounded-[34px] overflow-hidden bg-gradient-to-br from-[#09203f] via-[#123b63] to-[#096b72] text-white">
        <div className="relative z-10 max-w-[760px]">
          <div className="flex items-center gap-2.5 mb-6 text-[12px] font-extrabold tracking-[0.16em] text-[#8ff5da]">
            <span className="w-2 h-2 rounded-full bg-[#5ee8ba] shadow-[0_0_0_6px_rgba(94,232,186,0.13)] animate-pulse"></span>
            <span data-i18n="live_system">LIVE SYSTEM OVERVIEW</span>
          </div>
          <h1 className="text-[clamp(42px,5vw,72px)] leading-[0.98] tracking-[-0.055em] font-extrabold whitespace-pre-line" data-i18n="see_inside">
            See what's happening<br />
            inside <span className="text-[#6ef0ca]">JanMitra AI.</span>
          </h1>
          <p className="max-w-[620px] mt-6 text-[17px] leading-relaxed text-white/75" data-i18n="admin_desc">Real citizen interactions, AI usage and feedback — presented directly from the current application logs.</p>
        </div>
        <button onClick={loadStats} disabled={loading} className="relative z-10 flex items-center gap-3.5 px-5 py-3 pl-3 rounded-[18px] border border-white/20 bg-white/10 backdrop-blur-sm text-white hover:bg-white hover:text-[#09203f] transition-all disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0">
          <span className="w-[46px] h-[46px] grid place-items-center rounded-[13px] bg-[#6ef0ca] text-[#09203f]">
            <RefreshCw size={20} className={loading ? 'animate-spin' : ''} />
          </span>
          <span className="flex flex-col text-left text-sm font-bold">
            <small className="text-[10px] font-medium opacity-65" data-i18n="latest_metrics">Latest metrics</small>
            <span data-i18n="refresh_dashboard">Refresh dashboard</span>
          </span>
        </button>
        <div className="absolute w-[280px] h-[280px] -right-20 -bottom-[120px] border-[55px] border-white/10 rounded-full"></div>
      </section>

      {/* Loading */}
      {loading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-1 mt-6 rounded-[28px] overflow-hidden">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-[280px] bg-gradient-to-r from-[#eef1f0] via-[#f8f9f9] to-[#eef1f0] bg-[length:200%_100%] animate-skeleton"></div>
          ))}
        </div>
      )}

      {/* Content */}
      {!loading && (
        <>
          {adminError && <div className="mt-6 p-4 rounded-xl bg-red-50 text-red-700">{adminError}</div>}
          {/* Metrics */}
          <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 mt-6 border border-[#e4e8ed] dark:border-[#293533] rounded-[28px] overflow-hidden bg-white dark:bg-[#17201f]">
            <div className="min-h-[280px] p-7 flex flex-col justify-between border-r border-[#e4e8ed] dark:border-[#293533] hover:bg-[#f7faf9] dark:hover:bg-[#1d2927] transition-colors">
              <div className="flex justify-between items-center text-[#7d8988]">
                <span className="font-mono text-[11px] tracking-[0.1em]">01</span>
                <MessagesSquare size={25} />
              </div>
              <div className="my-5 text-[clamp(52px,5vw,82px)] leading-none font-extrabold tracking-[-0.07em] text-[#112d2b] dark:text-[#edf7f4]">
                {stats?.total_queries ?? 0}
              </div>
              <div>
                <strong className="text-[18px] text-[#162d2b] dark:text-[#edf7f4]" data-i18n="ai_queries">AI Queries</strong>
                <span className="block text-[13px] text-[#7a8987] dark:text-[#94a3b8]" data-i18n="total_conversations">Total conversations handled</span>
              </div>
            </div>
            <div className="min-h-[280px] p-7 flex flex-col justify-between border-r border-[#e4e8ed] dark:border-[#293533] hover:bg-[#f7faf9] dark:hover:bg-[#1d2927] transition-colors">
              <div className="flex justify-between items-center text-[#7d8988]">
                <span className="font-mono text-[11px] tracking-[0.1em]">02</span>
                <ThumbsUp size={25} />
              </div>
              <div className="my-5 text-[clamp(52px,5vw,82px)] leading-none font-extrabold tracking-[-0.07em] text-[#09875f]">
                {fb.thumbs_up ?? 0}
              </div>
              <div>
                <strong className="text-[18px] text-[#162d2b] dark:text-[#edf7f4]" data-i18n="positive">Positive</strong>
                <span className="block text-[13px] text-[#7a8987] dark:text-[#94a3b8]" data-i18n="helpful_responses">Helpful responses reported</span>
              </div>
            </div>
            <div className="min-h-[280px] p-7 flex flex-col justify-between border-r border-[#e4e8ed] dark:border-[#293533] hover:bg-[#f7faf9] dark:hover:bg-[#1d2927] transition-colors">
              <div className="flex justify-between items-center text-[#7d8988]">
                <span className="font-mono text-[11px] tracking-[0.1em]">03</span>
                <ThumbsDown size={25} />
              </div>
              <div className="my-5 text-[clamp(52px,5vw,82px)] leading-none font-extrabold tracking-[-0.07em] text-[#e25555]">
                {fb.thumbs_down ?? 0}
              </div>
              <div>
                <strong className="text-[18px] text-[#162d2b] dark:text-[#edf7f4]" data-i18n="needs_work">Needs Work</strong>
                <span className="block text-[13px] text-[#7a8987] dark:text-[#94a3b8]" data-i18n="negative_responses">Negative responses reported</span>
              </div>
            </div>
            <div className="min-h-[280px] p-7 flex flex-col justify-between bg-[#f5b942] hover:bg-[#ffc84e] transition-colors">
              <div className="flex justify-between items-center text-[rgba(24,32,29,0.67)]">
                <span className="font-mono text-[11px] tracking-[0.1em]">04</span>
                <Sparkles size={25} />
              </div>
              <div className="my-5 text-[clamp(52px,5vw,82px)] leading-none font-extrabold tracking-[-0.07em] text-[#18201d]">
                {fb.satisfaction_rate != null ? fb.satisfaction_rate + '%' : '—'}
              </div>
              <div>
                <strong className="text-[18px] text-[#18201d]" data-i18n="satisfaction">Satisfaction</strong>
                <span className="block text-[13px] text-[rgba(24,32,29,0.67)]" data-i18n="overall_feedback">Overall feedback performance</span>
              </div>
            </div>
          </section>

          <section className="grid lg:grid-cols-3 gap-6 mt-6">
            <article className="p-7 rounded-[28px] bg-white dark:bg-[#17201f] border border-[#e4e8ed]">
              <Upload className="text-[#118b77]" /><h2 className="mt-4 text-2xl font-extrabold">{t('knowledge_documents')}</h2>
              <p className="mt-2 text-sm text-[#667085]">{t('indexed_uploads', { count: documents.length })}</p>
              <label className="mt-5 h-11 px-4 inline-flex items-center rounded-xl bg-[#118b77] text-white font-bold cursor-pointer">{t('upload_txt')}<input type="file" accept=".txt" hidden onChange={uploadKnowledge} /></label>
              <div className="mt-4 space-y-2">{documents.slice(0, 5).map(document => <div key={document.id} className="text-sm flex gap-2"><FileText size={15} />{document.title} ({t('chunks_count', { count: document.chunk_count })})</div>)}</div>
            </article>
            <article className="p-7 rounded-[28px] bg-white dark:bg-[#17201f] border border-[#e4e8ed]">
              <AlertTriangle className="text-[#ff6b35]" /><h2 className="mt-4 text-2xl font-extrabold">{t('knowledge_gaps')}</h2>
              <p className="mt-2 text-sm text-[#667085]">{t('low_confidence_answers', { count: missing.length })}</p>
              <div className="mt-4 space-y-3">{missing.slice(0, 6).map((item, index) => <div key={index} className="p-3 rounded-xl bg-[#fff7e7] text-sm">{item.message}<span className="block text-xs text-[#74501e]">{t('confidence_percent', { percent: Math.round((item.confidence || 0) * 100) })}</span></div>)}</div>
            </article>
            <article className="p-7 rounded-[28px] bg-white dark:bg-[#17201f] border border-[#e4e8ed]">
              <ShieldCheck className="text-[#176bff]" /><h2 className="mt-4 text-2xl font-extrabold">{t('checklist_analytics')}</h2>
              {checklistStats && <div className="mt-5 space-y-3 text-sm"><p>{t('total')}: <strong>{checklistStats.total_checklists}</strong></p><p>{t('completion')}: <strong>{Math.round(checklistStats.completion_rate)}%</strong></p><p>{t('abandonment')}: <strong>{Math.round(checklistStats.abandonment_rate)}%</strong></p><p>{t('outdated')}: <strong>{checklistStats.outdated_count}</strong></p><p>{t('storage')}: <strong>{checklistStats.active_storage_mode}</strong></p></div>}
              {events.length > 0 && <div className="mt-5 pt-5 border-t space-y-2 text-sm">{events.map(item => <p key={item.event_type}>{item.event_type}: <strong>{item.count}</strong></p>)}</div>}
            </article>
          </section>

          {/* Insights */}
          <section className="grid grid-cols-1 lg:grid-cols-[.9fr_1.1fr] gap-6 mt-6">
            {/* Top Queries */}
            <article className="min-h-[530px] p-8 border border-[#e4e8ed] dark:border-[#293533] rounded-[30px] bg-white dark:bg-[#17201f]">
              <div className="flex justify-between items-start gap-5 mb-9">
                <div>
                  <span className="block font-mono text-[10px] font-bold tracking-[0.12em] text-[#118b77] mb-3" data-i18n="discovery">01 / DISCOVERY</span>
                  <h2 className="text-[35px] leading-[1.05] tracking-[-0.04em] text-[#142321] dark:text-[#edf7f4]" data-i18n="what_ask_most">What citizens ask the most.</h2>
                </div>
                <span className="w-[50px] h-[50px] grid place-items-center rounded-full bg-[#e8f7f3] text-[#118b77]">
                  <TrendingUp size={24} />
                </span>
              </div>
              <div className="space-y-0">
                {fb.top_queries?.length === 0 ? (
                  <div className="min-h-[180px] flex flex-col items-center justify-center gap-3 text-center text-[14px] text-[#899694] dark:text-[#94a3b8]">
                    <Search size={30} className="opacity-55" />
                    <span data-i18n="no_query">No query activity yet.</span>
                  </div>
                ) : (
                  fb.top_queries?.map((q, i) => (
                    <div key={i} className="py-4 border-b border-[#edf0ef] dark:border-[#293533] text-[15px] flex items-center gap-3">
                      <span className="text-[0.72rem] text-[#7a8987] dark:text-[#94a3b8]">#{i + 1}</span>
                      <span className="flex-1">{q.query.slice(0, 80)}{q.query.length > 80 ? '…' : ''}</span>
                      <span className="text-[#118b77] font-bold">{q.count}</span>
                    </div>
                  ))
                )}
              </div>
            </article>

            {/* Recent Feedback */}
            <article className="relative min-h-[530px] p-8 rounded-[30px] bg-[#142a2a] text-white overflow-hidden">
              <div className="absolute w-[330px] h-[330px] -top-[190px] -right-[120px] rounded-full bg-[#0e806c] blur-[20px] opacity-35"></div>
              <div className="relative z-10">
                <div className="flex justify-between items-start gap-5 mb-9">
                  <div>
                    <span className="block font-mono text-[10px] font-bold tracking-[0.12em] text-[#6ef0ca] mb-3" data-i18n="activity">02 / ACTIVITY</span>
                    <h2 className="text-[35px] leading-[1.05] tracking-[-0.04em] text-white" data-i18n="feedback_feed">Citizen feedback feed.</h2>
                  </div>
                  <span className="inline-flex items-center gap-2 px-3 py-2 border border-white/15 rounded-full font-mono text-[10px] font-bold text-[#9af2d8]">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#6ef0ca]"></span>
                    LIVE
                  </span>
                </div>
                <div className="space-y-0">
                  {fb.recent?.length === 0 ? (
                    <div className="min-h-[180px] flex flex-col items-center justify-center gap-3 text-center text-[14px] text-white/55">
                      <MessageCircleHeart size={30} className="opacity-55" />
                      <span data-i18n="no_feedback">No feedback recorded yet.</span>
                    </div>
                  ) : (
                    fb.recent?.map((f, i) => (
                      <div key={i} className="py-4 border-b border-white/10 text-white/80">
                        <span className={`text-xs font-bold ${f.type === 'thumbs_up' ? 'text-[#6ef0ca]' : f.type === 'thumbs_down' ? 'text-[#ff8c8c]' : 'text-[#f4c95d]'}`}>
                          {f.type === 'thumbs_up' ? '👍 Thumbs Up' : f.type === 'thumbs_down' ? '👎 Thumbs Down' : '⭐ General'}
                        </span>
                        {f.rating && <span className="text-xs"> · Rating: {f.rating}/5</span>}
                        {f.comment && <span className="text-xs"> · "{f.comment.slice(0, 60)}"</span>}
                        {f.page && <span className="text-xs"> · Page: {f.page}</span>}
                        <br />
                        <span className="text-[10px] text-white/40">{f.timestamp ? new Date(f.timestamp).toLocaleString() : '—'}</span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </article>
          </section>

          {/* Integrity Notice */}
          <section className="mt-6 p-6 border border-dashed border-[#b8c7c4] rounded-[22px] bg-white/40 dark:bg-[#17201f] flex items-start gap-4">
            <span className="w-[47px] h-[47px] flex-shrink-0 grid place-items-center rounded-[14px] bg-[#e8f7f3] text-[#118b77]">
              <ShieldCheck size={24} />
            </span>
            <div>
              <span className="block text-[10px] font-extrabold tracking-[0.13em] text-[#118b77] mb-1" data-i18n="data_integrity">DATA INTEGRITY</span>
              <p className="text-[13px] leading-relaxed text-[#687775] dark:text-[#94a3b8]" data-i18n="data_integrity_desc">Every number shown here comes from actual JanMitra AI activity. No demo statistics or fabricated engagement numbers are inserted.</p>
            </div>
          </section>
        </>
      )}
    </div>
  )
}
