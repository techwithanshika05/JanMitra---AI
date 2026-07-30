import { useState, useEffect, useRef } from 'react'
import { Bot, User, Volume2, Copy, ThumbsUp, ThumbsDown, Download, Trash2, Plus, MessagesSquare, Sparkles, CreditCard, Landmark, Files, MessageSquareWarning, ArrowUpRight, Mic, ArrowUp, ShieldCheck, MessageCircle } from 'lucide-react'
import { useLanguage } from '@/contexts/LanguageContext'
import { useChat } from '@/hooks/useChat'

export default function Chat() {
  const { t } = useLanguage()
  const { 
    messages, 
    sendMessage, 
    clearChat, 
    exportPDF, 
    isTyping,
    sessionId,
    history,
    newChat
  } = useChat()
  
  const [input, setInput] = useState('')
  const [charCount, setCharCount] = useState(0)
  const [isListening, setIsListening] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)
  const recognitionRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!input.trim()) return
    const query = input
    setInput('')
    setCharCount(0)
    await sendMessage(query)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleInputChange = (e) => {
    const value = e.target.value
    setInput(value)
    setCharCount(value.length)
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 140) + 'px'
  }

  const handleVoiceInput = () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      alert('Voice input is not supported in this browser. Please use Chrome or Microsoft Edge.')
      return
    }

    if (isListening && recognitionRef.current) {
      recognitionRef.current.stop()
      return
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    const recognition = new SpeechRecognition()
    recognition.continuous = false
    recognition.interimResults = true
    recognition.maxAlternatives = 1
    recognition.lang = 'en-IN'

    recognition.onstart = () => {
      setIsListening(true)
    }

    recognition.onresult = (event) => {
      let transcript = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript
      }
      setInput(transcript)
      setCharCount(transcript.length)
    }

    recognition.onend = () => {
      setIsListening(false)
      inputRef.current?.focus()
    }

    recognition.onerror = () => {
      setIsListening(false)
    }

    recognitionRef.current = recognition
    recognition.start()
  }

  const speakText = (text) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel()
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.lang = 'en-IN'
      utterance.rate = 0.9
      window.speechSynthesis.speak(utterance)
    }
  }

  const sampleQuestions = [
    'How do I apply for a new ration card in UP?',
    'What documents are needed for PM Kisan?',
    'How to check Ayushman Bharat eligibility?',
    'What is MGNREGA and how to get a job card?',
    'How to apply for old age pension in UP?',
    'How to add a member to my ration card?'
  ]

  const handleSampleClick = (question) => {
    setInput(question)
    setCharCount(question.length)
    setTimeout(() => handleSend(), 100)
  }

  return (
    <div className="chat-redesign w-full h-[calc(100vh-110px)] max-w-5xl mx-auto p-6 flex flex-col pb-[90px]">
      
      {/* Chat Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 py-6 custom-scrollbar">
        {messages.length === 0 ? (
          /* ===== WELCOME STATE — CENTERED ===== */
          <div className="flex flex-col items-center justify-center h-full text-center max-w-2xl mx-auto">
            {/* Icon */}
            <div className="w-20 h-20 rounded-full bg-gradient-to-br from-[#0d7c66] to-[#0a5a4a] flex items-center justify-center mb-6 shadow-lg">
              <Sparkles size={36} className="text-white" />
            </div>
            
            {/* Heading */}
            <h1 className="text-4xl md:text-5xl font-extrabold text-[#101828] dark:text-white tracking-tight">
              JanMitra <span className="text-[#0d7c66]">AI</span>
            </h1>
            
            {/* Tagline */}
            <p className="text-lg text-[#667085] dark:text-[#94a3b8] mt-3">
              Your welfare assistance guide for Uttar Pradesh
            </p>
            
            {/* Divider */}
            <div className="w-16 h-1 bg-[#0d7c66] rounded-full mt-6"></div>
            
            {/* Prompt */}
            <p className="text-xl font-semibold text-[#101828] dark:text-white mt-8">
              What can I help you with today?
            </p>
            
            {/* Sample Questions Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-6 w-full">
              {sampleQuestions.map((q, i) => (
                <button
                  key={i}
                  onClick={() => handleSampleClick(q)}
                  className="group text-left px-5 py-4 rounded-2xl border border-[#e5e7eb] dark:border-[#2c3a37] bg-white dark:bg-[#182230] hover:border-[#0d7c66] hover:shadow-md transition-all duration-200 hover:-translate-y-0.5"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-[10px] font-bold text-[#0d7c66] bg-[#dff5ec] dark:bg-[#1a3a2e] px-2 py-1 rounded-full">
                      {String(i + 1).padStart(2, '0')}
                    </span>
                    <span className="text-sm font-medium text-[#15201b] dark:text-[#edf5f2] group-hover:text-[#0d7c66] transition-colors">
                      {q.length > 50 ? q.slice(0, 50) + '...' : q}
                    </span>
                    <ArrowUpRight size={16} className="text-[#667085] dark:text-[#94a3b8] group-hover:text-[#0d7c66] group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all ml-auto flex-shrink-0" />
                  </div>
                </button>
              ))}
            </div>
          </div>
        ) : (
          /* ===== MESSAGES VIEW ===== */
          <div className="max-w-3xl mx-auto space-y-6">
            {messages.map((msg, index) => (
              <div key={index} className={`flex gap-3.5 ${msg.role === 'user' ? 'justify-end' : ''}`}>
                <div className={`w-9 h-9 flex-shrink-0 grid place-items-center rounded-full ${msg.role === 'user' ? 'order-2 bg-[#ffd35c] text-[#182c28]' : 'bg-[#0d7c66] text-white'}`}>
                  {msg.role === 'user' ? <User size={18} /> : <Bot size={18} />}
                </div>
                <div className={`max-w-[80%] ${msg.role === 'user' ? 'flex flex-col items-end' : ''}`}>
                  <div className={`p-4 rounded-2xl ${msg.role === 'user' ? 'bg-[#0d7c66] text-white rounded-tr-sm' : 'bg-white dark:bg-[#182230] border border-[#e5e7eb] dark:border-[#2c3a37] text-[#344642] dark:text-[#edf5f2] rounded-tl-sm'}`}>
                    <div dangerouslySetInnerHTML={{ __html: msg.content.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>') }} />
                  </div>
                  <div className="flex items-center gap-1 mt-1.5">
                    <span className="text-[10px] text-[#9ba6a4]">{msg.timestamp}</span>
                    {msg.role === 'assistant' && (
                      <>
                        <button onClick={() => speakText(msg.content)} className="w-6 h-6 grid place-items-center rounded-md bg-transparent text-[#899693] hover:bg-[#eaf4f1] hover:text-[#0d7c66] transition-all">
                          <Volume2 size={13} />
                        </button>
                        <div className="flex items-center gap-0.5">
                          <button className="w-6 h-6 grid place-items-center rounded-md bg-transparent text-[#899693] hover:bg-[#eaf4f1] hover:text-[#0d7c66] transition-all">
                            <Copy size={13} />
                          </button>
                          <button className="w-6 h-6 grid place-items-center rounded-md bg-transparent text-[#899693] hover:bg-[#eaf4f1] hover:text-[#0d7c66] transition-all">
                            <ThumbsUp size={13} />
                          </button>
                          <button className="w-6 h-6 grid place-items-center rounded-md bg-transparent text-[#899693] hover:bg-[#eaf4f1] hover:text-[#0d7c66] transition-all">
                            <ThumbsDown size={13} />
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))}
            {isTyping && (
              <div className="flex gap-3.5">
                <div className="w-9 h-9 flex-shrink-0 grid place-items-center rounded-full bg-[#0d7c66] text-white">
                  <Bot size={18} />
                </div>
                <div className="p-4 rounded-2xl bg-white dark:bg-[#182230] border border-[#e5e7eb] dark:border-[#2c3a37]">
                  <div className="flex gap-1.5">
                    <div className="w-2 h-2 rounded-full bg-[#0d7c66] animate-bounce [animation-delay:-0.3s]"></div>
                    <div className="w-2 h-2 rounded-full bg-[#0d7c66] animate-bounce [animation-delay:-0.15s]"></div>
                    <div className="w-2 h-2 rounded-full bg-[#0d7c66] animate-bounce"></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* ===== COMPOSER — BOTTOM ===== */}
      <div className="flex-shrink-0 pt-4 border-t border-[#e5e7eb] dark:border-[#2c3a37]">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-end gap-2 bg-white dark:bg-[#182230] border border-[#e5e7eb] dark:border-[#2c3a37] rounded-2xl p-2 shadow-sm focus-within:border-[#0d7c66] focus-within:shadow-[0_0_0_3px_rgba(13,124,102,0.1)] transition-all">
            <textarea
              ref={inputRef}
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder="Ask JanMitra AI anything..."
              rows="1"
              maxLength="1000"
              className="flex-1 max-h-[120px] p-3 border-0 outline-none resize-none bg-transparent text-[#15201b] dark:text-[#edf5f2] text-sm leading-relaxed placeholder:text-[#9aa5a2] dark:placeholder:text-[#64748b]"
            />
            <div className="flex items-center gap-1 flex-shrink-0">
              <span className="text-[10px] text-[#a2aaa8] font-mono px-1">{charCount}/1000</span>
              <button
                onClick={handleVoiceInput}
                className={`w-10 h-10 flex items-center justify-center rounded-xl transition-all ${isListening ? 'bg-[#ff6840] text-white shadow-[0_0_0_4px_rgba(255,104,64,0.15)]' : 'text-[#667085] hover:bg-[#f0f1eb] dark:hover:bg-[#2c3a37]'}`}
              >
                <Mic size={18} className={isListening ? 'animate-pulse' : ''} />
              </button>
              <button
                onClick={handleSend}
                disabled={!input.trim()}
                className="w-10 h-10 flex items-center justify-center rounded-xl bg-[#0d7c66] text-white disabled:opacity-40 disabled:cursor-not-allowed hover:bg-[#075c4d] transition-all"
              >
                <ArrowUp size={18} />
              </button>
            </div>
          </div>
          
          {/* Bottom Bar — Export + Clear + Disclaimer */}
          <div className="flex items-center justify-between mt-2 px-1">
            <div className="flex items-center gap-3">
              <button onClick={exportPDF} className="text-xs font-medium text-[#667085] dark:text-[#94a3b8] hover:text-[#0d7c66] transition-colors flex items-center gap-1.5">
                <Download size={14} />
                <span>Export</span>
              </button>
              <button onClick={clearChat} className="text-xs font-medium text-[#667085] dark:text-[#94a3b8] hover:text-red-500 transition-colors flex items-center gap-1.5">
                <Trash2 size={14} />
                <span>Clear</span>
              </button>
              <button onClick={newChat} className="text-xs font-medium text-[#667085] dark:text-[#94a3b8] hover:text-[#0d7c66] transition-colors flex items-center gap-1.5">
                <Plus size={14} />
                <span>New Chat</span>
              </button>
            </div>
            <div className="flex items-center gap-1.5 text-[10px] text-[#929e9b] dark:text-[#94a3b8]">
              <ShieldCheck size={13} />
              <span className="hidden sm:inline">AI guidance only. Verify with official sources.</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}