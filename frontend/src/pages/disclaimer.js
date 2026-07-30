import { ShieldCheck, Landmark, Check, X, ArrowRight, Trash2, BarChart3, Database, Settings2, Cloud, Sparkles, GraduationCap, Wheat, HeartPulse, ArrowUpRight } from 'lucide-react'

export default function Disclaimer() {
  const officialLinks = [
    { name: 'UP Food & Supply', url: 'https://fcs.up.gov.in', type: 'PDS' },
    { name: 'PM Kisan Portal', url: 'https://pmkisan.gov.in', type: 'AGRICULTURE' },
    { name: 'UP Pension Portal', url: 'https://sspy-up.gov.in', type: 'PENSION' },
    { name: 'Ayushman Bharat', url: 'https://pmjay.gov.in', type: 'HEALTH' },
    { name: 'UP Scholarship', url: 'https://scholarship.up.gov.in', type: 'EDUCATION' },
    { name: 'UP Jan Sunwai', url: 'https://jansunwai.up.nic.in', type: 'GRIEVANCE' },
  ]

  return (
    <div className="rai-page max-w-[1440px] mx-auto px-4 sm:px-8 py-7 sm:py-[70px] animate-fade-in">
      {/* HERO */}
      <section className="relative min-h-[440px] grid grid-cols-[60px_1fr_210px] items-center p-8 sm:p-14 overflow-hidden bg-gradient-to-br from-[#f7f1df] via-[#fffdf7] to-[#f3ead2] dark:from-[#171a1d] dark:via-[#171a1d] dark:to-[#171a1d] border border-[rgba(17,24,39,0.12)] dark:border-[#30353b] rounded-[8px]">
        <div className="h-full flex flex-col items-center justify-center">
          <span className="font-mono text-sm font-bold">01</span>
          <div className="w-px h-[120px] my-[18px] bg-[rgba(17,24,39,0.3)] dark:bg-[#30353b]"></div>
          <span className="writing-mode-vertical font-mono text-[11px] font-bold tracking-[0.18em]">TRUST CHARTER</span>
        </div>
        <div className="max-w-[850px]">
          <div className="inline-flex items-center gap-2.5 mb-6 font-mono text-[12px] font-bold tracking-[0.08em] uppercase text-[#138a63]">
            <ShieldCheck size={18} />
            Responsible Artificial Intelligence
          </div>
          <h1 className="text-[clamp(3.4rem,6vw,6.8rem)] leading-[0.94] tracking-[-0.065em] font-extrabold text-[#111827] dark:text-[#f8fafc]">
            Guidance with AI.<br />
            <span className="text-[#138a63]">Decisions with you.</span>
          </h1>
          <p className="max-w-[720px] mt-7 text-[18px] leading-relaxed text-[#505761] dark:text-[#aab4c1]">Understand what JanMitra AI does, where its limits are, and how your information is handled before using AI-powered welfare guidance.</p>
        </div>
        <div className="flex flex-col items-center font-mono hidden lg:flex">
          <div className="w-[105px] h-[105px] grid place-items-center mb-4 border-2 border-[#111827] dark:border-[#f8fafc] rounded-full">
            <ShieldCheck size={43} />
          </div>
          <strong className="text-sm tracking-[0.15em]">JANMITRA AI</strong>
          <span className="mt-1 text-[8px] tracking-[0.12em] text-[#7c838d] dark:text-[#94a3b8]">TRANSPARENCY FIRST</span>
        </div>
        <div className="absolute w-[380px] h-[380px] -right-[150px] -bottom-[190px] border border-[rgba(17,24,39,0.12)] dark:border-[#30353b] rounded-full"></div>
      </section>

      {/* NOTICE */}
      <section className="grid grid-cols-[190px_1fr_150px] mt-7 text-white bg-[#101a24] rounded-[6px] overflow-hidden">
        <div className="p-[35px] flex flex-col justify-center bg-[#f4c95d] text-[#111827]">
          <span className="font-mono text-[12px] font-bold tracking-[0.15em]">IMPORTANT</span>
          <strong className="mt-2 text-[22px] leading-[1.05]">READ BEFORE USE</strong>
        </div>
        <div className="p-[40px_50px]">
          <span className="font-mono text-[11px] tracking-[0.15em] text-[#9ca3af]">NOTICE / 001</span>
          <h2 className="mt-3 mb-4 text-[clamp(1.8rem,3vw,3rem)] tracking-[-0.04em]">JanMitra AI is not a Government service.</h2>
          <p className="max-w-[850px] mt-2 text-[15px] leading-relaxed text-[#cbd5e1]">JanMitra AI provides AI-generated guidance for educational and assistance purposes only. It is not an official Government of India service and does not provide legal or administrative approval.</p>
          <p className="max-w-[850px] mt-2 text-[15px] leading-relaxed text-[#cbd5e1]">Users should independently verify important information, eligibility conditions, documents, deadlines and procedures with the respective government department before taking action.</p>
        </div>
        <div className="flex flex-col items-center justify-center border-l border-white/15 text-center">
          <Landmark size={34} className="mb-3" />
          <span className="text-[#9ca3af] font-mono text-[9px] tracking-[0.1em]">Independent<br />AI Project</span>
        </div>
      </section>

      {/* CAN / CANNOT */}
      <section className="py-[100px]">
        <div className="grid grid-cols-[90px_1fr] max-w-[800px] mb-11">
          <span className="font-mono text-[13px] font-bold text-[#138a63]">02</span>
          <div>
            <span className="font-mono text-[11px] font-bold tracking-[0.16em] text-[#7c838d] dark:text-[#94a3b8]">OPERATIONAL BOUNDARIES</span>
            <h2 className="mt-2 mb-2.5 text-[clamp(2rem,4vw,4rem)] leading-none tracking-[-0.05em] text-[#111827] dark:text-[#f8fafc]">Know where the AI stops.</h2>
            <p className="max-w-[580px] text-[16px] leading-relaxed text-[#68707c] dark:text-[#aab4c1]">JanMitra AI assists with understanding processes. It does not replace government authorities.</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 border-t border-b border-[#d7d9dd] dark:border-[#343b43]">
          {/* CAN */}
          <div className="border-r border-[#d7d9dd] dark:border-[#343b43]">
            <div className="flex items-center gap-5 p-7 border-b border-[#d7d9dd] dark:border-[#343b43]">
              <span className="w-[50px] h-[50px] grid place-items-center rounded-full text-[#138a63] bg-[#dcf7ed]">
                <Check size={24} />
              </span>
              <div>
                <small className="font-mono text-[10px] tracking-[0.15em] text-[#7c838d] dark:text-[#94a3b8]">JANMITRA AI CAN</small>
                <h3 className="mt-1 text-2xl text-[#111827] dark:text-[#f8fafc]">Assist & Explain</h3>
              </div>
            </div>
            {[
              'Explain government scheme eligibility and benefits.',
              'List document requirements for welfare services.',
              'Provide grievance guidance and procedural steps.',
              'Generate standardized complaint letter templates.',
              'Identify relevant schemes based on major life events.'
            ].map((item, i) => (
              <div key={i} className="grid grid-cols-[55px_1fr] gap-4 min-h-[83px] items-center p-[17px_30px] border-b border-[#e6e7e9] dark:border-[#343b43] hover:pl-[38px] hover:bg-[rgba(15,23,42,0.025)] dark:hover:bg-[rgba(255,255,255,0.03)] transition-all">
                <span className="font-mono text-[11px] text-[#a0a5ad] dark:text-[#94a3b8]">{String(i + 1).padStart(2, '0')}</span>
                <p className="text-[15px] leading-relaxed text-[#39414c] dark:text-[#aab4c1]">{item}</p>
              </div>
            ))}
          </div>
          {/* CANNOT */}
          <div>
            <div className="flex items-center gap-5 p-7 border-b border-[#d7d9dd] dark:border-[#343b43]">
              <span className="w-[50px] h-[50px] grid place-items-center rounded-full text-[#e5484d] bg-[#fee7e7]">
                <X size={24} />
              </span>
              <div>
                <small className="font-mono text-[10px] tracking-[0.15em] text-[#7c838d] dark:text-[#94a3b8]">JANMITRA AI CANNOT</small>
                <h3 className="mt-1 text-2xl text-[#111827] dark:text-[#f8fafc]">Approve & Decide</h3>
              </div>
            </div>
            {[
              'Process or submit actual government applications.',
              'Guarantee scheme eligibility, funding or approval.',
              'Access, modify or verify official government records.',
              'Provide legally binding advice or representation.',
              'Make administrative decisions on your behalf.'
            ].map((item, i) => (
              <div key={i} className="grid grid-cols-[55px_1fr] gap-4 min-h-[83px] items-center p-[17px_30px] border-b border-[#e6e7e9] dark:border-[#343b43] hover:pl-[38px] hover:bg-[rgba(15,23,42,0.025)] dark:hover:bg-[rgba(255,255,255,0.03)] transition-all">
                <span className="font-mono text-[11px] text-[#a0a5ad] dark:text-[#94a3b8]">{String(i + 1).padStart(2, '0')}</span>
                <p className="text-[15px] leading-relaxed text-[#39414c] dark:text-[#aab4c1]">{item}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* PRIVACY */}
      <section className="mt-24 p-8 sm:p-[80px_65px] text-white bg-[radial-gradient(circle_at_85%_10%,rgba(19,138,99,0.28),transparent_30%),#101a24] rounded-[6px]">
        <div className="grid grid-cols-[90px_1fr] max-w-[800px] mb-11">
          <span className="font-mono text-[13px] font-bold text-[#6ee7b7]">03</span>
          <div>
            <span className="font-mono text-[11px] font-bold tracking-[0.16em] text-[#94a3b8]">DATA PROTOCOL</span>
            <h2 className="mt-2 mb-2.5 text-[clamp(2rem,4vw,4rem)] leading-none tracking-[-0.05em] text-white">What happens to your data?</h2>
            <p className="max-w-[580px] text-[16px] leading-relaxed text-[#aeb9c7]">A simple view of how information moves through JanMitra AI.</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-[1fr_70px_1fr_70px_1fr] gap-4 items-center mt-12">
          <div className="min-h-[270px] p-7 border border-white/15">
            <div className="w-[52px] h-[52px] grid place-items-center mb-7 text-[#6ee7b7] bg-[rgba(110,231,183,0.08)]">
              <Sparkles size={24} className="text-[#6ee7b7]" />
            </div>
            <span className="font-mono text-[10px] tracking-[0.13em] text-[#6ee7b7]">STEP 01</span>
            <h3 className="mt-2 mb-3 text-[22px]">You interact</h3>
            <p className="text-[14px] leading-relaxed text-[#aeb9c7]">Chat questions or documents are provided to the system when you use its features.</p>
          </div>
          <div className="grid place-items-center text-[#64748b] rotate-90 md:rotate-0">
            <ArrowRight size={24} />
          </div>
          <div className="min-h-[270px] p-7 border border-white/15">
            <div className="w-[52px] h-[52px] grid place-items-center mb-7 text-[#6ee7b7] bg-[rgba(110,231,183,0.08)]">
              <Database size={24} className="text-[#6ee7b7]" />
            </div>
            <span className="font-mono text-[10px] tracking-[0.13em] text-[#6ee7b7]">STEP 02</span>
            <h3 className="mt-2 mb-3 text-[22px]">System processes</h3>
            <p className="text-[14px] leading-relaxed text-[#aeb9c7]">Information is processed to generate guidance, OCR results or relevant responses.</p>
          </div>
          <div className="grid place-items-center text-[#64748b] rotate-90 md:rotate-0">
            <ArrowRight size={24} />
          </div>
          <div className="min-h-[270px] p-7 border border-white/15">
            <div className="w-[52px] h-[52px] grid place-items-center mb-7 text-[#6ee7b7] bg-[rgba(110,231,183,0.08)]">
              <Trash2 size={24} className="text-[#6ee7b7]" />
            </div>
            <span className="font-mono text-[10px] tracking-[0.13em] text-[#6ee7b7]">STEP 03</span>
            <h3 className="mt-2 mb-3 text-[22px]">Sensitive files leave</h3>
            <p className="text-[14px] leading-relaxed text-[#aeb9c7]">Uploaded documents are processed and immediately deleted. Chat conversations are not permanently stored.</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 mt-12 border-t border-white/15">
          <div className="p-[30px_25px] border-r border-white/15">
            <Sparkles size={24} className="text-[#6ee7b7]" />
            <strong className="block mt-4 mb-2 text-[15px]">No identity vault</strong>
            <span className="text-[12px] leading-relaxed text-[#9da9b8]">No Aadhaar, bank or identity data is stored.</span>
          </div>
          <div className="p-[30px_25px] border-r border-white/15">
            <BarChart3 size={24} className="text-[#6ee7b7]" />
            <strong className="block mt-4 mb-2 text-[15px]">Anonymous telemetry</strong>
            <span className="text-[12px] leading-relaxed text-[#9da9b8]">Only anonymised ratings and comments are retained.</span>
          </div>
          <div className="p-[30px_25px] border-r border-white/15">
            <Database size={24} className="text-[#6ee7b7]" />
            <strong className="block mt-4 mb-2 text-[15px]">Local knowledge</strong>
            <span className="text-[12px] leading-relaxed text-[#9da9b8]">Scheme and FAQ information uses local data files.</span>
          </div>
          <div className="p-[30px_25px]">
            <Settings2 size={24} className="text-[#6ee7b7]" />
            <strong className="block mt-4 mb-2 text-[15px]">Browser preferences</strong>
            <span className="text-[12px] leading-relaxed text-[#9da9b8]">localStorage stores language and theme preferences.</span>
          </div>
        </div>

        <div className="flex gap-4 items-center mt-5 p-[18px_22px] text-[#d9e1ea] bg-white/5">
          <Cloud size={20} />
          <p className="text-[13px] leading-relaxed"><strong>External processing:</strong> JanMitra AI uses Groq API for LLM inference, subject to Groq's privacy policy.</p>
        </div>
      </section>

      {/* SYSTEM */}
      <section className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-[70px] py-[100px]">
        <div>
          <span className="font-mono text-[11px] font-bold tracking-[0.13em] text-[#138a63]">04 / SYSTEM</span>
          <h2 className="mt-3 mb-3 text-[38px] leading-[1.05] tracking-[-0.045em] text-[#111827] dark:text-[#f8fafc]">What's behind JanMitra AI?</h2>
          <p className="text-[#68707c] dark:text-[#aab4c1] leading-relaxed">JanMitra AI is an AI-powered welfare assistance tool built for the HCLTech hackathon.</p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 border-t border-[#d7d9dd] dark:border-[#343b43]">
          {[
            { num: '01', title: 'TF-IDF Retrieval', label: 'RAG', desc: 'Finds relevant information from a curated knowledge base of UP welfare schemes and PDS FAQs.' },
            { num: '02', title: 'Groq LLM', label: 'AI INFERENCE', desc: 'Generates human-readable responses grounded in retrieved context.' },
            { num: '03', title: 'pytesseract', label: 'OCR', desc: 'Extracts text from uploaded document images.' },
            { num: '04', title: 'ReportLab', label: 'DOCUMENT ENGINE', desc: 'Generates downloadable PDF reports and checklists.' },
          ].map((item, i) => (
            <div key={i} className="p-[28px_22px_35px] border-r border-[#d7d9dd] dark:border-[#343b43]">
              <span className="block mb-11 font-mono text-[11px] text-[#a0a5ad] dark:text-[#94a3b8]">{item.num}</span>
              <strong className="block text-[19px] text-[#111827] dark:text-[#f8fafc]">{item.title}</strong>
              <span className="inline-block mt-2 mb-5 px-2 py-1 font-mono text-[9px] font-bold text-[#138a63] bg-[#e5f6ef] dark:bg-[#1a3a2e]">{item.label}</span>
              <p className="text-[13px] leading-relaxed text-[#68707c] dark:text-[#aab4c1]">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* DIRECTORY */}
      <section className="mt-12 p-[75px_65px] bg-[#f6f3eb] dark:bg-[#171a1d] rounded-[6px]">
        <div className="flex flex-col sm:flex-row items-end justify-between gap-12 mb-12">
          <div>
            <span className="font-mono text-[11px] font-bold tracking-[0.13em] text-[#138a63]">05 / VERIFY</span>
            <h2 className="mt-2.5 text-[clamp(2.3rem,4vw,4.2rem)] leading-none tracking-[-0.055em] text-[#111827] dark:text-[#f8fafc]">Continue on official sources.</h2>
          </div>
          <p className="max-w-[390px] text-[#68707c] dark:text-[#aab4c1] leading-relaxed">Always verify important information directly with the appropriate government portal.</p>
        </div>
        <div className="border-t border-[#bbbdbf] dark:border-[#34383d]">
          {officialLinks.map((link, i) => (
            <a key={i} href={link.url} target="_blank" rel="noopener" className="grid grid-cols-[70px_minmax(0,1fr)_160px_40px] gap-5 items-center min-h-[92px] text-[#111827] dark:text-[#f8fafc] border-b border-[#d1d1cf] dark:border-[#34383d] hover:px-[18px] hover:bg-white dark:hover:bg-[#202429] transition-all">
              <span className="font-mono text-[11px] text-[#8b8f95] dark:text-[#94a3b8]">{String(i + 1).padStart(2, '0')}</span>
              <div>
                <strong className="block text-[18px]">{link.name}</strong>
                <small className="block mt-1 font-mono text-[#7b8087] dark:text-[#94a3b8]">{link.url.replace('https://', '')}</small>
              </div>
              <span className="font-mono text-[10px] font-bold tracking-[0.12em] text-[#747980] dark:text-[#94a3b8]">{link.type}</span>
              <ArrowUpRight size={20} className="transition-transform group-hover:translate-x-1 group-hover:-translate-y-1" />
            </a>
          ))}
        </div>
      </section>

      {/* FINAL STATEMENT */}
      <div className="grid grid-cols-[70px_1fr] gap-6 items-center mt-7 p-[45px_50px] text-white bg-[#138a63] rounded-[6px]">
        <ShieldCheck size={45} />
        <div>
          <span className="block mb-2 font-mono text-[10px] font-bold tracking-[0.14em] opacity-80">JANMITRA AI RESPONSIBLE AI PRINCIPLE</span>
          <strong className="block max-w-[900px] text-[clamp(1.3rem,2.4vw,2.2rem)] leading-[1.25]">AI should make government information easier to understand — not pretend to be the government.</strong>
        </div>
      </div>

      <style jsx>{`
        .writing-mode-vertical {
          writing-mode: vertical-rl;
          transform: rotate(180deg);
        }
      `}</style>
    </div>
  )
}