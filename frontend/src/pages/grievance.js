import { useState, useEffect } from 'react'
import { Landmark, ShoppingBasket, IndianRupee, ShieldAlert, CirclePause, Phone, ShieldCheck, ArrowUpRight, User, MessageSquareWarning, FileCheck2, LockKeyhole, ListFilter, Route, CircleAlert, PhoneCall, MoveRight, BadgeCheck, X, ChevronDown, Copy, Printer, Loader, Paperclip, FileUp } from 'lucide-react'
import { useLanguage } from '@/contexts/LanguageContext'
import { api } from '@/utils/api'

export default function Grievance() {
  const { t } = useLanguage()
  const [activeCategory, setActiveCategory] = useState('ration_denial')
  const [steps, setSteps] = useState(null)
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    district: '',
    block: '',
    village: '',
    issue_type: '',
    description: '',
    date_of_incident: '',
    previous_complaint_no: ''
  })
  const [complaint, setComplaint] = useState(null)
  const [nextSteps, setNextSteps] = useState([])
  const [showComplaint, setShowComplaint] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [attachments, setAttachments] = useState([])
  const [error, setError] = useState('')

  const categories = [
    { id: 'ration_denial', icon: ShoppingBasket, label: t('ration_denied'), desc: t('ration_denied_desc') },
    { id: 'scheme_not_received', icon: IndianRupee, label: t('scheme_failed'), desc: t('scheme_failed_desc') },
    { id: 'corruption', icon: ShieldAlert, label: t('corruption'), desc: t('corruption_desc') },
    { id: 'pension_stopped', icon: CirclePause, label: t('pension_stopped'), desc: t('pension_stopped_desc') },
  ]

  useEffect(() => {
    loadSteps(activeCategory)
  }, [activeCategory])

  const loadSteps = async (catId) => {
    setLoading(true)
    setError('')
    try {
      const categoryMap = {
        ration_denial: 'ration',
        scheme_not_received: 'scheme',
        corruption: 'other',
        pension_stopped: 'pension'
      }
      const data = await api.grievanceGuide({
        category: categoryMap[catId] || 'other',
        description: categories.find(category => category.id === catId)?.desc || catId,
        state: 'Uttar Pradesh'
      })
      setSteps({
        name: data.department,
        steps: data.steps.map((description, index) => ({
          step: index + 1,
          title: description,
          description,
          open: index === 0
        })),
        contacts: []
      })
    } catch (e) {
      setSteps(null)
      setError(e.message || 'The grievance guide is temporarily unavailable.')
    }
    setLoading(false)
  }

  const toggleStep = (index) => {
    setSteps(prev => ({
      ...prev,
      steps: prev.steps.map((step, i) => ({
        ...step,
        open: i === index ? !step.open : step.open
      }))
    }))
  }

  const handleFormChange = (e) => {
    setFormData({ ...formData, [e.target.id]: e.target.value })
  }

  const handleAttachments = event => {
    const selected = Array.from(event.target.files || [])
    const acceptedTypes = new Set(['application/pdf', 'image/jpeg', 'image/png', 'text/plain'])
    const invalid = selected.find(file => !acceptedTypes.has(file.type) || file.size > 5 * 1024 * 1024)
    if (invalid) {
      setError('Supporting files must be PDF, JPG, PNG, or TXT and no larger than 5 MB each.')
      event.target.value = ''
      return
    }
    setError('')
    setAttachments(selected.slice(0, 5))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!formData.name || !formData.district || !formData.issue_type || !formData.description) {
      alert('Please fill in all required fields.')
      return
    }

    setIsGenerating(true)
    setError('')
    try {
      const categoryMap = {
        ration_denial: 'ration',
        scheme_not_received: 'scheme',
        corruption: 'other',
        pension_stopped: 'pension'
      }
      const data = await api.grievanceGuide({
        category: categoryMap[activeCategory] || 'other',
        description: formData.description,
        state: 'Uttar Pradesh'
      })
      const attachmentNames = attachments.map(file => file.name)
      const complaintText = [
          `To,`,
          data.department,
          ``,
          `Subject: Grievance regarding ${formData.issue_type}`,
          ``,
          `Respected Sir/Madam,`,
          ``,
          `I, ${formData.name}, resident of ${formData.village || formData.block || formData.district}, District ${formData.district}, wish to report the following grievance:`,
          ``,
          formData.description,
          formData.date_of_incident ? `Date of incident: ${formData.date_of_incident}` : '',
          formData.previous_complaint_no ? `Previous complaint number: ${formData.previous_complaint_no}` : '',
          attachmentNames.length ? `Supporting documents: ${attachmentNames.join(', ')}` : '',
          ``,
          `I request your office to examine this matter and provide the appropriate resolution.`,
          ``,
          `Sincerely,`,
          formData.name
      ].filter(Boolean).join('\n')
      setComplaint(complaintText)
      setNextSteps(data.escalation_path.map((description, index) => ({
        step: index + 1,
        title: `Escalation step ${index + 1}`,
        description
      })))
      setShowComplaint(true)
      window.setTimeout(() => document.getElementById('complaint-output')?.scrollIntoView({ behavior: 'smooth' }), 50)
    } catch (e) {
      setError(e.message || 'Failed to generate complaint. Please try again.')
    }
    setIsGenerating(false)
  }

  const handleCopy = () => {
    if (complaint) {
      navigator.clipboard.writeText(complaint)
      const btn = document.getElementById('copy-complaint')
      if (btn) {
        btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>'
        setTimeout(() => {
          btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>'
        }, 2000)
      }
    }
  }

  return (
    <div className="grievance-desk max-w-[1450px] mx-auto px-4 sm:px-8 py-8 sm:py-[70px] animate-fade-in">
      {/* HERO */}
      <section className="relative min-h-[430px] flex flex-col sm:flex-row items-end justify-between gap-12 p-10 sm:p-[70px] overflow-hidden bg-gradient-to-r from-[#160d0b] via-[#481710] to-[#9b2c1d] text-white rounded-[8px_8px_42px_8px]">
        <div className="relative z-10 max-w-[850px]">
          <div className="inline-flex items-center gap-2.5 mb-6 text-[13px] font-extrabold tracking-[2px] uppercase text-[#ffd5cc]">
            <Landmark size={19} />
            <span data-i18n="citizen_resolution">Citizen Resolution Desk</span>
          </div>
          <h1 className="text-[clamp(46px,5vw,78px)] leading-[0.98] tracking-[-4px] font-extrabold whitespace-pre-line" data-i18n="grievance_title">
            Don't know where to<br />
            <span className="text-[#ffb4a6]">raise your complaint?</span>
          </h1>
          <p className="max-w-[680px] mt-7 text-[18px] leading-relaxed text-white/75" data-i18n="grievance_sub">Choose your issue, follow the official escalation path, and prepare a formal complaint without getting lost in the process.</p>
        </div>
        <div className="relative z-10 flex items-center gap-4 p-5 bg-white/10 border border-white/15 backdrop-blur-sm rounded-[18px] flex-shrink-0 w-full sm:w-auto">
          <span className="w-[54px] h-[54px] flex-shrink-0 grid place-items-center rounded-full bg-white text-[#d92d20]">
            <ShieldCheck size={25} />
          </span>
          <div>
            <small className="text-[10px] font-extrabold tracking-[1.5px] text-[#ffb4a6]" data-i18n="guided_process">GUIDED PROCESS</small>
            <strong className="block mt-1 text-[18px]" data-i18n="three_stages">3 Simple Stages</strong>
            <span className="block mt-1 text-[12px] text-white/65">{t('identify')} → {t('resolve')} → {t('escalate')}</span>
          </div>
        </div>
        <div className="absolute w-[420px] h-[420px] -right-[130px] -top-[180px] border-[70px] border-white/5 rounded-full"></div>
      </section>

      {/* STAGE 1 — ISSUE SELECTOR */}
      <section className="grid grid-cols-[90px_1fr] mt-[75px]">
        <div className="flex flex-col items-center">
          <span className="w-[55px] h-[55px] grid place-items-center border border-[#d0d5dd] dark:border-[#344054] rounded-full bg-white dark:bg-[#182230] font-mono text-sm font-extrabold text-[#d92d20]">01</span>
          <div className="w-px flex-1 min-h-[80px] mt-4 bg-gradient-to-b from-[#d0d5dd] dark:from-[#344054] to-transparent"></div>
        </div>
        <div className="min-w-0 pl-5">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-12 mb-9">
            <div>
              <span className="block mb-2 text-[11px] font-extrabold tracking-[2px] text-[#d92d20]" data-i18n="start_here_grievance">START HERE</span>
              <h2 className="text-[clamp(30px,3vw,45px)] leading-[1.1] tracking-[-1.7px] text-[#101828] dark:text-[#f8fafc]" data-i18n="what_went_wrong">What went wrong?</h2>
            </div>
            <p className="max-w-[460px] text-[15px] leading-relaxed text-[#667085] dark:text-[#94a3b8]">{t('pick_problem')}</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 border-t border-l border-[#e4e7ec] dark:border-[#344054]">
            {categories.map((cat) => {
              const Icon = cat.icon
              return (
                <button
                  key={cat.id}
                  onClick={() => setActiveCategory(cat.id)}
                  className={`relative min-h-[160px] grid grid-cols-[45px_58px_1fr_35px] items-center gap-5 p-7 border-r border-b border-[#e4e7ec] dark:border-[#344054] text-left transition-all ${
                    activeCategory === cat.id
                      ? 'bg-[#101828] dark:bg-[#7a271a] text-white'
                      : 'bg-white dark:bg-[#182230] text-[#101828] dark:text-[#f8fafc] hover:bg-[#fff8f6] dark:hover:bg-[#1d2939]'
                  }`}
                >
                  <span className={`font-mono text-[11px] font-bold ${activeCategory === cat.id ? 'text-[#ffb4a6]' : 'text-[#98a2b3]'}`}>{String(categories.indexOf(cat) + 1).padStart(2, '0')}</span>
                  <span className={`w-[58px] h-[58px] grid place-items-center rounded-full ${activeCategory === cat.id ? 'bg-[#d92d20] text-white' : 'bg-[#fff0ed] text-[#d92d20]'}`}>
                    <Icon size={25} />
                  </span>
                  <div>
                    <strong className="block text-[19px] font-bold">{cat.label}</strong>
                    <small className={`text-[13px] leading-relaxed ${activeCategory === cat.id ? 'text-[#98a2b3]' : 'text-[#667085] dark:text-[#94a3b8]'}`}>{cat.desc}</small>
                  </div>
                  <span className={`w-[34px] h-[34px] grid place-items-center border rounded-full ${activeCategory === cat.id ? 'border-[#475467]' : 'border-[#e4e7ec] dark:border-[#344054]'}`}>
                    <ArrowUpRight size={16} />
                  </span>
                </button>
              )
            })}
          </div>
        </div>
      </section>

      {/* STAGE 2 — RESOLUTION ROADMAP */}
      <section className="grid grid-cols-[90px_1fr] mt-[75px]">
        <div className="flex flex-col items-center">
          <span className="w-[55px] h-[55px] grid place-items-center border border-[#d0d5dd] dark:border-[#344054] rounded-full bg-white dark:bg-[#182230] font-mono text-sm font-extrabold text-[#d92d20]">02</span>
          <div className="w-px flex-1 min-h-[80px] mt-4 bg-gradient-to-b from-[#d0d5dd] dark:from-[#344054] to-transparent"></div>
        </div>
        <div className="min-w-0 pl-5">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-12 mb-9">
            <div>
              <span className="block mb-2 text-[11px] font-extrabold tracking-[2px] text-[#d92d20]" data-i18n="resolution_route">RESOLUTION ROUTE</span>
              <h2 className="text-[clamp(30px,3vw,45px)] leading-[1.1] tracking-[-1.7px] text-[#101828] dark:text-[#f8fafc]" data-i18n="follow_path">Follow your escalation path</h2>
            </div>
            <p className="max-w-[460px] text-[15px] leading-relaxed text-[#667085] dark:text-[#94a3b8]">{t('escalation_help')}</p>
          </div>

          {loading ? (
            <div className="min-h-[180px] flex flex-col items-center justify-center gap-4 text-[#667085] dark:text-[#94a3b8]">
              <div className="w-[36px] h-[36px] border-3 border-[rgba(13,124,102,0.14)] border-t-[#0d7c66] rounded-full animate-spin-slow"></div>
              <span>{t('preparing_resolution')}</span>
            </div>
          ) : steps && (
            <div className="overflow-hidden bg-white dark:bg-[#182230] border border-[#e4e7ec] dark:border-[#344054]">
              <div className="flex items-center justify-between gap-5 p-[27px_32px] bg-[#f9fafb] dark:bg-[#0f172a] border-b border-[#e4e7ec] dark:border-[#344054]">
                <div>
                  <span className="block mb-1 text-[10px] font-extrabold tracking-[1.6px] text-[#d92d20]" data-i18n="current_case">CURRENT CASE</span>
                  <h3 className="text-2xl text-[#101828] dark:text-[#f8fafc]">{steps.name}</h3>
                </div>
                <span className="px-3 py-2 bg-white dark:bg-[#182230] border border-[#e4e7ec] dark:border-[#344054] rounded-full text-[12px] font-bold text-[#667085] dark:text-[#94a3b8]">{steps.steps.length} <span data-i18n="actions">Actions</span></span>
              </div>
              <div className="p-0 sm:p-0">
                {steps.steps.map((step, index) => (
                  <div key={index} className={`grid grid-cols-[65px_1fr] border-b border-[#e4e7ec] dark:border-[#344054] ${step.open ? 'step-open' : ''}`}>
                    <span className={`pt-[27px] font-mono text-sm font-extrabold ${step.open ? 'text-[#d92d20]' : 'text-[#98a2b3]'}`}>{step.step}</span>
                    <div>
                      <button
                        onClick={() => toggleStep(index)}
                        className="w-full flex items-center justify-between gap-5 p-[24px_0] border-0 bg-transparent text-left cursor-pointer"
                      >
                        <div>
                          <small className="text-[9px] font-extrabold tracking-[1.4px] text-[#98a2b3]">{t('action')} {step.step}</small>
                          <strong className="block text-[17px] text-[#101828] dark:text-[#f8fafc]">{step.title}</strong>
                        </div>
                        <div className="flex items-center gap-5">
                          {step.time && <span className="text-[12px] font-semibold text-[#667085] dark:text-[#94a3b8]">{step.time}</span>}
                          <span className="w-[35px] h-[35px] grid place-items-center border border-[#e4e7ec] dark:border-[#344054] rounded-full transition-transform">
                            <ChevronDown size={17} className={step.open ? 'rotate-180' : ''} />
                          </span>
                        </div>
                      </button>
                      {step.open && (
                        <div className="p-[0_70px_26px_0]">
                          <p className="max-w-[850px] text-[15px] leading-relaxed text-[#667085] dark:text-[#94a3b8]">{step.description}</p>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
              {steps.contacts && steps.contacts.length > 0 && (
                <div className="p-[30px_32px] bg-[#101828] text-white">
                  <div className="flex justify-between items-center mb-5">
                    <div>
                      <small className="text-[9px] tracking-[1.5px] text-[#fda29b]" data-i18n="need_direct_help">NEED DIRECT HELP?</small>
                      <h4 className="mt-1 text-xl" data-i18n="official_contacts">Official Contacts</h4>
                    </div>
                    <PhoneCall size={24} />
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                    {steps.contacts.map((contact, i) => (
                      <div key={i} className="flex items-center justify-between gap-4 p-4 bg-[#1d2939] border border-[#344054]">
                        <div>
                          <span className="text-[9px] font-extrabold tracking-[1px] text-[#98a2b3]">{contact.type}</span>
                          <strong className="block text-sm">{contact.name}</strong>
                        </div>
                        <a href={`tel:${contact.number}`} className="flex items-center gap-2 text-[#fda29b] font-bold">
                          <Phone size={15} />
                          {contact.number}
                        </a>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </section>

      {/* STAGE 3 — COMPLAINT BUILDER */}
      <section className="grid grid-cols-[90px_1fr] mt-[75px]">
        <div className="flex flex-col items-center">
          <span className="w-[55px] h-[55px] grid place-items-center border border-[#d0d5dd] dark:border-[#344054] rounded-full bg-white dark:bg-[#182230] font-mono text-sm font-extrabold text-[#d92d20]">03</span>
          <div className="w-px flex-1 min-h-[80px] mt-4 bg-gradient-to-b from-[#d0d5dd] dark:from-[#344054] to-transparent"></div>
        </div>
        <div className="min-w-0 pl-5">
          <div className="grid grid-cols-1 lg:grid-cols-[0.72fr_1.28fr] overflow-hidden bg-[#101828] rounded-[0_35px_0_0]">
            {/* Left Intro */}
            <div className="p-8 sm:p-14 bg-[radial-gradient(circle_at_20%_100%,rgba(217,45,32,0.25),transparent_38%),#101828] text-white">
              <span className="block mb-2 text-[11px] font-extrabold tracking-[2px] text-[#d92d20]" data-i18n="escalation_tool">ESCALATION TOOL</span>
              <h2 className="mt-3 mb-5 text-[39px] leading-[1.05] tracking-[-1.8px] whitespace-pre-line" data-i18n="complaint_title">Turn your issue into a <span className="text-[#fda29b]">formal complaint.</span></h2>
              <p className="text-[15px] leading-relaxed text-[#98a2b3]" data-i18n="complaint_sub">Provide the essential details and JanMitra AI will prepare a structured complaint draft for the concerned authority.</p>
              <div className="flex flex-col gap-6 mt-11">
                {[
                  { icon: User, title: 'your_details', desc: 'name_location' },
                  { icon: MessageSquareWarning, title: 'describe_problem', desc: 'explain_happened' },
                  { icon: FileCheck2, title: 'get_draft', desc: 'ready_letter' },
                ].map((item, i) => (
                  <div key={i} className="flex gap-4">
                    <span className="w-[40px] h-[40px] flex-shrink-0 grid place-items-center border border-[#475467] rounded-full text-[#fda29b]">
                      <item.icon size={17} />
                    </span>
                    <div>
                      <strong className="text-sm text-white" data-i18n={item.title}>{item.title}</strong>
                      <p className="text-[12px] leading-relaxed text-[#98a2b3]" data-i18n={item.desc}>{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Form */}
            <div className="p-8 sm:p-12 bg-white dark:bg-[#182230]">
              <div className="flex justify-between items-center mb-8 pb-5 border-b border-[#e4e7ec] dark:border-[#344054]">
                <div>
                  <span className="text-[9px] font-extrabold tracking-[1.5px] text-[#d92d20]" data-i18n="complaint_builder">COMPLAINT BUILDER</span>
                  <h3 className="mt-1.5 text-2xl text-[#101828] dark:text-[#f8fafc]" data-i18n="citizen_info">Citizen Information</h3>
                </div>
                <span className="flex items-center gap-2 text-[11px] font-bold text-[#039855]">
                  <LockKeyhole size={15} />
                  <span data-i18n="form_data">Form Data</span>
                </span>
              </div>

              <form onSubmit={handleSubmit} className="space-y-5">
                {error && (
                  <div className="p-4 rounded-lg bg-red-50 dark:bg-red-950/30 text-sm font-semibold text-red-700 dark:text-red-300">
                    {error}
                  </div>
                )}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div>
                    <label className="block mb-2 text-[12px] font-bold text-[#344054] dark:text-[#94a3b8]" data-i18n="full_name">Full Name <span className="text-[#d92d20]">*</span></label>
                    <input
                      id="name"
                      value={formData.name}
                      onChange={handleFormChange}
                      placeholder="e.g. Ram Kumar"
                      required
                      className="w-full p-4 border border-[#d0d5dd] dark:border-[#344054] rounded-[5px] bg-white dark:bg-[#0f172a] text-[#101828] dark:text-[#f8fafc] outline-none focus:border-[#d92d20] focus:shadow-[0_0_0_3px_rgba(217,45,32,0.08)] transition-all"
                    />
                  </div>
                  <div>
                    <label className="block mb-2 text-[12px] font-bold text-[#344054] dark:text-[#94a3b8]" data-i18n="district">District <span className="text-[#d92d20]">*</span></label>
                    <input
                      id="district"
                      value={formData.district}
                      onChange={handleFormChange}
                      placeholder="e.g. Lucknow"
                      required
                      className="w-full p-4 border border-[#d0d5dd] dark:border-[#344054] rounded-[5px] bg-white dark:bg-[#0f172a] text-[#101828] dark:text-[#f8fafc] outline-none focus:border-[#d92d20] focus:shadow-[0_0_0_3px_rgba(217,45,32,0.08)] transition-all"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div>
                    <label className="block mb-2 text-[12px] font-bold text-[#344054] dark:text-[#94a3b8]" data-i18n="block_tehsil">Block / Tehsil</label>
                    <input
                      id="block"
                      value={formData.block}
                      onChange={handleFormChange}
                      placeholder="e.g. Malihabad"
                      className="w-full p-4 border border-[#d0d5dd] dark:border-[#344054] rounded-[5px] bg-white dark:bg-[#0f172a] text-[#101828] dark:text-[#f8fafc] outline-none focus:border-[#d92d20] focus:shadow-[0_0_0_3px_rgba(217,45,32,0.08)] transition-all"
                    />
                  </div>
                  <div>
                    <label className="block mb-2 text-[12px] font-bold text-[#344054] dark:text-[#94a3b8]" data-i18n="village_ward">Village / Ward</label>
                    <input
                      id="village"
                      value={formData.village}
                      onChange={handleFormChange}
                      placeholder="e.g. Rampur"
                      className="w-full p-4 border border-[#d0d5dd] dark:border-[#344054] rounded-[5px] bg-white dark:bg-[#0f172a] text-[#101828] dark:text-[#f8fafc] outline-none focus:border-[#d92d20] focus:shadow-[0_0_0_3px_rgba(217,45,32,0.08)] transition-all"
                    />
                  </div>
                </div>
                <div>
                  <label className="block mb-2 text-[12px] font-bold text-[#344054] dark:text-[#94a3b8]" data-i18n="issue_type">Issue Type <span className="text-[#d92d20]">*</span></label>
                  <div className="relative">
                    <ListFilter size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-[#64748b] pointer-events-none" />
                    <select
                      id="issue_type"
                      value={formData.issue_type}
                      onChange={handleFormChange}
                      required
                      className="w-full p-4 pl-12 border border-[#d0d5dd] dark:border-[#344054] rounded-[5px] bg-white dark:bg-[#0f172a] text-[#101828] dark:text-[#f8fafc] appearance-none outline-none focus:border-[#d92d20] focus:shadow-[0_0_0_3px_rgba(217,45,32,0.08)] transition-all"
                    >
                      <option value="" data-i18n="select_category">— Select Official Issue Category —</option>
                      <option value="Ration Denied or Short Supply">{t('ration_denied_short')}</option>
                      <option value="Government Scheme Benefit Not Received">{t('scheme_benefit_not_received')}</option>
                      <option value="Corruption / Bribery by Government Official">{t('corruption_bribery')}</option>
                      <option value="Pension Stopped or Not Received">{t('pension_stopped')}</option>
                      <option value="Other PDS/Welfare Issue">{t('other_issue')}</option>
                    </select>
                    <ChevronDown size={18} className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none" />
                  </div>
                </div>
                <div>
                  <label className="block mb-2 text-[12px] font-bold text-[#344054] dark:text-[#94a3b8]" data-i18n="issue_desc">Description of Issue <span className="text-[#d92d20]">*</span></label>
                  <textarea
                    id="description"
                    value={formData.description}
                    onChange={handleFormChange}
                    rows="5"
                    placeholder="Explain what happened, when it happened, and which office or person was involved..."
                    required
                    className="w-full p-4 border border-[#d0d5dd] dark:border-[#344054] rounded-[5px] bg-white dark:bg-[#0f172a] text-[#101828] dark:text-[#f8fafc] resize-vertical outline-none focus:border-[#d92d20] focus:shadow-[0_0_0_3px_rgba(217,45,32,0.08)] transition-all min-h-[135px]"
                  />
                </div>
                <div>
                  <label className="block mb-2 text-[12px] font-bold text-[#344054] dark:text-[#94a3b8]">{t('supporting_documents')}</label>
                  <label className="min-h-[86px] px-5 py-4 flex items-center gap-4 border-2 border-dashed border-[#d0d5dd] dark:border-[#344054] rounded-xl bg-[#f9fafb] dark:bg-[#0f172a] cursor-pointer hover:border-[#d92d20] transition-colors">
                    <span className="w-11 h-11 grid place-items-center rounded-full bg-white dark:bg-[#182230] text-[#d92d20] shadow-sm">
                      <FileUp size={20} />
                    </span>
                    <span>
                      <strong className="block text-sm">{attachments.length ? `${attachments.length} file${attachments.length > 1 ? 's' : ''} selected` : 'Choose supporting files'}</strong>
                      <small className="text-[#667085] dark:text-[#94a3b8]">{t('supporting_file_types')}</small>
                    </span>
                    <input type="file" multiple accept=".pdf,.jpg,.jpeg,.png,.txt,application/pdf,image/jpeg,image/png,text/plain" onChange={handleAttachments} className="sr-only" />
                  </label>
                  {attachments.length > 0 && (
                    <div className="mt-3 space-y-2">
                      {attachments.map(file => (
                        <div key={`${file.name}-${file.size}`} className="flex items-center justify-between gap-3 px-3 py-2 rounded-lg bg-[#f4f7f6] dark:bg-[#101817] text-xs">
                          <span className="flex min-w-0 items-center gap-2"><Paperclip size={14} /><span className="truncate">{file.name}</span></span>
                          <button type="button" onClick={() => setAttachments(current => current.filter(item => item !== file))} className="font-bold text-red-600">{t('remove')}</button>
                        </div>
                      ))}
                    </div>
                  )}
                  <p className="mt-2 text-[11px] leading-5 text-[#667085] dark:text-[#94a3b8]">{t('attachment_disclaimer')}</p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div>
                    <label className="block mb-2 text-[12px] font-bold text-[#344054] dark:text-[#94a3b8]" data-i18n="incident_date">Date of Incident</label>
                    <input
                      id="date_of_incident"
                      type="date"
                      value={formData.date_of_incident}
                      onChange={handleFormChange}
                      className="w-full p-4 border border-[#d0d5dd] dark:border-[#344054] rounded-[5px] bg-white dark:bg-[#0f172a] text-[#101828] dark:text-[#f8fafc] outline-none focus:border-[#d92d20] focus:shadow-[0_0_0_3px_rgba(217,45,32,0.08)] transition-all"
                    />
                  </div>
                  <div>
                    <label className="block mb-2 text-[12px] font-bold text-[#344054] dark:text-[#94a3b8]" data-i18n="previous_complaint">Previous Complaint No.</label>
                    <input
                      id="previous_complaint_no"
                      value={formData.previous_complaint_no}
                      onChange={handleFormChange}
                      placeholder="If already reported"
                      className="w-full p-4 border border-[#d0d5dd] dark:border-[#344054] rounded-[5px] bg-white dark:bg-[#0f172a] text-[#101828] dark:text-[#f8fafc] outline-none focus:border-[#d92d20] focus:shadow-[0_0_0_3px_rgba(217,45,32,0.08)] transition-all"
                    />
                  </div>
                </div>
                <button
                  type="submit"
                  disabled={isGenerating}
                  className="w-full min-h-[57px] flex items-center justify-center gap-3 mt-2.5 rounded-[5px] bg-[#d92d20] text-white text-sm font-bold hover:bg-[#b42318] transition-all disabled:opacity-60 disabled:cursor-wait"
                >
                  {isGenerating ? (
                    <>
                      <Loader size={18} className="animate-spin" />
                      <span>{t('generating_document')}</span>
                    </>
                  ) : (
                    <>
                      <span data-i18n="generate_complaint">Generate Complaint Draft</span>
                      <MoveRight size={18} />
                    </>
                  )}
                </button>
              </form>
            </div>
          </div>

          {/* COMPLAINT OUTPUT */}
          {showComplaint && complaint && (
            <div id="complaint-output" className="mt-16">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4 mb-6">
                <div>
                  <span className="block mb-2 text-[11px] font-extrabold tracking-[2px] text-[#d92d20]" data-i18n="document_ready">DOCUMENT READY</span>
                  <h2 className="text-[clamp(30px,3vw,45px)] leading-[1.1] tracking-[-1.7px] text-[#101828] dark:text-[#f8fafc]" data-i18n="your_complaint">Your complaint draft</h2>
                </div>
                <span className="flex items-center gap-2 px-3 py-2 rounded-full bg-[#ecfdf3] text-[#039855] text-[12px] font-bold">
                  <BadgeCheck size={16} />
                  <span data-i18n="generated">Generated</span>
                </span>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_330px] gap-6 items-start">
                <div className="overflow-hidden bg-white dark:bg-[#182230] border border-[#d0d5dd] dark:border-[#344054] shadow-[0_25px_60px_rgba(16,24,40,0.08)]">
                  <div className="flex justify-between items-center p-[17px_22px] border-b border-[#e4e7ec] dark:border-[#344054] bg-[#f9fafb] dark:bg-[#0f172a]">
                    <div className="flex items-center gap-3">
                      <FileCheck2 size={20} className="text-[#d92d20]" />
                      <div>
                        <small className="text-[8px] tracking-[1.4px] text-[#98a2b3]" data-i18n="formal_letter">FORMAL LETTER</small>
                        <strong className="block text-sm text-[#101828] dark:text-[#f8fafc]" data-i18n="complaint_draft">Complaint Draft</strong>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button onClick={handleCopy} id="copy-complaint" className="w-[37px] h-[37px] grid place-items-center border border-[#e4e7ec] dark:border-[#344054] rounded-[5px] bg-white dark:bg-[#0f172a] hover:bg-[#f0f0f0] dark:hover:bg-[#1a2a22] transition-all">
                        <Copy size={18} />
                      </button>
                      <button onClick={() => window.print()} className="w-[37px] h-[37px] grid place-items-center border border-[#e4e7ec] dark:border-[#344054] rounded-[5px] bg-white dark:bg-[#0f172a] hover:bg-[#f0f0f0] dark:hover:bg-[#1a2a22] transition-all">
                        <Printer size={18} />
                      </button>
                    </div>
                  </div>
                  <div className="min-h-[500px] p-[55px] bg-[#fdfdfc] dark:bg-[#0f172a]">
                    <pre className="whitespace-pre-wrap break-words font-serif text-[16px] leading-[1.9] text-[#1d2939] dark:text-[#edf5f2]">{complaint}</pre>
                  </div>
                </div>

                {/* Next Steps */}
                <div className="sticky top-[95px] overflow-hidden bg-[#101828] text-white">
                  <div className="flex gap-3 items-center p-5 border-b border-[#344054]">
                    <span className="w-[40px] h-[40px] grid place-items-center rounded-full bg-[#d92d20]">
                      <Route size={20} />
                    </span>
                    <div>
                      <small className="text-[8px] tracking-[1.3px] text-[#98a2b3]" data-i18n="what_now">WHAT NOW?</small>
                      <h3 className="mt-1 text-[17px]" data-i18n="submission_route">Submission Route</h3>
                    </div>
                  </div>
                  <div className="p-[10px_22px_22px]">
                    {nextSteps.map((step, i) => (
                      <div key={i} className="grid grid-cols-[30px_1fr] gap-3 py-[18px] border-b border-[#344054] last:border-0">
                        <span className="w-[28px] h-[28px] grid place-items-center border border-[#475467] rounded-full font-mono text-[10px] text-[#fda29b]">{step.step}</span>
                        <div>
                          <strong className="block text-[13px]">{step.title}</strong>
                          <p className="text-[11px] leading-relaxed text-[#98a2b3]">{step.description}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
