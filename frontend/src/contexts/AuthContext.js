import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { CheckCircle2, X } from 'lucide-react'
import { api, getToken, setToken } from '@/utils/api'
import { useLanguage } from '@/contexts/LanguageContext'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const { t } = useLanguage()
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [notice, setNotice] = useState('')

  const refreshUser = useCallback(async () => {
    if (!getToken()) {
      setUser(null)
      setLoading(false)
      return null
    }
    try {
      const currentUser = await api.me()
      setUser(currentUser)
      return currentUser
    } catch (error) {
      if (error.status === 401) setToken(null)
      setUser(null)
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refreshUser()
    const handleAuthChange = () => refreshUser()
    const handleStorage = event => {
      if (!event.key || event.key === 'janmitra_token') refreshUser()
    }
    window.addEventListener('janmitra-auth-changed', handleAuthChange)
    window.addEventListener('storage', handleStorage)
    return () => {
      window.removeEventListener('janmitra-auth-changed', handleAuthChange)
      window.removeEventListener('storage', handleStorage)
    }
  }, [refreshUser])

  useEffect(() => {
    if (!notice) return undefined
    const timer = window.setTimeout(() => setNotice(''), 5000)
    return () => window.clearTimeout(timer)
  }, [notice])

  const completeAuth = useCallback((data, message) => {
    setToken(data.access_token)
    setUser(data.user)
    setLoading(false)
    setNotice(message)
  }, [])

  const logout = useCallback(() => {
    setToken(null)
    setUser(null)
    setNotice(t('logged_out'))
  }, [t])

  const value = useMemo(() => ({
    user,
    loading,
    authenticated: Boolean(user),
    completeAuth,
    logout,
    refreshUser,
    showNotice: setNotice
  }), [user, loading, completeAuth, logout, refreshUser])

  return (
    <AuthContext.Provider value={value}>
      {children}
      {notice && (
        <div
          role="status"
          className="fixed z-[6000] top-24 right-4 sm:right-7 max-w-sm px-5 py-4 flex items-center gap-3 rounded-2xl bg-[#10271f] text-white shadow-[0_18px_55px_rgba(16,39,31,.30)]"
        >
          <CheckCircle2 size={21} className="text-[#6ef0ca] flex-shrink-0" />
          <span className="text-sm font-bold">{notice}</span>
          <button onClick={() => setNotice('')} className="ml-2 text-white/60 hover:text-white" aria-label="Close notification">
            <X size={17} />
          </button>
        </div>
      )}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside AuthProvider')
  return context
}
