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

  const suggestedQuestions = [
    'How do I apply for a new ration card in UP?',
    'What documents are needed for PM Kisan?',
    'How to check Ayushman Bharat eligibility?',
    'What is MGNREGA and how to get a job card?',
    'How to apply for old age pension in UP?'
  ]

  return (
    <div className="setu-chat w-full h-[calc(100vh-110px)] max-w-none mx-auto p-6 grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-5">
      {/* Left Panel */}
      <div className="p-8 flex flex-col justify-start rounded-[30px] bg-gradient-to-br from-[#102d2a] to-[#173c36] text-white overflow-y-auto">
        <div>
          <div className="flex items-center gap-2.5 mb-5 font-mono text-[10px] font-extrabold tracking-[0.13em] text-[#86e9c9]">
            <span className="w-2 h-2 rounded-full bg-[#65e6bd] shadow-[0_0_0_6px_rgba(101,230,189,0.12)]"></span>
            JANMITRA AI IS ONLINE
          </div>
          <h1 className="text-[clamp(30px,2.4vw,44px)] leading-[1.02] font-extrabold tracking-[-0.055em]">
            Ask.<br />
            Understand.<br />
            <em className="not-italic text-[#ffd35c]">Take action.</em>
          </h1>
          <p className="mt-4 text-sm leading-relaxed text-white/70">Simple guidance for welfare schemes, ration cards, documents and government services in Uttar Pradesh.</p>
        </div>

        {/* Session History - No heading */}
        <div className="mt-8">
          <button onClick={newChat} className="flex items-center gap-1.5 px-3 py-2 rounded-[7px] border border-white/20 bg-white/5 text-white/75 text-[10px] font-bold uppercase hover:border-[#ffd35c] hover:bg-[#ffd35c]/10 hover:text-[#ffd35c] transition-all mb-3">
            <Plus size={14} />
            <span>New chat</span>
          </button>
          <div className="max-h-[190px] overflow-y-auto space-y-1.5 custom-scrollbar">
            {history.length === 0 ? (
              <div className="min-h-[42px] flex items-center gap-2 p-2.5 border border-dashed border-white/15 rounded-[9px] text-white/40 text-xs">
                <MessagesSquare size={14} />
                <span>Your questions will appear here.</span>
              </div>
            ) : (
              history.map((item, index) => (
                <button 
                  key={index}
                  onClick={() => setInput(item)}
                  className="w-full flex items-center gap-2.5 p-2.5 rounded-[9px] bg-white/5 text-white/80 text-xs hover:border-[#ffd35c]/35 hover:bg-[#ffd35c]/10 hover:text-[#ffd35c] hover:translate-x-1 transition-all"
                >
                  <MessageCircle size={13} className="text-[#78e8c4]" />
                  <span className="truncate">{item}</span>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Suggested Topics - No heading */}
        <div className="mt-6">
          <div className="space-y-0">
            {suggestedQuestions.map((q, i) => (
              <button
                key={i}
                onClick={() => setInput(q)}
                className="w-full py-3 px-2 grid grid-cols-[30px_1fr_20px] items-center gap-2 border-t border-white/10 text-white/80 text-[12.5px] font-semibold text-left hover:pl-4 hover:text-[#ffd35c] transition-all"
              >
                <span className="font-mono text-[9px] text-white/35">{String(i + 1).padStart(2, '0')}</span>
                <b className="truncate font-semibold">{q}</b>
                <ArrowUpRight size={15} className="opacity-50" />
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Chat Area */}
      <div className="min-w-0 min-h-0 grid grid-rows-[auto_1fr_auto] border border-[#e1e7e5] dark:border-[#293532] rounded-[30px] bg-[#fbfcfb] dark:bg-[#111918] overflow-hidden">
        {/* Header */}
        <div className="min-h-[82px] p-4 flex items-center justify-between gap-5 border-b border-[#e7ebe9] dark:border-[#2c3a37] bg-white/90 dark:bg-[#182220]">
          <div className="flex items-center gap-3">
            <div className="w-[45px] h-[45px] grid place-items-center rounded-[14px] bg-[#173c36] dark:bg-[#2c3a37] text-[#78e8c4]">
              <Sparkles size={21} />
            </div>
            <div>
              <strong className="text-[15px] text-[#152522] dark:text-[#edf5f2]">JanMitra AI Assistant</strong>
              <span className="block text-[11px] text-[#83918e] dark:text-[#94a3b8]">Citizen welfare assistant</span>
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={exportPDF} className="h-[39px] px-3.5 flex items-center gap-2 border border-[#dce3e0] dark:border-[#32403d] rounded-[11px] bg-white dark:bg-[#1c2725] text-[#455753] dark:text-[#ccd8d5] text-xs font-semibold hover:border-[#173c36] hover:text-[#173c36] transition-all">
              <Download size={15} />
              <span>Export</span>
            </button>
            <button onClick={clearChat} className="h-[39px] px-3.5 flex items-center gap-2 border border-[#dce3e0] dark:border-[#32403d] rounded-[11px] bg-white dark:bg-[#1c2725] text-[#455753] dark:text-[#ccd8d5] text-xs font-semibold hover:border-red-500 hover:text-red-500 transition-all">
              <Trash2 size={15} />
              <span>Clear</span>
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="min-h-0 overflow-y-auto p-8 bg-[linear-gradient(rgba(20,60,54,0.025)_1px,transparent_1px),linear-gradient(90deg,rgba(20,60,54,0.025)_1px,transparent_1px)] bg-[length:32px_32px] dark:bg-[#111918] custom-scrollbar">
          {messages.length === 0 ? (
            <div className="flex gap-3.5 mb-7 max-w-full">
              <div className="w-[38px] h-[38px] flex-shrink-0 grid place-items-center rounded-[12px] bg-[#173c36] text-[#77e5c2]">
                <Bot size={18} />
              </div>
              <div className="flex-1 min-w-0 max-w-full">
                <div className="text-[9px] font-extrabold tracking-[0.13em] text-[#1a8c76] mb-2">JANMITRA AI</div>
                <div className="p-5 rounded-[4px_20px_20px_20px] border border-[#e0e7e4] dark:border-[#2c3a37] bg-white dark:bg-[#182220] shadow-sm text-[#344642] dark:text-[#edf5f2] text-sm leading-relaxed w-full">
                  <p className="mt-0">Hello! I'm JanMitra AI, your welfare assistance guide for Uttar Pradesh. Tell me what you're trying to do and I'll help you understand the next steps.</p>
                  <div className="my-4 grid grid-cols-2 gap-2">
                    <div className="p-3 flex items-center gap-2.5 rounded-[11px] bg-[#f2f7f5] dark:bg-[#202d2a] text-[12px] font-semibold text-[#38514c] dark:text-[#d5e0dd]">
                      <CreditCard size={15} className="text-[#118b77]" />
                      <span>Ration Cards</span>
                    </div>
                    <div className="p-3 flex items-center gap-2.5 rounded-[11px] bg-[#f2f7f5] dark:bg-[#202d2a] text-[12px] font-semibold text-[#38514c] dark:text-[#d5e0dd]">
                      <Landmark size={15} className="text-[#118b77]" />
                      <span>Welfare Schemes</span>
                    </div>
                    <div className="p-3 flex items-center gap-2.5 rounded-[11px] bg-[#f2f7f5] dark:bg-[#202d2a] text-[12px] font-semibold text-[#38514c] dark:text-[#d5e0dd]">
                      <Files size={15} className="text-[#118b77]" />
                      <span>Documents</span>
                    </div>
                    <div className="p-3 flex items-center gap-2.5 rounded-[11px] bg-[#f2f7f5] dark:bg-[#202d2a] text-[12px] font-semibold text-[#38514c] dark:text-[#d5e0dd]">
                      <MessageSquareWarning size={15} className="text-[#118b77]" />
                      <span>Grievances</span>
                    </div>
                  </div>
                  <p className="font-semibold text-[#173c36] dark:text-[#73e3bf]">What can I help you with today?</p>
                </div>
                <div className="flex items-center gap-2 mt-2">
                  <span className="text-[10px] text-[#9ba6a4]">{new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  <button onClick={() => speakText('Hello! I\'m JanMitra AI, your welfare assistance guide for Uttar Pradesh. Tell me what you\'re trying to do and I\'ll help you understand the next steps.')} className="w-[27px] h-[27px] grid place-items-center rounded-[8px] bg-transparent text-[#899693] hover:bg-[#eaf4f1] hover:text-[#118b77] transition-all">
                    <Volume2 size={14} />
                  </button>
                </div>
              </div>
            </div>
          ) : (
            messages.map((msg, index) => (
              <div key={index} className={`flex gap-3.5 mb-7 ${msg.role === 'user' ? 'justify-end' : ''} max-w-full`}>
                <div className={`w-[38px] h-[38px] flex-shrink-0 grid place-items-center rounded-[12px] ${msg.role === 'user' ? 'order-2 bg-[#ffd35c] text-[#182c28]' : 'bg-[#173c36] text-[#77e5c2]'}`}>
                  {msg.role === 'user' ? <User size={18} /> : <Bot size={18} />}
                </div>
                <div className={`flex-1 min-w-0 max-w-full ${msg.role === 'user' ? 'flex flex-col items-end' : ''}`}>
                  <div className={`p-5 w-full ${msg.role === 'user' ? 'rounded-[20px_4px_20px_20px] bg-[#173c36] text-white' : 'rounded-[4px_20px_20px_20px] border border-[#e0e7e4] dark:border-[#2c3a37] bg-white dark:bg-[#182220] text-[#344642] dark:text-[#edf5f2]'} text-sm leading-relaxed`}>
                    <div dangerouslySetInnerHTML={{ __html: msg.content.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>') }} />
                  </div>
                  <div className="flex items-center gap-1 mt-2">
                    <span className="text-[10px] text-[#9ba6a4]">{msg.timestamp}</span>
                    {msg.role === 'assistant' && (
                      <>
                        <button onClick={() => speakText(msg.content)} className="w-[27px] h-[27px] grid place-items-center rounded-[8px] bg-transparent text-[#899693] hover:bg-[#eaf4f1] hover:text-[#118b77] transition-all">
                          <Volume2 size={14} />
                        </button>
                        <div className="flex items-center gap-0.5">
                          <button className="w-[27px] h-[27px] grid place-items-center rounded-[8px] bg-transparent text-[#899693] hover:bg-[#eaf4f1] hover:text-[#173c36] transition-all">
                            <Copy size={15} />
                          </button>
                          <button className="w-[27px] h-[27px] grid place-items-center rounded-[8px] bg-transparent text-[#899693] hover:bg-[#eaf4f1] hover:text-[#173c36] transition-all">
                            <ThumbsUp size={15} />
                          </button>
                          <button className="w-[27px] h-[27px] grid place-items-center rounded-[8px] bg-transparent text-[#899693] hover:bg-[#eaf4f1] hover:text-[#173c36] transition-all">
                            <ThumbsDown size={15} />
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
          {isTyping && (
            <div className="flex gap-3.5 mb-7 max-w-full">
              <div className="w-[38px] h-[38px] flex-shrink-0 grid place-items-center rounded-[12px] bg-[#173c36] text-[#77e5c2]">
                <Bot size={18} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="p-5 rounded-[4px_20px_20px_20px] border border-[#e0e7e4] dark:border-[#2c3a37] bg-white dark:bg-[#182220] w-full">
                  <div className="flex gap-1.5">
                    <div className="w-2 h-2 rounded-full bg-[#118b77] animate-bounce [animation-delay:-0.3s]"></div>
                    <div className="w-2 h-2 rounded-full bg-[#118b77] animate-bounce [animation-delay:-0.15s]"></div>
                    <div className="w-2 h-2 rounded-full bg-[#118b77] animate-bounce"></div>
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Composer */}
        <div className="p-4 pb-5 bg-gradient-to-t from-[#fbfcfb] to-transparent dark:from-[#111918]">
          <div className="p-3 px-[18px] border border-[#d7dfdc] dark:border-[#2c3a37] rounded-[20px] bg-white dark:bg-[#182220] shadow-[0_16px_45px_rgba(17,48,42,0.09)] focus-within:border-[#168b76] focus-within:shadow-[0_0_0_4px_rgba(22,139,118,0.08),0_18px_50px_rgba(17,48,42,0.1)] transition-all">
            <textarea
              ref={inputRef}
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder="Ask JanMitra AI anything..."
              rows="1"
              maxLength="1000"
              className="w-full max-h-[150px] p-1 pb-3 border-0 outline-none resize-none bg-transparent text-[#233632] dark:text-[#edf5f2] text-sm leading-relaxed placeholder:text-[#9aa5a2] dark:placeholder:text-[#64748b]"
            />
            <div className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-1.5 text-[#929e9b] text-[10px]">
                <ShieldCheck size={13} />
                <span className="hidden sm:inline">AI guidance only. Verify important information with official sources.</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="font-mono text-[9px] text-[#a2aaa8]">{charCount}/1000</span>
                <button
                  onClick={handleVoiceInput}
                  className={`w-11 h-11 flex items-center justify-center flex-shrink-0 border rounded-[13px] transition-all ${isListening ? 'bg-[#ff6840] text-white border-[#ff6840] shadow-[0_0_0_5px_rgba(255,104,64,0.12)] animate-mic-pulse' : 'border-[#dce5e1] bg-[#f4f8f6] text-[#315149] hover:bg-[#e8f5f0] hover:text-[#0f6b56] hover:border-[#b9ddd2]'}`}
                >
                  <Mic size={18} className={isListening ? 'animate-mic-scale' : ''} />
                </button>
                <button
                  onClick={handleSend}
                  disabled={!input.trim()}
                  className="w-[39px] h-[39px] grid place-items-center rounded-[12px] bg-[#173c36] dark:bg-[#2c3a37] text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[#0d725f] hover:-translate-y-0.5 transition-all"
                >
                  <ArrowUp size={18} />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}