import { useState, useEffect, useRef } from 'react'
import { Bot, User, Volume2, Copy, ThumbsUp, ThumbsDown, Download, Trash2, Plus, MessagesSquare, Sparkles, CreditCard, Landmark, Files, MessageSquareWarning, ArrowUpRight, Mic, ArrowUp, ShieldCheck, MessageCircle, Pencil, X, RotateCcw } from 'lucide-react'
import { useLanguage } from '@/contexts/LanguageContext'
import { useChat } from '@/hooks/useChat'
import { api } from '@/utils/api'
import ChatResponse from '@/components/ChatResponse'

export default function Chat() {
  const { language, t } = useLanguage()
  const { 
    messages, 
    sendMessage, 
    clearChat, 
    exportPDF, 
    isTyping,
    sessionId,
    sessions,
    history,
    newChat,
    loadSession,
    renameSession,
    removeSession
  } = useChat()
  
  const [input, setInput] = useState('')
  const [charCount, setCharCount] = useState(0)
  const [isListening, setIsListening] = useState(false)
  const [showSessions, setShowSessions] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)
  const recognitionRef = useRef(null)
  const sendingRef = useRef(false)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async (requestedText) => {
    const query = typeof requestedText === 'string' ? requestedText : input
    if (!query.trim() || sendingRef.current || isTyping) return
    sendingRef.current = true
    setInput('')
    setCharCount(0)
    try {
      await sendMessage(query)
    } finally {
      sendingRef.current = false
    }
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
      alert(t('voice_input_unsupported'))
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
    recognition.lang = language === 'hi' ? 'hi-IN' : 'en-IN'

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
      utterance.lang = language === 'hi' ? 'hi-IN' : 'en-IN'
      utterance.rate = 0.9
      window.speechSynthesis.speak(utterance)
    }
  }

  const sampleQuestions = [
    t('chat_sample_1'),
    t('chat_sample_2'),
    t('chat_sample_3'),
    t('chat_sample_4'),
    t('chat_sample_5'),
    t('chat_sample_6')
  ]

  const handleSampleClick = (question) => {
    handleSend(question)
  }

  return (
    <div className="chat-redesign w-full h-[calc(100vh-110px)] max-w-5xl mx-auto p-6 flex flex-col pb-[90px]">
      <div className="flex-shrink-0 mb-3 flex items-center justify-between gap-3">
        <button onClick={() => setShowSessions(!showSessions)} className="h-10 px-4 inline-flex items-center gap-2 rounded-xl border border-[#e5e7eb] dark:border-[#2c3a37] bg-white dark:bg-[#182230] text-sm font-bold">
          <MessagesSquare size={17} /> {t('conversations')} ({sessions.length})
        </button>
        <button onClick={newChat} className="h-10 px-4 inline-flex items-center gap-2 rounded-xl bg-[#0d7c66] text-white text-sm font-bold"><Plus size={17} /> {t('new_chat')}</button>
      </div>
      {showSessions && (
        <section className="flex-shrink-0 mb-3 max-h-48 overflow-y-auto rounded-2xl border border-[#e5e7eb] dark:border-[#2c3a37] bg-white dark:bg-[#182230]">
          {sessions.map(item => (
            <div key={item.id} className={`p-3 flex items-center gap-3 border-b border-[#eef0ed] ${sessionId === item.id ? 'bg-[#eef8f5] dark:bg-[#15332b]' : ''}`}>
              <button onClick={() => { loadSession(item.id); setShowSessions(false) }} className="flex-1 min-w-0 text-left">
                <strong className="block truncate text-sm">{item.title || t('untitled_conversation')}</strong>
                <span className="text-xs text-[#667085]">{new Date(item.last_message_at).toLocaleString()}</span>
              </button>
              <button title={t('rename')} aria-label={t('rename')} onClick={async () => { const title = prompt(t('conversation_title'), item.title || ''); if (title?.trim()) await renameSession(item.id, title.trim()) }} className="w-8 h-8 grid place-items-center rounded-lg hover:bg-[#edf5e6]"><Pencil size={14} /></button>
              <button title={t('delete')} aria-label={t('delete')} onClick={async () => { if (confirm(t('delete_conversation_confirm'))) await removeSession(item.id) }} className="w-8 h-8 grid place-items-center rounded-lg text-red-600 hover:bg-red-50"><X size={15} /></button>
            </div>
          ))}
          {sessions.length === 0 && <p className="p-4 text-sm text-[#667085]">{t('no_saved_conversations')}</p>}
        </section>
      )}
      
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
              {t('chat_guide_tagline')}
            </p>
            
            {/* Divider */}
            <div className="w-16 h-1 bg-[#0d7c66] rounded-full mt-6"></div>
            
            {/* Prompt */}
            <p className="text-xl font-semibold text-[#101828] dark:text-white mt-8">
              {t('what_help_today')}
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
                    {msg.role === 'assistant'
                      ? <ChatResponse content={msg.content} />
                      : <p className="whitespace-pre-wrap break-words leading-7">{msg.content}</p>}
                  </div>
                  <div className="flex items-center gap-1 mt-1.5">
                    <span className="text-[10px] text-[#9ba6a4]">{msg.timestamp}</span>
                    {msg.role === 'assistant' && (
                      <>
                        <button onClick={() => speakText(msg.content)} className="w-6 h-6 grid place-items-center rounded-md bg-transparent text-[#899693] hover:bg-[#eaf4f1] hover:text-[#0d7c66] transition-all">
                          <Volume2 size={13} />
                        </button>
                        <div className="flex items-center gap-0.5">
                          <button title={t('copy')} aria-label={t('copy')} onClick={() => navigator.clipboard.writeText(msg.content)} className="w-6 h-6 grid place-items-center rounded-md bg-transparent text-[#899693] hover:bg-[#eaf4f1] hover:text-[#0d7c66] transition-all">
                            <Copy size={13} />
                          </button>
                          <button onClick={() => msg.id && api.saveChatFeedback(msg.id, { reaction: 'like', rating: 5, feedback_text: 'Helpful response' }).catch(error => alert(error.message))} className="w-6 h-6 grid place-items-center rounded-md bg-transparent text-[#899693] hover:bg-[#eaf4f1] hover:text-[#0d7c66] transition-all">
                            <ThumbsUp size={13} />
                          </button>
                          <button onClick={() => msg.id && api.saveChatFeedback(msg.id, { reaction: 'dislike', rating: 1, feedback_text: 'Unhelpful response' }).catch(error => alert(error.message))} className="w-6 h-6 grid place-items-center rounded-md bg-transparent text-[#899693] hover:bg-[#eaf4f1] hover:text-[#0d7c66] transition-all">
                            <ThumbsDown size={13} />
                          </button>
                          <button title={t('remove_feedback')} aria-label={t('remove_feedback')} onClick={() => msg.id && api.deleteChatFeedback(msg.id).catch(error => error.status !== 404 && alert(error.message))} className="w-6 h-6 grid place-items-center rounded-md bg-transparent text-[#899693] hover:bg-[#eaf4f1] hover:text-[#0d7c66] transition-all">
                            <RotateCcw size={12} />
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                  {msg.role === 'assistant' && msg.sources?.length > 0 && (
                    <details className="mt-2 max-w-[90%] text-[11px] text-[#667085]">
                      <summary className="cursor-pointer font-bold text-[#0d7c66]">{t('verified_sources')} ({msg.sources.length})</summary>
                      <ul className="mt-2 space-y-1">
                        {msg.sources.map((source, sourceIndex) => (
                          <li key={`${source.title}-${sourceIndex}`}>{source.title}</li>
                        ))}
                      </ul>
                    </details>
                  )}
                  {msg.role === 'assistant' && msg.alert && (
                    <div className={`mt-2 max-w-[90%] px-3 py-2 rounded-lg text-[11px] font-semibold ${
                      msg.apiStatus === 'working'
                        ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300'
                        : 'bg-amber-50 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300'
                    }`}>
                      {msg.apiStatus === 'working' ? `${t('live_knowledge_answer')}: ` : `${t('verified_faq_fallback')}: `}
                      {msg.alert}
                    </div>
                  )}
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
              placeholder={t('ask_anything')}
              rows="1"
              maxLength="1000"
              className="flex-1 max-h-[120px] p-3 border-0 outline-none resize-none bg-transparent text-[#15201b] dark:text-[#edf5f2] text-sm leading-relaxed placeholder:text-[#9aa5a2] dark:placeholder:text-[#64748b]"
            />
            <div className="flex items-center gap-1 flex-shrink-0">
              <span className="text-[10px] text-[#a2aaa8] font-mono px-1">{charCount}/1000</span>
              <button
                onClick={handleVoiceInput}
                title={isListening ? t('listening') : t('start_speaking')}
                aria-label={isListening ? t('listening') : t('start_speaking')}
                className={`w-10 h-10 flex items-center justify-center rounded-xl transition-all ${isListening ? 'bg-[#ff6840] text-white shadow-[0_0_0_4px_rgba(255,104,64,0.15)]' : 'text-[#667085] hover:bg-[#f0f1eb] dark:hover:bg-[#2c3a37]'}`}
              >
                <Mic size={18} className={isListening ? 'animate-pulse' : ''} />
              </button>
              <button
                onClick={handleSend}
                title={t('send')}
                aria-label={t('send')}
                disabled={!input.trim() || isTyping}
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
                <span>{t('export')}</span>
              </button>
              <button onClick={clearChat} className="text-xs font-medium text-[#667085] dark:text-[#94a3b8] hover:text-red-500 transition-colors flex items-center gap-1.5">
                <Trash2 size={14} />
                <span>{t('clear')}</span>
              </button>
              <button onClick={newChat} className="text-xs font-medium text-[#667085] dark:text-[#94a3b8] hover:text-[#0d7c66] transition-colors flex items-center gap-1.5">
                <Plus size={14} />
                <span>{t('new_chat')}</span>
              </button>
            </div>
            <div className="flex items-center gap-1.5 text-[10px] text-[#929e9b] dark:text-[#94a3b8]">
              <ShieldCheck size={13} />
              <span className="hidden sm:inline">{t('ai_guidance')}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
