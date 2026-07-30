import { useState, useEffect, useCallback } from 'react'

const SESSION_STORAGE_KEY = 'setuai_session_id'

export function useChat() {
  const [messages, setMessages] = useState([])
  const [history, setHistory] = useState([])
  const [isTyping, setIsTyping] = useState(false)
  const [sessionId, setSessionId] = useState('')

  useEffect(() => {
    const stored = localStorage.getItem(SESSION_STORAGE_KEY)
    if (stored) {
      setSessionId(stored)
      loadSession(stored)
    }
  }, [])

  const loadSession = async (sid) => {
    try {
      const res = await fetch(`/api/chat/history?session_id=${encodeURIComponent(sid)}`)
      const data = await res.json()
      if (data.success && data.messages) {
        const userMessages = data.messages.filter(m => m.role === 'user').map(m => m.content)
        setHistory(userMessages)
        // Restore messages for display
        const formatted = data.messages.map(m => ({
          ...m,
          timestamp: m.timestamp ? new Date(m.timestamp * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }))
        setMessages(formatted)
      }
    } catch (e) {
      console.warn('Could not load session history:', e)
    }
  }

  const sendMessage = async (query) => {
    if (!query.trim()) return

    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    
    // Add user message
    setMessages(prev => [...prev, { role: 'user', content: query, timestamp }])
    setHistory(prev => [...prev, query])
    setIsTyping(true)

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          language: 'en',
          session_id: sessionId
        })
      })

      const data = await res.json()
      setIsTyping(false)

      if (data.success) {
        if (data.session_id) {
          setSessionId(data.session_id)
          localStorage.setItem(SESSION_STORAGE_KEY, data.session_id)
        }
        const botTimestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        setMessages(prev => [...prev, { role: 'assistant', content: data.response, timestamp: botTimestamp }])
      } else {
        setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.', timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }])
      }
    } catch (e) {
      setIsTyping(false)
      setMessages(prev => [...prev, { role: 'assistant', content: 'Network error. Please check your connection and try again.', timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }])
    }
  }

  const clearChat = async () => {
    if (sessionId) {
      try {
        await fetch('/api/chat/clear', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: sessionId })
        })
      } catch (e) { /* silent */ }
    }
    localStorage.removeItem(SESSION_STORAGE_KEY)
    setMessages([])
    setHistory([])
    setSessionId('')
    window.location.reload()
  }

  const exportPDF = async () => {
    if (!messages.length) {
      alert('No messages to export. Start a conversation first.')
      return
    }

    try {
      const res = await fetch('/api/pdf/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages })
      })

      if (!res.ok) throw new Error('PDF generation failed')

      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'setuai_chat.pdf'
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      alert('PDF export failed. Please try again.')
    }
  }

  const newChat = () => {
    if (messages.length > 0 && !confirm('Start a new chat? Current session will be cleared.')) return
    clearChat()
  }

  return {
    messages,
    history,
    isTyping,
    sessionId,
    sendMessage,
    clearChat,
    exportPDF,
    newChat
  }
}