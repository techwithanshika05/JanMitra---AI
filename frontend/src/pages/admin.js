import { useState, useEffect } from 'react'
import { RefreshCw, MessagesSquare, ThumbsUp, ThumbsDown, Sparkles, TrendingUp, ShieldCheck } from 'lucide-react'

export default function Admin() {
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState(null)

  const loadStats = async () => {
    setLoading(true)
    try {
      const res = await fetch('/api/admin/stats')
      const data = await res.json()
      if (data.success) setStats(data)
    } catch (e) {
      console.error('Failed to load stats:', e)
      setStats({
        total_queries: 0,
        feedback: { total_feedback: 0, thumbs_up: 0, thumbs_down: 0, satisfaction_rate: null, top_queries: [], recent: [] }
      })
    }
    setLoading(false)
  }

  useEffect(() => {
    loadStats()
  }, [])

  const fb = stats?.feedback || {}

  return (
    <div className="admin-workspace max-w-[1500px] mx-auto px-4 sm:px-8 py-8 sm:py-12">
      {/* Intro */}
      <section className="relative min-h-[340px] flex flex-col sm:flex-row items-end justify-between gap-12 p-8 sm:p-14 rounded-[34px] overflow-hidden bg-gradient-to-br from-[#09203f] via-[#123b63] to-[#096b72] text-white">
        <div className="relative z-10 max-w-[760px]">
          <div className="flex items-center gap-2.5 mb-6 text-[12px] font-extrabold tracking-[0.16em] text-[#8ff5da]">
            <span className="w-2 h-2 rounded-full bg-[#5ee8ba] shadow-[0_0_0_6px_rgba(94,232,186,0.13)] animate-pulse"></span>
            LIVE SYSTEM OVERVIEW
          </div>
          <h1 className="text-[clamp(42px,5vw,72px)] leading-[0.98] tracking-[-0.055em] font-extrabold">
            See what's happening<br />
            inside <span className="text-[#6ef0ca]">JanMitra AI.</span>
          </h1>
          <p className="max-w-[620px] mt-6 text-[17px] leading-relaxed text-white/75">Real citizen interactions, AI usage and feedback — presented directly from the current application logs.</p>
        </div>
        <button onClick={loadStats} disabled={loading} className="relative z-10 flex items-center gap-3.5 px-5 py-3 pl-3 rounded-[18px] border border-white/20 bg-white/10 backdrop-blur-sm text-white hover:bg-white hover:text-[#09203f] transition-all disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0">
          <span className="w-[46px] h-[46px] grid place-items-center rounded-[13px] bg-[#6ef0ca] text-[#09203f]">
            <RefreshCw size={20} className={loading ? 'animate-spin' : ''} />
          </span>
          <span className="flex flex-col text-left text-sm font-bold">
            <small className="text-[10px] font-medium opacity-65">Latest metrics</small>
            Refresh dashboard
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
                <strong className="text-[18px] text-[#162d2b] dark:text-[#edf7f4]">AI Queries</strong>
                <span className="block text-[13px] text-[#7a8987] dark:text-[#94a3b8]">Total conversations handled</span>
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
                <strong className="text-[18px] text-[#162d2b] dark:text-[#edf7f4]">Positive</strong>
                <span className="block text-[13px] text-[#7a8987] dark:text-[#94a3b8]">Helpful responses reported</span>
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
                <strong className="text-[18px] text-[#162d2b] dark:text-[#edf7f4]">Needs Work</strong>
                <span className="block text-[13px] text-[#7a8987] dark:text-[#94a3b8]">Negative responses reported</span>
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
                <strong className="text-[18px] text-[#18201d]">Satisfaction</strong>
                <span className="block text-[13px] text-[rgba(24,32,29,0.67)]">Overall feedback performance</span>
              </div>
            </div>
          </section>

          {/* Insights */}
          <section className="grid grid-cols-1 lg:grid-cols-[.9fr_1.1fr] gap-6 mt-6">
            {/* Top Queries */}
            <article className="min-h-[530px] p-8 border border-[#e4e8ed] dark:border-[#293533] rounded-[30px] bg-white dark:bg-[#17201f]">
              <div className="flex justify-between items-start gap-5 mb-9">
                <div>
                  <span className="block font-mono text-[10px] font-bold tracking-[0.12em] text-[#118b77] mb-3">01 / DISCOVERY</span>
                  <h2 className="text-[35px] leading-[1.05] tracking-[-0.04em] text-[#142321] dark:text-[#edf7f4]">What citizens<br />ask the most.</h2>
                </div>
                <span className="w-[50px] h-[50px] grid place-items-center rounded-full bg-[#e8f7f3] text-[#118b77]">
                  <TrendingUp size={24} />
                </span>
              </div>
              <div className="space-y-0">
                {fb.top_queries?.length === 0 ? (
                  <div className="min-h-[180px] flex flex-col items-center justify-center gap-3 text-center text-[14px] text-[#899694] dark:text-[#94a3b8]">
                    <Search size={30} className="opacity-55" />
                    <span>No query activity yet.</span>
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
                    <span className="block font-mono text-[10px] font-bold tracking-[0.12em] text-[#6ef0ca] mb-3">02 / ACTIVITY</span>
                    <h2 className="text-[35px] leading-[1.05] tracking-[-0.04em] text-white">Citizen<br />feedback feed.</h2>
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
                      <span>No feedback recorded yet.</span>
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
              <span className="block text-[10px] font-extrabold tracking-[0.13em] text-[#118b77] mb-1">DATA INTEGRITY</span>
              <p className="text-[13px] leading-relaxed text-[#687775] dark:text-[#94a3b8]">Every number shown here comes from actual JanMitra AI activity. No demo statistics or fabricated engagement numbers are inserted.</p>
            </div>
          </section>
        </>
      )}
    </div>
  )
}

// Missing imports
const Search = ({ size, className }) => <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
const MessageCircleHeart = ({ size, className }) => <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/><path d="M12 8v4"/><path d="M12 16h.01"/></svg>