import { useState } from 'react'
import { MessageCircleHeart, Star, Layers3, ChevronDown, Lightbulb, LockKeyhole, ArrowUpRight, Check, Sparkles, BrainCircuit, Users, ShieldCheck, Info, Loader } from 'lucide-react'

export default function Feedback() {
  const [rating, setRating] = useState(null)
  const [hoverRating, setHoverRating] = useState(null)
  const [comment, setComment] = useState('')
  const [page, setPage] = useState('general')
  const [submitted, setSubmitted] = useState(false)
  const [loading, setLoading] = useState(false)

  const ratingLabels = {
    1: 'Poor',
    2: 'Fair',
    3: 'Good',
    4: 'Very Good',
    5: 'Excellent'
  }

  const handleSubmit = async () => {
    if (!rating && !comment.trim()) {
      alert('Please provide a rating or comment.')
      return
    }

    setLoading(true)
    try {
      const res = await fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rating, comment, page })
      })
      if (res.ok) {
        setSubmitted(true)
        setRating(null)
        setComment('')
        setPage('general')
      }
    } catch (e) {
      alert('Failed to submit. Please try again.')
    }
    setLoading(false)
  }

  return (
    <div className="fbx-page max-w-[1440px] mx-auto px-4 sm:px-8 py-6 sm:py-[70px] animate-fade-in">
      {/* INTRO */}
      <section className="min-h-[480px] grid grid-cols-[150px_minmax(0,1fr)_180px] border-t-2 border-b border-[#101114] dark:border-[#34363c]">
        <div className="flex flex-col justify-between p-[35px_0] border-r border-[#d9d9dc] dark:border-[#34363c]">
          <span className="font-mono text-[11px] font-bold tracking-[0.17em] text-[#70727a] dark:text-[#94a3b8]">FEEDBACK</span>
          <strong className="text-[72px] leading-none tracking-[-0.07em] text-[#101114] dark:text-[#f8fafc]">05</strong>
        </div>
        <div className="p-[55px_7%]">
          <div className="flex items-center gap-2.5 mb-6 font-mono text-[11px] font-bold tracking-[0.13em] uppercase text-[#7557ff]">
            <MessageCircleHeart size={18} />
            Citizen Voice
          </div>
          <h1 className="text-[clamp(4rem,7vw,7.5rem)] leading-[0.88] tracking-[-0.075em] font-extrabold text-[#17181c] dark:text-[#f8fafc]">
            Tell us what<br />
            <em className="not-italic text-[#7557ff] font-serif">actually</em> worked.
          </h1>
          <p className="max-w-[630px] mt-9 text-[18px] leading-relaxed text-[#70727a] dark:text-[#94a3b8]">One rating can help make JanMitra AI clearer, faster and more useful for the next citizen.</p>
        </div>
        <div className="flex flex-col items-center justify-around border-l border-[#d9d9dc] dark:border-[#34363c] overflow-hidden">
          {['RATE', 'REVIEW', 'IMPROVE'].map((text, i) => (
            <span key={i} className="writing-mode-vertical font-mono text-[10px] font-bold tracking-[0.28em] text-[#b1b2b6] dark:text-[#94a3b8]">{text}</span>
          ))}
        </div>
      </section>

      {/* RATING */}
      <section className="min-h-[390px] grid grid-cols-1 md:grid-cols-[300px_1fr] mt-[70px] text-white bg-[#101114] dark:bg-[#1a1a1e]">
        <div className="p-8 md:p-12 border-r border-white/15">
          <span className="font-mono text-[10px] font-bold tracking-[0.14em] text-[#c8ff4d]">01 / YOUR EXPERIENCE</span>
          <h2 className="mt-5 text-[43px] leading-[0.98] tracking-[-0.05em]">How did JanMitra AI do?</h2>
        </div>
        <div className="flex flex-col justify-center p-[45px_7%]">
          <div className="grid grid-cols-5 border-t border-b border-white/15">
            {[1, 2, 3, 4, 5].map((val) => (
              <button
                key={val}
                onClick={() => setRating(val)}
                onMouseEnter={() => setHoverRating(val)}
                onMouseLeave={() => setHoverRating(null)}
                className={`relative h-[145px] flex items-center justify-center border-r border-white/15 bg-transparent text-[#6d7077] hover:text-[#c8ff4d] hover:bg-[rgba(200,255,77,0.055)] transition-all ${
                  (hoverRating !== null && val <= hoverRating) || (rating !== null && val <= rating)
                    ? 'text-[#c8ff4d] bg-[rgba(200,255,77,0.09)]'
                    : ''
                }`}
              >
                <span className="absolute top-3 left-3.5 font-mono text-[10px] text-[#676a70]">{val}</span>
                <Star size={50} strokeWidth={1.4} fill={(hoverRating !== null && val <= hoverRating) || (rating !== null && val <= rating) ? 'currentColor' : 'none'} />
              </button>
            ))}
          </div>
          <div className="flex justify-between items-center mt-6">
            <span className="font-mono text-[10px] tracking-[0.15em] text-[#777b82]">YOUR RATING</span>
            <strong className="text-[22px] text-[#c8ff4d]">{rating ? ratingLabels[rating] : 'Select 1 — 5'}</strong>
          </div>
        </div>
      </section>

      {/* FEATURE */}
      <section className="grid grid-cols-[130px_1fr] py-[110px] border-b border-[#d9d9dc] dark:border-[#34363c]">
        <span className="text-[75px] font-extrabold leading-none tracking-[-0.08em] text-[#7557ff]">02</span>
        <div className="grid grid-cols-1 lg:grid-cols-[minmax(260px,0.8fr)_minmax(350px,1.2fr)] gap-[70px] items-end">
          <div>
            <span className="font-mono text-[10px] font-bold tracking-[0.14em] text-[#8c8e94] dark:text-[#94a3b8]">WHAT ARE YOU REVIEWING?</span>
            <h2 className="mt-3 text-[clamp(2.2rem,4vw,4.4rem)] leading-[0.98] tracking-[-0.055em] text-[#17181c] dark:text-[#f8fafc]">Choose the part you used.</h2>
          </div>
          <div className="relative min-h-[100px] grid grid-cols-[70px_1fr_40px] items-center px-6 bg-[#f5f2e9] dark:bg-[#202126] border-b-3 border-[#101114] dark:border-[#34363c]">
            <span className="w-[47px] h-[47px] grid place-items-center text-white bg-[#7557ff]">
              <Layers3 size={20} />
            </span>
            <div>
              <label className="block mb-1 font-mono text-[9px] font-bold tracking-[0.1em] uppercase text-[#7a7d84] dark:text-[#94a3b8]">JanMitra AI Feature</label>
              <select 
                value={page}
                onChange={(e) => setPage(e.target.value)}
                className="w-full appearance-none p-0 border-0 outline-none bg-transparent text-[18px] font-bold text-[#17181c] dark:text-[#f8fafc] cursor-pointer"
              >
                <option value="general">Overall App Experience</option>
                <option value="chat">AI Chatbot</option>
                <option value="checklist">Document Checklist</option>
                <option value="schemes">Scheme Finder</option>
                <option value="grievance">Grievance Guide</option>
              </select>
            </div>
            <ChevronDown size={20} className="pointer-events-none" />
          </div>
        </div>
      </section>

      {/* COMMENT */}
      <section className="grid grid-cols-1 lg:grid-cols-[0.75fr_1.25fr] gap-[80px] py-[110px]">
        <div>
          <span className="font-mono text-[10px] font-bold tracking-[0.15em] text-[#7557ff]">03 / SPEAK FREELY</span>
          <h2 className="mt-4 mb-5 text-[clamp(2.8rem,5vw,5.7rem)] leading-[0.9] tracking-[-0.065em] text-[#17181c] dark:text-[#f8fafc]">What should<br />we change?</h2>
          <p className="max-w-[430px] text-[16px] leading-relaxed text-[#70727a] dark:text-[#94a3b8]">Short or detailed — tell us what felt useful, confusing, slow or missing.</p>
          <div className="max-w-[390px] flex gap-4 mt-11 pt-5 border-t border-[#d9d9dc] dark:border-[#34363c] text-[13px] leading-relaxed text-[#72747a] dark:text-[#94a3b8]">
            <Lightbulb size={19} className="flex-shrink-0 text-[#7557ff]" />
            <span>Specific feedback helps us understand the problem faster.</span>
          </div>
        </div>
        <div className="min-h-[430px] p-[28px_34px] bg-[repeating-linear-gradient(transparent,transparent_44px,rgba(23,24,28,0.07)_45px),#f7f3e8] dark:bg-[repeating-linear-gradient(transparent,transparent_44px,rgba(255,255,255,0.055)_45px),#e9e2d3] shadow-[14px_14px_0_#ded9cd] dark:shadow-[14px_14px_0_#292b30]">
          <div className="flex justify-between pb-5 border-b border-[rgba(23,24,28,0.18)] font-mono text-[9px] font-bold tracking-[0.13em] text-[#77746d]">
            <span>JANMITRA AI / CITIZEN NOTE</span>
            <span>OPTIONAL</span>
          </div>
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            rows="7"
            placeholder="Write your experience here..."
            className="w-full min-h-[260px] p-[25px_4px] resize-vertical border-0 outline-none bg-transparent text-[#252525] font-serif text-[22px] leading-[2.05] placeholder:text-[#a8a398]"
          />
          <div className="flex flex-col sm:flex-row items-center justify-between gap-6 mt-3.5 pt-5 border-t border-[rgba(23,24,28,0.18)]">
            <span className="flex items-center gap-2 text-[11px] text-[#77746d]">
              <LockKeyhole size={15} />
              Feedback is used to improve JanMitra AI
            </span>
            <button
              onClick={handleSubmit}
              disabled={loading}
              className="min-w-[190px] px-5 py-4 flex items-center justify-between gap-5 text-white bg-[#101114] dark:bg-[#1a1a1e] border-0 text-[13px] font-bold hover:bg-[#7557ff] hover:-translate-y-1 transition-all disabled:opacity-60 disabled:cursor-wait"
            >
              {loading ? (
                <>
                  <Loader size={18} className="animate-spin" />
                  <span>Sending...</span>
                </>
              ) : (
                <>
                  <span>Send Feedback</span>
                  <ArrowUpRight size={18} />
                </>
              )}
            </button>
          </div>
        </div>
      </section>

      {/* SUCCESS */}
      {submitted && (
        <div className="relative grid grid-cols-[65px_1fr_50px] items-center gap-6 mb-[90px] p-[27px_35px] text-[#102111] bg-[#c8ff4d] overflow-hidden animate-fade-in">
          <div className="w-[54px] h-[54px] grid place-items-center text-white bg-[#101114] dark:bg-[#1a1a1e] rounded-full">
            <Check size={24} />
          </div>
          <div>
            <span className="block mb-1 font-mono text-[9px] font-bold tracking-[0.14em]">FEEDBACK RECEIVED</span>
            <strong className="block text-[20px]">Thank you for helping us improve.</strong>
          </div>
          <Sparkles size={30} />
        </div>
      )}

      {/* IMPACT */}
      <section className="grid grid-cols-1 lg:grid-cols-[0.7fr_1.3fr] gap-[80px] pt-10">
        <div>
          <span className="font-mono text-[10px] font-bold tracking-[0.15em] text-[#7557ff]">04 / WHAT HAPPENS NEXT</span>
          <h2 className="mt-4 text-[clamp(2.6rem,4vw,4.8rem)] leading-[0.95] tracking-[-0.06em] text-[#17181c] dark:text-[#f8fafc]">Your feedback<br />doesn't stop here.</h2>
        </div>
        <div className="border-t-2 border-[#101114] dark:border-[#34363c]">
          {[
            { index: 'A', icon: BrainCircuit, title: 'Improve AI Accuracy', desc: 'Ratings help identify where AI answers can become clearer and more accurate.', tag: 'ACCURACY' },
            { index: 'B', icon: Users, title: 'Serve More Citizens', desc: 'Better experiences make welfare information easier to access across Uttar Pradesh.', tag: 'ACCESS' },
            { index: 'C', icon: ShieldCheck, title: 'Build Responsible AI', desc: 'Negative feedback helps surface potential issues that require attention.', tag: 'TRUST' },
          ].map((item, i) => (
            <div key={i} className="grid grid-cols-[45px_55px_minmax(0,1fr)_100px] gap-5 items-center min-h-[145px] border-b border-[#d9d9dc] dark:border-[#34363c] hover:pl-4 hover:bg-[rgba(117,87,255,0.04)] transition-all">
              <span className="font-mono text-[11px] text-[#a2a3a8] dark:text-[#94a3b8]">{item.index}</span>
              <span className="w-[48px] h-[48px] grid place-items-center text-[#7557ff] bg-[#eeeaff] dark:bg-[#2a1a4a]">
                <item.icon size={20} />
              </span>
              <div>
                <strong className="text-[17px] text-[#17181c] dark:text-[#f8fafc]">{item.title}</strong>
                <p className="max-w-[500px] mt-1.5 text-[13px] leading-relaxed text-[#70727a] dark:text-[#94a3b8]">{item.desc}</p>
              </div>
              <span className="font-mono text-[9px] font-bold tracking-[0.13em] text-[#b2b3b7] dark:text-[#94a3b8] text-right">{item.tag}</span>
            </div>
          ))}
        </div>
      </section>

      {/* DISCLAIMER */}
      <div className="grid grid-cols-[170px_1fr] items-center mt-[100px] text-[#111] bg-[#ffd84d] dark:bg-[#4a3a10] dark:text-[#f8fafc]">
        <span className="flex items-center gap-2.5 p-[20px_25px] text-white bg-[#101114] dark:bg-[#1a1a1e] font-mono text-[10px] font-bold tracking-[0.12em]">
          <Info size={17} />
          IMPORTANT
        </span>
        <p className="p-[20px_30px] text-[13px] font-semibold leading-relaxed">JanMitra AI provides AI-generated guidance for educational purposes only. It is not an official Government of India service.</p>
      </div>

      <style jsx>{`
        .writing-mode-vertical {
          writing-mode: vertical-rl;
          letter-spacing: 0.28em;
        }
        .border-b-3 {
          border-bottom-width: 3px;
        }
      `}</style>
    </div>
  )
}