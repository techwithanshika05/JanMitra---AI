import { useState } from 'react'
import { useRouter } from 'next/router'
import { LogIn, ShieldCheck } from 'lucide-react'
import Link from 'next/link'
import { api } from '@/utils/api'
import { useAuth } from '@/contexts/AuthContext'
import { useLanguage } from '@/contexts/LanguageContext'

export default function Login() {
  const router = useRouter()
  const { completeAuth } = useAuth()
  const { t } = useLanguage()
  const [identifier, setIdentifier] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async (event) => {
    event.preventDefault()
    setError('')
    setLoading(true)
    try {
      const identity = identifier.includes('@')
        ? { email: identifier.trim().toLowerCase() }
        : { mobile: identifier.replace(/\D/g, '') }
      if (identity.mobile && identity.mobile.length !== 10) {
        throw new Error('Enter a valid 10-digit mobile number.')
      }
      const data = await api.login({ ...identity, password })
      completeAuth(data, t('login_success', { name: data.user.name }))
      await router.push(data.user?.role === 'admin' ? '/admin' : '/profile')
    } catch (err) {
      setError(err.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="max-w-lg mx-auto px-5 py-20">
      <section className="p-8 sm:p-10 rounded-[30px] border border-[#dde2dc] bg-white dark:bg-[#14231c] shadow-[0_24px_70px_rgba(16,24,40,0.10)]">
        <span className="w-14 h-14 grid place-items-center rounded-2xl bg-[#dff5ec] text-[#0d7c66]">
          <ShieldCheck size={26} />
        </span>
        <h1 className="mt-6 text-4xl font-extrabold tracking-[-0.04em]">{t('welcome_back')}</h1>
        <p className="mt-2 text-[#667085] dark:text-[#94a3b8]">{t('login_subtitle')}</p>

        <form onSubmit={submit} className="mt-8 space-y-5">
          <label className="block">
            <span className="block mb-2 text-sm font-bold">{t('email_or_mobile')}</span>
            <input
              value={identifier}
              onChange={(event) => setIdentifier(event.target.value)}
              required
              className="w-full h-12 px-4 rounded-xl border border-[#d0d5dd] bg-transparent outline-none focus:border-[#0d7c66]"
            />
          </label>
          <label className="block">
            <span className="block mb-2 text-sm font-bold">{t('password')}</span>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
              className="w-full h-12 px-4 rounded-xl border border-[#d0d5dd] bg-transparent outline-none focus:border-[#0d7c66]"
            />
          </label>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full h-12 flex items-center justify-center gap-2 rounded-xl bg-[#101828] text-white font-extrabold disabled:opacity-60"
          >
            <LogIn size={18} />
            {loading ? t('signing_in') : t('sign_in')}
          </button>
        </form>
        <p className="mt-5 text-sm text-[#667085]">{t('new_to_janmitra')} <Link href="/register" className="font-bold text-[#0d7c66]">{t('create_account')}</Link></p>
      </section>
    </main>
  )
}
