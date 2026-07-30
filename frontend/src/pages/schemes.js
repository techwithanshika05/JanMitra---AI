import { useState } from 'react'
import { Sparkles, Landmark, GraduationCap, Wheat, HeartPulse, CalendarDays, BriefcaseBusiness, UsersRound, ChevronDown, Search, ArrowRight, ShieldCheck, ScanSearch, BadgeCheck, Gift, Files, MapPin, ArrowUpRight, Check, SearchX, Loader } from 'lucide-react'

export default function Schemes() {
  const [form, setForm] = useState({
    age: '',
    occupation: 'farmer',
    category: 'General',
    income: ''
  })
  const [schemes, setSchemes] = useState([])
  const [loading, setLoading] = useState(false)
  const [searching, setSearching] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSearching(true)
    setLoading(true)

    try {
      const res = await fetch('/api/schemes/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          age: parseInt(form.age),
          occupation: form.occupation,
          category: form.category,
          income: form.income || null
        })
      })
      const data = await res.json()
      setSchemes(data.schemes || [])
    } catch (e) {
      alert('Failed to load schemes. Please try again.')
    }
    setLoading(false)
    setSearching(false)
  }

  return (
    <div className="sf-page max-w-[1500px] mx-auto px-4 sm:px-8 py-7 sm:py-[70px] animate-fade-in">
      {/* INTRO */}
      <section className="relative min-h-[390px] grid grid-cols-1 lg:grid-cols-[1.25fr_0.75fr] items-center p-8 sm:p-[55px_65px] overflow-hidden bg-gradient-to-r from-[#ffefe3] via-[#ffd8b7] to-[#ffc98f] dark:from-[#3b271f] dark:via-[#5c321f] dark:to-[#5c321f] rounded-[42px]">
        <div className="relative z-10 max-w-[800px]">
          <div className="inline-flex items-center gap-2.5 mb-5 text-[13px] font-extrabold tracking-[1.7px] text-[#8d3e13] dark:text-[#ffc18d]">
            <Sparkles size={18} />
            PERSONALIZED WELFARE DISCOVERY
          </div>
          <h1 className="text-[clamp(44px,5vw,76px)] leading-[0.98] tracking-[-3.5px] font-extrabold text-[#192236] dark:text-white">
            Find government schemes
            <span className="block text-[#b64a17] dark:text-[#ffc18d]">made for your profile.</span>
          </h1>
          <p className="max-w-[690px] mt-7 text-[18px] leading-relaxed text-[#654a3d] dark:text-[#e0c3b2]">Tell us a few basic details and JanMitra AI will match your profile with relevant welfare schemes, benefits and required documents.</p>
        </div>
        <div className="relative min-h-[300px] flex items-center justify-center">
          <div className="absolute w-[250px] h-[250px] border border-dashed border-[rgba(77,44,27,0.25)] dark:border-[rgba(255,255,255,0.15)] rounded-full"></div>
          <div className="absolute w-[360px] h-[360px] border border-dashed border-[rgba(77,44,27,0.25)] dark:border-[rgba(255,255,255,0.15)] rounded-full"></div>
          <div className="relative z-10 w-[145px] h-[145px] flex items-center justify-center rounded-[42px] text-white bg-[#172033] dark:bg-[#0a0f1a] shadow-[0_30px_70px_rgba(80,40,20,0.25)]">
            <Landmark size={66} />
          </div>
          <div className="absolute top-5 left-2.5 z-20 flex items-center gap-2.5 px-4 py-3 rounded-[15px] bg-white/90 dark:bg-[#1a1a2a] shadow-[0_15px_35px_rgba(87,48,28,0.15)] text-[13px] font-bold text-[#283044] dark:text-white">
            <GraduationCap size={18} />
            Scholarship
          </div>
          <div className="absolute right-0 top-[105px] z-20 flex items-center gap-2.5 px-4 py-3 rounded-[15px] bg-white/90 dark:bg-[#1a1a2a] shadow-[0_15px_35px_rgba(87,48,28,0.15)] text-[13px] font-bold text-[#283044] dark:text-white">
            <Wheat size={18} />
            Farmer Support
          </div>
          <div className="absolute left-1.5 bottom-4 z-20 flex items-center gap-2.5 px-4 py-3 rounded-[15px] bg-white/90 dark:bg-[#1a1a2a] shadow-[0_15px_35px_rgba(87,48,28,0.15)] text-[13px] font-bold text-[#283044] dark:text-white">
            <HeartPulse size={18} />
            Healthcare
          </div>
        </div>
        <div className="absolute w-[420px] h-[420px] -right-[130px] -bottom-[230px] border-[80px] border-white/20 dark:border-white/5 rounded-full"></div>
      </section>

      {/* FINDER */}
      <section className="grid grid-cols-1 lg:grid-cols-[390px_minmax(0,1fr)] mt-7 border border-[#e4e6ec] dark:border-[#303643] rounded-[34px] overflow-hidden bg-white dark:bg-[#181d27]">
        {/* PROFILE */}
        <aside className="p-[38px_32px] bg-[#172033] dark:bg-[#0a0f1a] text-white">
          <div className="flex gap-4 items-start mb-9">
            <span className="w-[44px] h-[44px] flex-shrink-0 flex items-center justify-center rounded-[14px] bg-[#ffb16c] text-[#48200d] text-[13px] font-black">01</span>
            <div>
              <span className="block mb-1 text-[11px] tracking-[1.5px] font-extrabold opacity-60">PROFILE DETAILS</span>
              <h2 className="text-[25px] tracking-[-0.7px]">Tell us about yourself</h2>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="flex flex-col gap-6">
            <div>
              <label className="block mb-2.5 text-sm font-bold text-[#eef1f7]">Your Age</label>
              <div className="relative min-h-[57px] flex items-center border border-white/15 rounded-[15px] bg-white/10 focus-within:border-[#ffb16c] focus-within:bg-white/15 focus-within:shadow-[0_0_0_4px_rgba(255,177,108,0.11)] transition-all">
                <CalendarDays size={19} className="absolute left-4 text-[#ffb16c]" />
                <input
                  type="number"
                  value={form.age}
                  onChange={(e) => setForm({ ...form, age: e.target.value })}
                  placeholder="Example: 45"
                  required
                  className="w-full h-[57px] pl-12 pr-4 border-0 outline-none bg-transparent text-white text-[15px] font-medium placeholder:text-[#8e98aa]"
                />
              </div>
            </div>

            <div>
              <label className="block mb-2.5 text-sm font-bold text-[#eef1f7]">What do you do?</label>
              <div className="relative min-h-[57px] flex items-center border border-white/15 rounded-[15px] bg-white/10 focus-within:border-[#ffb16c] focus-within:bg-white/15 focus-within:shadow-[0_0_0_4px_rgba(255,177,108,0.11)] transition-all">
                <BriefcaseBusiness size={19} className="absolute left-4 text-[#ffb16c]" />
                <select
                  value={form.occupation}
                  onChange={(e) => setForm({ ...form, occupation: e.target.value })}
                  className="w-full h-[57px] pl-12 pr-11 appearance-none border-0 outline-none bg-transparent text-white text-[15px] font-medium cursor-pointer"
                >
                  <option value="farmer" className="text-[#172033] bg-white">Farmer / Kisan</option>
                  <option value="labour" className="text-[#172033] bg-white">Daily Wage Labour</option>
                  <option value="student" className="text-[#172033] bg-white">Student</option>
                  <option value="unemployed" className="text-[#172033] bg-white">Unemployed / Homemaker</option>
                  <option value="other" className="text-[#172033] bg-white">Other / Salaried</option>
                </select>
                <ChevronDown size={17} className="absolute right-4 pointer-events-none text-[#a9b1c0]" />
              </div>
            </div>

            <div>
              <label className="block mb-2.5 text-sm font-bold text-[#eef1f7]">Social Category</label>
              <div className="relative min-h-[57px] flex items-center border border-white/15 rounded-[15px] bg-white/10 focus-within:border-[#ffb16c] focus-within:bg-white/15 focus-within:shadow-[0_0_0_4px_rgba(255,177,108,0.11)] transition-all">
                <UsersRound size={19} className="absolute left-4 text-[#ffb16c]" />
                <select
                  value={form.category}
                  onChange={(e) => setForm({ ...form, category: e.target.value })}
                  className="w-full h-[57px] pl-12 pr-11 appearance-none border-0 outline-none bg-transparent text-white text-[15px] font-medium cursor-pointer"
                >
                  <option value="General" className="text-[#172033] bg-white">General</option>
                  <option value="OBC" className="text-[#172033] bg-white">OBC</option>
                  <option value="SC" className="text-[#172033] bg-white">SC (Scheduled Caste)</option>
                  <option value="ST" className="text-[#172033] bg-white">ST (Scheduled Tribe)</option>
                  <option value="BPL" className="text-[#172033] bg-white">BPL (Below Poverty Line)</option>
                </select>
                <ChevronDown size={17} className="absolute right-4 pointer-events-none text-[#a9b1c0]" />
              </div>
            </div>

            <div>
              <div className="flex justify-between items-center mb-2.5">
                <label className="text-sm font-bold text-[#eef1f7]">Annual Family Income</label>
                <span className="text-[10px] tracking-[1px] font-extrabold text-[#ffbd83]">OPTIONAL</span>
              </div>
              <div className="relative min-h-[57px] flex items-center border border-white/15 rounded-[15px] bg-white/10 focus-within:border-[#ffb16c] focus-within:bg-white/15 focus-within:shadow-[0_0_0_4px_rgba(255,177,108,0.11)] transition-all">
                <span className="absolute left-4 text-xl text-[#ffb16c]">₹</span>
                <input
                  type="number"
                  value={form.income}
                  onChange={(e) => setForm({ ...form, income: e.target.value })}
                  placeholder="Example: 120000"
                  className="w-full h-[57px] pl-12 pr-4 border-0 outline-none bg-transparent text-white text-[15px] font-medium placeholder:text-[#8e98aa]"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={searching}
              className="w-full min-h-[62px] px-[18px] flex items-center justify-between border-0 rounded-[17px] bg-[#ffad63] text-[#2e1609] text-[15px] font-extrabold hover:-translate-y-0.5 hover:shadow-[0_13px_28px_rgba(255,173,99,0.25)] transition-all disabled:opacity-70 disabled:cursor-wait"
            >
              {searching ? (
                <>
                  <Loader size={20} className="animate-spin" />
                  <span>Finding Matches...</span>
                </>
              ) : (
                <>
                  <span className="flex items-center gap-2.5">
                    <Search size={20} />
                    <span>Find My Schemes</span>
                  </span>
                  <ArrowRight size={20} />
                </>
              )}
            </button>
          </form>

          <div className="flex gap-3 mt-7 pt-6 border-t border-white/10">
            <ShieldCheck size={19} className="flex-shrink-0 text-[#77d9ae]" />
            <div>
              <strong className="block text-[13px]">Privacy first</strong>
              <span className="block text-[11px] leading-relaxed text-[#99a3b4]">Your profile is only used to calculate scheme matches.</span>
            </div>
          </div>
        </aside>

        {/* RESULTS */}
        <main className="min-h-[650px] p-[40px_44px_48px] bg-[linear-gradient(#f8f8f6,#f8f8f6),radial-gradient(circle,#ddd_1px,transparent_1px)] dark:bg-[#121720] text-[#172033] dark:text-[#edf0f6]">
          <div className="flex gap-4 items-start mb-9">
            <span className="w-[44px] h-[44px] flex-shrink-0 flex items-center justify-center rounded-[14px] bg-[#172033] dark:bg-[#0a0f1a] text-white text-[13px] font-black">02</span>
            <div>
              <span className="block mb-1 text-[11px] tracking-[1.5px] font-extrabold opacity-60">YOUR RESULTS</span>
              <h2 className="text-[25px] tracking-[-0.7px]">Recommended schemes</h2>
            </div>
          </div>

          {loading ? (
            <div className="pt-7">
              <div className="flex gap-4 items-center mb-6">
                <div className="w-[36px] h-[36px] border-3 border-[rgba(13,124,102,0.14)] border-t-[#0d7c66] rounded-full animate-spin-slow"></div>
                <div>
                  <strong className="block text-[15px]">Finding suitable schemes...</strong>
                  <span className="text-[12px] text-[#7b8390] dark:text-[#94a3b8]">Checking your profile against available programs</span>
                </div>
              </div>
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-[180px] mb-4 rounded-[22px] bg-gradient-to-r from-[#eceef1] via-[#f7f7f7] to-[#eceef1] dark:from-[#1a1a2a] dark:via-[#2a2a3a] dark:to-[#1a1a2a] bg-[length:200%_100%] animate-skeleton"></div>
              ))}
            </div>
          ) : schemes.length === 0 ? (
            <div className="min-h-[460px] flex flex-col items-center justify-center text-center">
              <div className="relative w-[190px] h-[190px] flex items-center justify-center mb-6">
                <div className="absolute w-[80px] h-[80px] border border-[#d8dce3] dark:border-[#303643] rounded-full"></div>
                <div className="absolute w-[130px] h-[130px] border border-[#d8dce3] dark:border-[#303643] rounded-full"></div>
                <div className="absolute w-[180px] h-[180px] border border-[#d8dce3] dark:border-[#303643] rounded-full"></div>
                <div className="relative z-10 w-[66px] h-[66px] flex items-center justify-center rounded-full bg-[#ffad63] text-[#46210d] shadow-[0_10px_30px_rgba(255,173,99,0.28)]">
                  <ScanSearch size={29} />
                </div>
              </div>
              <h3 className="text-2xl tracking-[-0.5px] text-[#172033] dark:text-[#edf0f6]">Your matches will appear here</h3>
              <p className="max-w-[470px] text-[15px] leading-relaxed text-[#737b89] dark:text-[#94a3b8]">Complete your profile and we'll search available welfare schemes for suitable matches.</p>
              <div className="flex flex-wrap gap-2.5 justify-center mt-6">
                <span className="inline-flex items-center gap-1.5 px-3 py-2 border border-[#e0e2e7] dark:border-[#303643] rounded-full bg-white dark:bg-[#1d2430] text-[#555e6e] dark:text-[#bdc4d0] text-[11px] font-bold">
                  <BadgeCheck size={14} />
                  Eligibility
                </span>
                <span className="inline-flex items-center gap-1.5 px-3 py-2 border border-[#e0e2e7] dark:border-[#303643] rounded-full bg-white dark:bg-[#1d2430] text-[#555e6e] dark:text-[#bdc4d0] text-[11px] font-bold">
                  <Gift size={14} />
                  Benefits
                </span>
                <span className="inline-flex items-center gap-1.5 px-3 py-2 border border-[#e0e2e7] dark:border-[#303643] rounded-full bg-white dark:bg-[#1d2430] text-[#555e6e] dark:text-[#bdc4d0] text-[11px] font-bold">
                  <Files size={14} />
                  Documents
                </span>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex justify-between items-center mb-2 p-[19px_22px] rounded-[18px] bg-[#e7f7ee] dark:bg-[#1a3a2e]">
                <div>
                  <span className="block mb-1 text-[10px] font-black tracking-[1.2px] text-[#32815c] dark:text-[#6ef0ca]">MATCHING COMPLETE</span>
                  <h3 className="text-[18px] text-[#17452f] dark:text-[#edf7f4]">{schemes.length} scheme{schemes.length !== 1 ? 's' : ''} found for you</h3>
                </div>
                <span className="w-[42px] h-[42px] flex items-center justify-center rounded-full bg-[#2e8b61] text-white">
                  <Check size={20} />
                </span>
              </div>

              {schemes.map((scheme, index) => (
                <div key={index} className="relative grid grid-cols-[62px_1fr] overflow-hidden border border-[#e1e4e9] dark:border-[#303744] rounded-[23px] bg-white dark:bg-[#1b212c] hover:-translate-y-1 hover:shadow-[0_18px_45px_rgba(30,37,50,0.09)] hover:border-[#ffc18c] transition-all">
                  <div className="flex justify-center pt-[27px] bg-[#f1f2f4] dark:bg-[#242b37] text-[#9da3ae] dark:text-[#94a3b8] text-[12px] font-black tracking-[1px]">
                    {String(index + 1).padStart(2, '0')}
                  </div>
                  <div className="p-[25px_27px]">
                    <div className="flex justify-between gap-5">
                      <div>
                        <span className="inline-block mb-2 text-[10px] font-black tracking-[1.1px] uppercase text-[#b45320] dark:text-[#ffc18d]">{scheme.category || 'Welfare Scheme'}</span>
                        <h3 className="text-[21px] leading-[1.25] text-[#172033] dark:text-[#edf0f6]">{scheme.name}</h3>
                      </div>
                      <div className="text-center">
                        <span className="flex items-center justify-center w-[55px] h-[55] rounded-full bg-[#172033] dark:bg-[#0a0f1a] text-white text-sm">{scheme.match_score || '✓'}</span>
                        <span className="block mt-1 text-[9px] font-extrabold uppercase text-[#9198a4] dark:text-[#94a3b8]">Match</span>
                      </div>
                    </div>
                    <p className="my-4 text-sm leading-relaxed text-[#687181] dark:text-[#aab2bf]">{scheme.description}</p>
                    <div className="grid grid-cols-1 md:grid-cols-2 border-t border-b border-[#eceef1] dark:border-[#333a47]">
                      <div className="flex gap-3 p-[18px_10px_18px_0]">
                        <Gift size={19} className="flex-shrink-0 text-[#c35a22]" />
                        <div>
                          <span className="block text-[9px] font-extrabold tracking-[1px] text-[#9a9faa] dark:text-[#94a3b8]">WHAT YOU GET</span>
                          <strong className="text-[12px] leading-relaxed text-[#343d4c] dark:text-[#dce1e9]">{scheme.benefits}</strong>
                        </div>
                      </div>
                      <div className="flex gap-3 p-[18px_10px_18px_20px] border-l border-[#eceef1] dark:border-[#333a47]">
                        <Files size={19} className="flex-shrink-0 text-[#c35a22]" />
                        <div>
                          <span className="block text-[9px] font-extrabold tracking-[1px] text-[#9a9faa] dark:text-[#94a3b8]">DOCUMENTS NEEDED</span>
                          <strong className="text-[12px] leading-relaxed text-[#343d4c] dark:text-[#dce1e9]">{(scheme.documents || []).join(', ') || 'Check official portal'}</strong>
                        </div>
                      </div>
                    </div>
                    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mt-5">
                      <span className="flex items-center gap-2 text-[11px] font-semibold text-[#737b87] dark:text-[#94a3b8]">
                        <MapPin size={15} />
                        {scheme.apply_at || 'Official Portal / CSC'}
                      </span>
                      <a
                        href={scheme.website || '#'}
                        target="_blank"
                        rel="noopener"
                        className="inline-flex items-center gap-2 px-4 py-3 rounded-[11px] bg-[#ffad63] dark:bg-[#4a3a1a] text-[#321708] dark:text-white text-[11px] font-extrabold hover:bg-[#172033] dark:hover:bg-[#0a0f1a] hover:text-white transition-all"
                      >
                        Visit Official Portal
                        <ArrowUpRight size={15} />
                      </a>
                    </div>
                  </div>
                </div>
              ))}

              <div className="flex gap-3 mt-1 p-[17px_19px] border border-[#f1d49e] dark:border-[#4a3a1a] rounded-[16px] bg-[#fff7e7] dark:bg-[#1a1a0a] text-[#74501e] dark:text-[#fbbf24]">
                <ShieldCheck size={19} className="flex-shrink-0" />
                <div>
                  <strong className="block text-[12px]">Important</strong>
                  <span className="text-[11px] leading-relaxed">JanMitra AI provides AI-generated guidance for educational purposes only. Verify important information with official sources.</span>
                </div>
              </div>
            </div>
          )}
        </main>
      </section>
    </div>
  )
}