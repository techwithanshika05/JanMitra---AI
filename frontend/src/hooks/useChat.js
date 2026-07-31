import { useState, useEffect } from 'react'
import { api } from '@/utils/api'

const SESSION_STORAGE_KEY = 'janmitra_session_id'
const displayTime = value => value
  ? new Date(value).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  : new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

export function useChat() {
  const [messages, setMessages] = useState([])
  const [history, setHistory] = useState([])
  const [isTyping, setIsTyping] = useState(false)
  const [feedbackPending, setFeedbackPending] = useState({})
  const [sessionId, setSessionId] = useState('')
  const [sessions, setSessions] = useState([])

  useEffect(() => {
    refreshSessions()
    const stored = localStorage.getItem(SESSION_STORAGE_KEY)
    if (stored) {
      setSessionId(stored)
      loadSession(stored)
    }
  }, [])

  const refreshSessions = async () => {
    try { setSessions(await api.chatSessions()) }
    catch (error) { setSessions([]) }
  }

  const normalizeMessage = message => ({
    id: message.id,
    role: message.role,
    content: message.content,
    timestamp: displayTime(message.created_at),
    confidence: message.confidence,
    sources: message.sources,
    disclaimer: message.disclaimer,
    structuredContent: message.structured_content,
    visualEvidence: (
      message.visual_evidence
      || message.structured_content?.visual_evidence
      || []
    ).slice(0, 1),
    feedback: message.feedback || null
  })

  const loadFeedback = async message => {
    if (message.role !== 'assistant' || !message.id) return message
    try {
      return { ...message, feedback: await api.chatFeedback(message.id) }
    } catch (error) {
      if (error.status !== 404) console.warn('Could not load chat feedback', error)
      return message
    }
  }

  const loadSession = async id => {
    try {
      const session = await api.chatSession(id)
      const normalized = (session.messages || []).map(normalizeMessage)
      const withFeedback = await Promise.all(normalized.map(loadFeedback))
      setMessages(withFeedback)
      setHistory(normalized.filter(message => message.role === 'user').map(message => message.content))
      setSessionId(id)
      localStorage.setItem(SESSION_STORAGE_KEY, id)
    } catch (error) {
      localStorage.removeItem(SESSION_STORAGE_KEY)
      setSessionId('')
    }
  }

  const sendMessage = async query => {
    if (!query.trim()) return
    const timestamp = displayTime()
    setMessages(previous => [...previous, { role: 'user', content: query, timestamp }])
    setHistory(previous => [...previous, query])
    setIsTyping(true)

    let activeId = sessionId
    try {
      if (!activeId) {
        const session = await api.createChatSession(query.slice(0, 80))
        activeId = session.id
        setSessionId(activeId)
        localStorage.setItem(SESSION_STORAGE_KEY, activeId)
        await refreshSessions()
      }
      const response = await api.sendChatMessage(activeId, {
        message: query,
        language: 'en',
        client_message_id: crypto.randomUUID()
      })
      setMessages(previous => [...previous, {
        ...normalizeMessage(response.assistant_message),
        confidence: response.confidence,
        sources: response.sources,
        disclaimer: response.disclaimer,
        apiStatus: response.api_status,
        alert: response.alert
      }])
      await refreshSessions()
    } catch (error) {
      let recovered = false
      if (activeId) {
        try {
          const session = await api.chatSession(activeId)
          const lastMessage = session.messages?.[session.messages.length - 1]
          if (lastMessage?.role === 'assistant') {
            const normalized = normalizeMessage(lastMessage)
            setMessages(previous => previous.some(message => message.id === normalized.id) ? previous : [...previous, normalized])
            recovered = true
          }
        } catch (recoveryError) {
          if (recoveryError.status === 404) {
            localStorage.removeItem(SESSION_STORAGE_KEY)
            setSessionId('')
          }
        }
      }
      if (!recovered) {
        setMessages(previous => [...previous, {
          role: 'assistant',
          content: error.status === 404
            ? 'This saved chat session expired. A new session will be created with your next message.'
            : error.message || 'The assistant is temporarily unavailable.',
          timestamp: displayTime()
        }])
      }
    } finally {
      setIsTyping(false)
    }
  }

  const clearChat = async () => {
    if (sessionId) {
      try { await api.deleteChatSession(sessionId) } catch (error) { /* clear local state */ }
    }
    localStorage.removeItem(SESSION_STORAGE_KEY)
    setMessages([])
    setHistory([])
    setSessionId('')
    await refreshSessions()
  }

  const exportPDF = () => {
    if (!messages.length) return alert('No messages to export. Start a conversation first.')
    window.print()
  }

  const newChat = () => {
    if (messages.length > 0 && !confirm('Start a new chat? Current session will be cleared.')) return
    clearChat()
  }

  const renameSession = async (id, title) => {
    await api.renameChatSession(id, title)
    await refreshSessions()
  }

  const removeSession = async id => {
    await api.deleteChatSession(id)
    if (id === sessionId) {
      localStorage.removeItem(SESSION_STORAGE_KEY)
      setMessages([])
      setHistory([])
      setSessionId('')
    }
    await refreshSessions()
  }

  const saveMessageFeedback = async (messageId, reaction) => {
    if (!messageId || feedbackPending[messageId]) return
    setFeedbackPending(previous => ({ ...previous, [messageId]: true }))
    try {
      const feedback = await api.saveChatFeedback(messageId, {
        reaction,
        rating: reaction === 'like' ? 5 : 1,
        feedback_text: reaction === 'like' ? 'Helpful response' : 'Unhelpful response'
      })
      setMessages(previous => previous.map(message => (
        message.id === messageId ? { ...message, feedback } : message
      )))
      return feedback
    } finally {
      setFeedbackPending(previous => ({ ...previous, [messageId]: false }))
    }
  }

  const removeMessageFeedback = async messageId => {
    if (!messageId || feedbackPending[messageId]) return
    setFeedbackPending(previous => ({ ...previous, [messageId]: true }))
    try {
      await api.deleteChatFeedback(messageId)
      setMessages(previous => previous.map(message => (
        message.id === messageId ? { ...message, feedback: null } : message
      )))
    } catch (error) {
      if (error.status !== 404) throw error
      setMessages(previous => previous.map(message => (
        message.id === messageId ? { ...message, feedback: null } : message
      )))
    } finally {
      setFeedbackPending(previous => ({ ...previous, [messageId]: false }))
    }
  }

  return {
    messages, history, isTyping, sessionId, sessions, sendMessage, clearChat,
    exportPDF, newChat, loadSession, renameSession, removeSession, refreshSessions,
    feedbackPending, saveMessageFeedback, removeMessageFeedback
  }
}
