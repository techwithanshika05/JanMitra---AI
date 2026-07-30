import { useState, useEffect } from 'react'
import { Files, ClipboardCheck, Landmark, ChevronDown, Clock, IndianRupee, Printer, Download, Check, Info, Lightbulb, FileSearch, CheckCheck, BadgeCheck } from 'lucide-react'

export default function Checklist() {
  const [selectedService, setSelectedService] = useState('')
  const [checklist, setChecklist] = useState(null)
  const [checkedItems, setCheckedItems] = useState([])
  const [loading, setLoading] = useState(false)

  const services = [
    { id: 'new_ration_card', name: 'New Ration Card Application', processing_time: '15-30 days', fee: 'Free' },
    { id: 'add_member_ration', name: 'Add Member to Ration Card', processing_time: '7-15 days', fee: 'Free' },
    { id: 'old_age_pension', name: 'Old Age Pension (Vridhavastha)', processing_time: '30-60 days', fee: 'Free' },
    { id: 'pm_kisan', name: 'PM Kisan Samman Nidhi', processing_time: '15-30 days', fee: 'Free' },
    { id: 'up_scholarship', name: 'UP Scholarship Application', processing_time: '45-90 days', fee: 'Free' },
    { id: 'mgnrega_job_card', name: 'MGNREGA Job Card', processing_time: '7-14 days', fee: 'Free' },
    { id: 'ayushman_bharat', name: 'Ayushman Bharat (PMJAY)', processing_time: '15-30 days', fee: 'Free' },
    { id: 'pm_ujjwala', name: 'PM Ujjwala Yojana (LPG)', processing_time: '15-30 days', fee: 'Free' },
    { id: 'kanya_sumangala', name: 'Kanya Sumangala Yojana', processing_time: '30-60 days', fee: 'Free' },
    { id: 'widow_pension', name: 'Widow Pension', processing_time: '30-60 days', fee: 'Free' },
  ]

  const documentData = {
    new_ration_card: {
      name: 'New Ration Card Application',
      processing_time: '15-30 days',
      fee: 'Free',
      documents: [
        { name: 'Aadhaar Card', mandatory: true, note: 'All family members' },
        { name: 'Residence Proof', mandatory: true, note: 'Electricity bill / Voter ID' },
        { name: 'Passport Size Photos', mandatory: true, note: '2 copies each' },
        { name: 'Income Certificate', mandatory: false, note: 'From Lekhpal/SDM if required' },
        { name: 'Family Register', mandatory: true, note: 'From Gram Panchayat' },
        { name: 'Caste Certificate', mandatory: false, note: 'For SC/ST/OBC' },
      ]
    },
    old_age_pension: {
      name: 'Old Age Pension (Vridhavastha)',
      processing_time: '30-60 days',
      fee: 'Free',
      documents: [
        { name: 'Aadhaar Card', mandatory: true, note: 'Self-attested copy' },
        { name: 'Age Proof', mandatory: true, note: 'Birth certificate / Voter ID' },
        { name: 'Bank Account Details', mandatory: true, note: 'Passbook copy' },
        { name: 'Passport Size Photos', mandatory: true, note: '2 copies' },
        { name: 'Income Certificate', mandatory: true, note: 'Below poverty line' },
        { name: 'Residence Proof', mandatory: true, note: 'Electricity bill / Voter ID' },
      ]
    },
    pm_kisan: {
      name: 'PM Kisan Samman Nidhi',
      processing_time: '15-30 days',
      fee: 'Free',
      documents: [
        { name: 'Aadhaar Card', mandatory: true, note: 'Self-attested copy' },
        { name: 'Bank Account Details', mandatory: true, note: 'Passbook copy' },
        { name: 'Land Ownership Proof', mandatory: true, note: 'Khatauni / Patta' },
        { name: 'Passport Size Photos', mandatory: true, note: '2 copies' },
        { name: 'Mobile Number', mandatory: true, note: 'Registered with Aadhaar' },
      ]
    },
    ayushman_bharat: {
      name: 'Ayushman Bharat (PMJAY)',
      processing_time: '15-30 days',
      fee: 'Free',
      documents: [
        { name: 'Aadhaar Card', mandatory: true, note: 'Family members' },
        { name: 'Ration Card', mandatory: true, note: 'For family verification' },
        { name: 'Income Certificate', mandatory: true, note: 'BPL/EWS category' },
        { name: 'Passport Size Photos', mandatory: true, note: '2 copies each' },
        { name: 'Mobile Number', mandatory: true, note: 'For SMS alerts' },
      ]
    },
    mgnrega_job_card: {
      name: 'MGNREGA Job Card',
      processing_time: '7-14 days',
      fee: 'Free',
      documents: [
        { name: 'Aadhaar Card', mandatory: true, note: 'All family members' },
        { name: 'Residence Proof', mandatory: true, note: 'Voter ID / Electricity bill' },
        { name: 'Bank Account Details', mandatory: true, note: 'For wage payment' },
        { name: 'Passport Size Photos', mandatory: true, note: '2 copies' },
        { name: 'Caste Certificate', mandatory: false, note: 'For SC/ST/OBC' },
      ]
    },
    up_scholarship: {
      name: 'UP Scholarship Application',
      processing_time: '45-90 days',
      fee: 'Free',
      documents: [
        { name: 'Aadhaar Card', mandatory: true, note: 'Student' },
        { name: 'Caste Certificate', mandatory: true, note: 'For SC/ST/OBC' },
        { name: 'Income Certificate', mandatory: true, note: 'Family income proof' },
        { name: 'Previous Marksheet', mandatory: true, note: 'Last exam passed' },
        { name: 'Bank Account Details', mandatory: true, note: 'Student/Parent account' },
        { name: 'Passport Size Photos', mandatory: true, note: '2 copies' },
        { name: 'Bonafide Certificate', mandatory: true, note: 'From school/college' },
      ]
    },
    pm_ujjwala: {
      name: 'PM Ujjwala Yojana (LPG)',
      processing_time: '15-30 days',
      fee: 'Free',
      documents: [
        { name: 'Aadhaar Card', mandatory: true, note: 'Self-attested copy' },
        { name: 'Bank Account Details', mandatory: true, note: 'For subsidy transfer' },
        { name: 'Ration Card', mandatory: true, note: 'For family verification' },
        { name: 'Passport Size Photos', mandatory: true, note: '2 copies' },
        { name: 'Income Certificate', mandatory: true, note: 'BPL category' },
      ]
    },
    kanya_sumangala: {
      name: 'Kanya Sumangala Yojana',
      processing_time: '30-60 days',
      fee: 'Free',
      documents: [
        { name: 'Aadhaar Card', mandatory: true, note: 'Girl child & parents' },
        { name: 'Birth Certificate', mandatory: true, note: 'Girl child' },
        { name: 'Bank Account Details', mandatory: true, note: 'Joint account with mother' },
        { name: 'Income Certificate', mandatory: true, note: 'Family income < 3 Lakh' },
        { name: 'Passport Size Photos', mandatory: true, note: '2 copies' },
        { name: 'Caste Certificate', mandatory: false, note: 'For SC/ST/OBC' },
      ]
    },
    widow_pension: {
      name: 'Widow Pension',
      processing_time: '30-60 days',
      fee: 'Free',
      documents: [
        { name: 'Aadhaar Card', mandatory: true, note: 'Self-attested copy' },
        { name: 'Husband Death Certificate', mandatory: true, note: 'Original copy' },
        { name: 'Marriage Certificate', mandatory: true, note: 'Proof of marriage' },
        { name: 'Bank Account Details', mandatory: true, note: 'Passbook copy' },
        { name: 'Passport Size Photos', mandatory: true, note: '2 copies' },
        { name: 'Income Certificate', mandatory: true, note: 'Below poverty line' },
        { name: 'Residence Proof', mandatory: true, note: 'Electricity bill / Voter ID' },
      ]
    },
    add_member_ration: {
      name: 'Add Member to Ration Card',
      processing_time: '7-15 days',
      fee: 'Free',
      documents: [
        { name: 'Aadhaar Card', mandatory: true, note: 'New member' },
        { name: 'Birth Certificate', mandatory: true, note: 'For children' },
        { name: 'Marriage Certificate', mandatory: true, note: 'For spouse addition' },
        { name: 'Passport Size Photos', mandatory: true, note: '2 copies' },
        { name: 'Residence Proof', mandatory: true, note: 'Current address proof' },
      ]
    }
  }

  const handleServiceChange = (e) => {
    const id = e.target.value
    setSelectedService(id)
    if (id && documentData[id]) {
      setChecklist(documentData[id])
      setCheckedItems([])
    } else {
      setChecklist(null)
      setCheckedItems([])
    }
  }

  const toggleCheck = (index) => {
    setCheckedItems(prev => 
      prev.includes(index) 
        ? prev.filter(i => i !== index)
        : [...prev, index]
    )
  }

  const getProgress = () => {
    if (!checklist) return 0
    return Math.round((checkedItems.length / checklist.documents.length) * 100)
  }

  const handlePrint = () => {
    window.print()
  }

  const handleDownloadPDF = async () => {
    if (!checklist) return
    
    try {
      const res = await fetch('/api/pdf/checklist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          service_name: checklist.name,
          documents: checklist.documents
        })
      })
      if (!res.ok) throw new Error('PDF error')
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'janmitra_checklist.pdf'
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      alert('PDF download failed. Please try again.')
    }
  }

  return (
    <div className="checklist-desk max-w-[1450px] mx-auto px-4 sm:px-8 py-8 sm:py-[34px]">
      {/* INTRO */}
      <section className="relative min-h-[330px] p-8 sm:p-14 flex items-center justify-between gap-10 overflow-hidden text-white bg-gradient-to-r from-[#092d24] via-[#0b6847] to-[#11865e] rounded-t-[12px]">
        <div className="relative z-10 max-w-[790px]">
          <div className="inline-flex items-center gap-2.5 mb-6 text-[0.76rem] font-extrabold tracking-[0.16em] text-[#dff45f]">
            <Files size={18} />
            DOCUMENT PREPARATION DESK
          </div>
          <h1 className="text-[clamp(2.8rem,5vw,5.3rem)] leading-[0.96] tracking-[-0.06em] font-extrabold">
            Get your documents<br />
            <span className="text-[#dff45f]">ready before you go.</span>
          </h1>
          <p className="max-w-[680px] mt-6 text-[1.08rem] leading-relaxed text-white/75">
            Choose the government service you're applying for. JanMitra AI will prepare a clear document checklist for you.
          </p>
        </div>
        <div className="relative z-10 w-[180px] flex-shrink-0 text-center font-mono text-[0.72rem] leading-relaxed tracking-[0.08em] text-white/55 hidden lg:block">
          <div className="w-[112px] h-[112px] mx-auto mb-4 grid place-items-center border border-white/25 rounded-full animate-float">
            <ClipboardCheck size={42} className="text-[#dff45f]" />
          </div>
          JanMitra AI<br />Document Desk
        </div>
        <div className="absolute w-[420px] h-[420px] -right-[180px] -bottom-[260px] border border-white/20 rounded-full shadow-[0_0_0_50px_rgba(255,255,255,0.025)]"></div>
      </section>

      {/* MAIN DESK */}
      <section className="grid grid-cols-1 lg:grid-cols-[minmax(300px,0.78fr)_minmax(0,1.65fr)] bg-[#f4f0e6] dark:bg-[#111713] rounded-b-[12px] overflow-hidden">
        {/* LEFT PANEL */}
        <aside className="p-8 sm:p-[55px_42px] bg-[#ebe5d7] dark:bg-[#19211c] border-r border-[#d4cebf] dark:border-[#303830]">
          <div className="font-mono text-[4rem] leading-none font-bold tracking-[-0.08em] text-[rgba(23,33,27,0.12)] dark:text-[rgba(255,255,255,0.08)] mb-11">01</div>
          <div>
            <span className="font-mono text-[0.7rem] font-bold tracking-[0.15em] text-[#0b6847] dark:text-[#6ef0ca]">START HERE</span>
            <h2 className="mt-2.5 mb-3 text-3xl leading-[1.08] tracking-[-0.04em] text-[#17211b] dark:text-[#edf7f4]">What are you applying for?</h2>
            <p className="text-[0.96rem] leading-relaxed text-[#6d706a] dark:text-[#94a3b8]">Select one service and we'll prepare the documents you need.</p>
          </div>

          <div className="mt-9">
            <label className="block mb-2.5 text-[0.75rem] font-extrabold uppercase tracking-[0.09em] text-[#4d554f] dark:text-[#94a3b8]">Government Service</label>
            <div className="relative flex items-center bg-[#fffef9] dark:bg-[#101512] border-2 border-[#17211b] dark:border-[#dbe5d9] shadow-[5px_5px_0_#17211b] dark:shadow-[5px_5px_0_#526257] focus-within:translate-x-[-2px] focus-within:translate-y-[-2px] focus-within:shadow-[8px_8px_0_#0b6847] transition-all">
              <span className="w-[54px] h-[58px] flex-shrink-0 grid place-items-center text-[#0b6847] dark:text-[#6ef0ca] border-r border-[#ddd8cc] dark:border-[#303830]">
                <Landmark size={21} />
              </span>
              <select 
                value={selectedService}
                onChange={handleServiceChange}
                className="w-full h-[58px] px-4 pr-12 appearance-none border-0 outline-none bg-transparent text-[0.93rem] font-semibold text-[#17211b] dark:text-[#edf7f4] cursor-pointer"
              >
                <option value="">Choose your service</option>
                {services.map(s => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
              <ChevronDown size={19} className="absolute right-4 pointer-events-none" />
            </div>
          </div>

          <div className="relative mt-12">
            <div className="absolute top-[19px] bottom-[19px] left-[18px] w-[1px] bg-[#c5beae] dark:bg-[#303830]"></div>
            <div className="relative z-10 flex items-start gap-4 mb-6">
              <span className="w-[37px] h-[37px] flex-shrink-0 grid place-items-center border border-[#b7b0a2] dark:border-[#303830] rounded-full bg-[#ebe5d7] dark:bg-[#19211c] font-mono text-[0.72rem] font-bold text-[#0b6847] dark:text-[#6ef0ca]">1</span>
              <div>
                <strong className="block text-[0.91rem] text-[#17211b] dark:text-[#edf7f4]">Select service</strong>
                <p className="text-[0.8rem] leading-relaxed text-[#7c7c73] dark:text-[#94a3b8]">Tell us what you're applying for.</p>
              </div>
            </div>
            <div className="relative z-10 flex items-start gap-4 mb-6">
              <span className="w-[37px] h-[37px] flex-shrink-0 grid place-items-center border border-[#b7b0a2] dark:border-[#303830] rounded-full bg-[#ebe5d7] dark:bg-[#19211c] font-mono text-[0.72rem] font-bold text-[#0b6847] dark:text-[#6ef0ca]">2</span>
              <div>
                <strong className="block text-[0.91rem] text-[#17211b] dark:text-[#edf7f4]">Collect documents</strong>
                <p className="text-[0.8rem] leading-relaxed text-[#7c7c73] dark:text-[#94a3b8]">Tick each document when ready.</p>
              </div>
            </div>
            <div className="relative z-10 flex items-start gap-4">
              <span className="w-[37px] h-[37px] flex-shrink-0 grid place-items-center border border-[#b7b0a2] dark:border-[#303830] rounded-full bg-[#ebe5d7] dark:bg-[#19211c] font-mono text-[0.72rem] font-bold text-[#0b6847] dark:text-[#6ef0ca]">3</span>
              <div>
                <strong className="block text-[0.91rem] text-[#17211b] dark:text-[#edf7f4]">Take your checklist</strong>
                <p className="text-[0.8rem] leading-relaxed text-[#7c7c73] dark:text-[#94a3b8]">Print it or save it as PDF.</p>
              </div>
            </div>
          </div>

          <div className="mt-10 p-[18px] flex gap-3 bg-[#dff45f] dark:bg-[#4a5a1a] border border-[#17211b] dark:border-[#6ef0ca]">
            <Lightbulb size={20} className="flex-shrink-0" />
            <div>
              <strong className="text-[0.85rem]">Quick tip</strong>
              <p className="mt-1 text-[0.76rem] leading-relaxed">Keep originals and photocopies together before visiting the office.</p>
            </div>
          </div>
        </aside>

        {/* RIGHT PAPER */}
        <div className="min-h-[700px] p-8 sm:p-11 bg-[#fffef9] dark:bg-[#141916] bg-[linear-gradient(rgba(23,33,27,0.025)_1px,transparent_1px)] bg-[length:100%_38px]">
          {!checklist ? (
            <div className="min-h-[610px] flex flex-col items-center justify-center text-center">
              <div className="w-[105px] h-[105px] grid place-items-center border-2 border-dashed border-[#a9a99e] dark:border-[#303830] rounded-full -rotate-[7deg] text-[#8b8d84] dark:text-[#94a3b8]">
                <FileSearch size={40} />
              </div>
              <span className="mt-6 font-mono text-[0.68rem] font-bold tracking-[0.16em] text-[#96968c] dark:text-[#94a3b8]">WAITING FOR SERVICE</span>
              <h2 className="mt-3 mb-2 text-3xl tracking-[-0.04em] text-[#17211b] dark:text-[#edf7f4]">Your checklist will appear here.</h2>
              <p className="max-w-[440px] text-[#83837b] dark:text-[#94a3b8] leading-relaxed">Select a government service from the left panel to begin.</p>
              <div className="w-[min(400px,80%)] mt-10">
                <div className="h-[1px] my-[18px] bg-[#e2dfd6] dark:bg-[#303830]"></div>
                <div className="h-[1px] my-[18px] bg-[#e2dfd6] dark:bg-[#303830]"></div>
                <div className="h-[1px] my-[18px] bg-[#e2dfd6] dark:bg-[#303830]"></div>
                <div className="h-[1px] my-[18px] bg-[#e2dfd6] dark:bg-[#303830]"></div>
              </div>
            </div>
          ) : (
            <>
              {/* PAPER HEADER */}
              <div className="flex flex-col sm:flex-row items-start justify-between gap-7 pb-8 border-b-2 border-[#17211b] dark:border-[#edf7f4]">
                <div>
                  <span className="font-mono text-[0.68rem] font-bold tracking-[0.15em] text-[#0b6847] dark:text-[#6ef0ca]">DOCUMENT REQUIREMENT SHEET</span>
                  <h2 className="mt-2 mb-5 text-[clamp(2rem,3vw,3.3rem)] leading-none tracking-[-0.055em] text-[#17211b] dark:text-[#edf7f4]">{checklist.name}</h2>
                  <div className="flex flex-wrap gap-7">
                    <div className="flex flex-col gap-1.5">
                      <span className="font-mono text-[0.61rem] font-bold tracking-[0.12em] text-[#99988f] dark:text-[#94a3b8]">PROCESSING</span>
                      <strong className="flex items-center gap-2 text-[0.85rem] text-[#444b45] dark:text-[#edf7f4]">
                        <Clock size={15} className="text-[#0b6847] dark:text-[#6ef0ca]" />
                        {checklist.processing_time}
                      </strong>
                    </div>
                    <div className="flex flex-col gap-1.5">
                      <span className="font-mono text-[0.61rem] font-bold tracking-[0.12em] text-[#99988f] dark:text-[#94a3b8]">APPLICATION FEE</span>
                      <strong className="flex items-center gap-2 text-[0.85rem] text-[#444b45] dark:text-[#edf7f4]">
                        <IndianRupee size={15} className="text-[#0b6847] dark:text-[#6ef0ca]" />
                        {checklist.fee}
                      </strong>
                    </div>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button onClick={handlePrint} className="min-h-[45px] px-4 flex items-center justify-center gap-2 border border-[#17211b] dark:border-[#edf7f4] bg-transparent text-[0.78rem] font-bold text-[#17211b] dark:text-[#edf7f4] hover:-translate-y-0.5 hover:shadow-[3px_3px_0_#17211b] dark:hover:shadow-[3px_3px_0_#edf7f4] transition-all">
                    <Printer size={16} />
                    <span>Print</span>
                  </button>
                  <button onClick={handleDownloadPDF} className="min-h-[45px] px-4 flex items-center justify-center gap-2 border border-[#17211b] dark:border-[#edf7f4] bg-[#17211b] dark:bg-[#edf7f4] text-white dark:text-[#17211b] text-[0.78rem] font-bold hover:-translate-y-0.5 hover:shadow-[3px_3px_0_#17211b] dark:hover:shadow-[3px_3px_0_#edf7f4] transition-all">
                    <Download size={16} />
                    <span>Download PDF</span>
                  </button>
                </div>
              </div>

              {/* COMPLETION METER */}
              <div className="my-9 grid grid-cols-[120px_1fr] border border-[#d7d3c8] dark:border-[#303830] bg-[#f7f4eb] dark:bg-[#19201b]">
                <div className="p-[24px_20px] flex flex-col justify-center bg-[#0b6847] dark:bg-[#1a5a3e] text-white">
                  <strong className="font-mono text-3xl">{getProgress()}%</strong>
                  <span className="mt-1 text-[0.61rem] font-extrabold tracking-[0.13em] text-[#dff45f]">READY</span>
                </div>
                <div className="p-[23px_26px]">
                  <div className="flex items-center justify-between gap-4 mb-3.5">
                    <strong className="text-[0.9rem] text-[#17211b] dark:text-[#edf7f4]">Document readiness</strong>
                    <span className="text-[0.78rem] text-[#73756e] dark:text-[#94a3b8]">
                      <b className="text-[#17211b] dark:text-[#edf7f4]">{checkedItems.length}</b>
                      {' of '}
                      <b className="text-[#17211b] dark:text-[#edf7f4]">{checklist.documents.length}</b>
                      {' collected'}
                    </span>
                  </div>
                  <div className="w-full h-2 overflow-hidden bg-[#ddd9ce] dark:bg-[#343d35]">
                    <div className="h-full bg-gradient-to-r from-[#0b6847] via-[#23a06f] to-[#dff45f] transition-all duration-[450ms] ease-[cubic-bezier(.2,.8,.2,1)]" style={{ width: `${getProgress()}%` }}></div>
                  </div>
                </div>
              </div>

              {/* DOCUMENT LIST */}
              <div className="flex items-end justify-between mb-4">
                <div>
                  <span className="font-mono text-[0.61rem] font-bold tracking-[0.13em] text-[#99978e] dark:text-[#94a3b8]">CHECK EACH ITEM</span>
                  <h3 className="mt-1.5 text-[1.55rem] tracking-[-0.035em] text-[#17211b] dark:text-[#edf7f4]">Required documents</h3>
                </div>
                <CheckCheck size={26} className="text-[#0b6847] dark:text-[#6ef0ca]" />
              </div>

              <div className="border-t border-[#d9d5c9] dark:border-[#303830]">
                {checklist.documents.map((doc, index) => (
                  <div key={index} className={`border-b border-[#d9d5c9] dark:border-[#303830] transition-colors ${checkedItems.includes(index) ? 'bg-[#edf5e6] dark:bg-[#1b261f]' : ''}`}>
                    <label className="min-h-[94px] p-4 grid grid-cols-[34px_45px_1fr] items-center gap-3.5 cursor-pointer hover:bg-[#f5f8ef] dark:hover:bg-[#1b261f] transition-colors">
                      <div className="relative w-[28px] h-[28px]">
                        <input 
                          type="checkbox" 
                          checked={checkedItems.includes(index)}
                          onChange={() => toggleCheck(index)}
                          className="absolute opacity-0 pointer-events-none"
                        />
                        <div className={`w-[28px] h-[28px] grid place-items-center border-2 transition-all ${checkedItems.includes(index) ? 'border-[#0b6847] bg-[#0b6847] text-white' : 'border-[#9c9e96] bg-white dark:bg-transparent'}`}>
                          <Check size={16} className={`transition-all ${checkedItems.includes(index) ? 'opacity-100 scale-100' : 'opacity-0 scale-30'}`} />
                        </div>
                      </div>
                      <span className="font-mono text-[0.7rem] text-[#a2a197] dark:text-[#94a3b8]">{String(index + 1).padStart(2, '0')}</span>
                      <div>
                        <div className="flex items-center flex-wrap gap-2.5">
                          <span className={`text-base font-bold ${checkedItems.includes(index) ? 'text-[#72786f] dark:text-[#94a3b8] line-through' : 'text-[#17211b] dark:text-[#edf7f4]'}`}>{doc.name}</span>
                          {doc.mandatory ? (
                            <span className="px-2 py-1 font-mono text-[0.56rem] font-bold uppercase tracking-[0.06em] bg-[#ffe1d5] text-[#b13d18]">Required</span>
                          ) : (
                            <span className="px-2 py-1 font-mono text-[0.56rem] font-bold uppercase tracking-[0.06em] bg-[#e7eee9] dark:bg-[#2a3a32] text-[#607268] dark:text-[#94a3b8]">Optional</span>
                          )}
                        </div>
                        {doc.note && (
                          <div className="mt-1.5 flex items-center gap-1.5 text-[0.76rem] text-[#84857d] dark:text-[#94a3b8]">
                            <Info size={13} />
                            <span>{doc.note}</span>
                          </div>
                        )}
                      </div>
                    </label>
                  </div>
                ))}
              </div>

              <div className="mt-9 pt-5 flex gap-3 border-t border-dashed border-[#c6c3b9] dark:border-[#303830] text-[#7e8079] dark:text-[#94a3b8]">
                <Info size={17} className="flex-shrink-0" />
                <p className="text-[0.76rem] leading-relaxed">Requirements may vary depending on your case. Confirm important details with the respective department before submission.</p>
              </div>
            </>
          )}
        </div>
      </section>
    </div>
  )
}