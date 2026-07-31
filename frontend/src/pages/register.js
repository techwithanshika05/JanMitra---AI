import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/router'
import { UserPlus, ShieldCheck } from 'lucide-react'
import { api } from '@/utils/api'
import { useAuth } from '@/contexts/AuthContext'
import { useLanguage } from '@/contexts/LanguageContext'

export default function Register() {
  const router = useRouter()
  const { completeAuth } = useAuth()
  const { t } = useLanguage()
  const [form, setForm] = useState({
    name: '', mobile: '', email: '', password: '', state: 'Uttar Pradesh',
    pincode: '', preferred_language: 'en', confirm_password: ''
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async event => {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      const mobile = form.mobile.replace(/\D/g, '')
      if (mobile.length !== 10) throw new Error('Enter a valid 10-digit mobile number.')
      if (form.pincode && !/^\d{6}$/.test(form.pincode)) throw new Error('PIN code must contain exactly 6 digits.')
      if (form.password.length < 8) throw new Error('Password must contain at least 8 characters.')
      if (form.password !== form.confirm_password) throw new Error('Passwords do not match.')
      const registration = { ...form }
      delete registration.confirm_password
      const data = await api.register({
        ...registration,
        mobile,
        email: form.email.trim().toLowerCase() || null,
        pincode: form.pincode || null
      })
      completeAuth(data, t('registration_success', { name: data.user.name }))
      await router.push('/profile')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="max-w-3xl mx-auto px-5 py-16">
      <section className="p-8 sm:p-12 rounded-[34px] bg-white dark:bg-[#17201f] border border-[#e4e8ed] dark:border-[#293533] shadow-xl">
        <span className="w-14 h-14 grid place-items-center rounded-2xl bg-[#dff5ec] text-[#0d7c66]"><UserPlus /></span>
        <h1 className="mt-6 text-4xl sm:text-5xl font-extrabold tracking-[-0.05em]">{t('create_account_title')}</h1>
        <p className="mt-3 text-[#667085]">{t('create_account_subtitle')}</p>
        <form onSubmit={submit} className="grid sm:grid-cols-2 gap-5 mt-9">
          {[
            ['name', 'full_name', 'text'],
            ['mobile', 'mobile_10', 'tel'],
            ['email', 'email_optional', 'email'],
            ['pincode', 'pincode_optional', 'text'],
            ['state', 'state', 'text'],
            ['password', 'password', 'password'],
            ['confirm_password', 'confirm_password', 'password']
          ].map(([key, labelKey, type]) => (
            <label key={key} className="block">
              <span className="block mb-2 text-sm font-bold">{t(labelKey)}</span>
              <input
                type={type}
                value={form[key]}
                required={['name', 'mobile', 'password', 'confirm_password'].includes(key)}
                minLength={['password', 'confirm_password'].includes(key) ? 8 : undefined}
                maxLength={key === 'mobile' ? 10 : key === 'pincode' ? 6 : undefined}
                onChange={event => setForm({ ...form, [key]: event.target.value })}
                className="w-full h-12 px-4 rounded-xl border border-[#d0d5dd] bg-transparent outline-none focus:border-[#0d7c66]"
              />
            </label>
          ))}
          <label className="block sm:col-span-2">
            <span className="block mb-2 text-sm font-bold">{t('preferred_language')}</span>
            <select value={form.preferred_language} onChange={event => setForm({ ...form, preferred_language: event.target.value })} className="w-full h-12 px-4 rounded-xl border border-[#d0d5dd] bg-transparent">
              <option value="en">English</option>
              <option value="hi">Hindi</option>
              <option value="hinglish">Hinglish</option>
            </select>
          </label>
          {error && <p className="sm:col-span-2 text-sm text-red-600">{error}</p>}
          <button disabled={loading} className="sm:col-span-2 h-12 rounded-xl bg-[#101828] text-white font-extrabold disabled:opacity-60">
            {loading ? t('creating_account') : t('create_account')}
          </button>
        </form>
        <p className="mt-5 text-sm text-[#667085]">{t('already_registered')} <Link href="/login" className="font-bold text-[#0d7c66]">{t('sign_in')}</Link></p>
        <div className="mt-6 flex gap-3 p-4 rounded-xl bg-[#f4f7f6] dark:bg-[#101817] text-sm text-[#667085]"><ShieldCheck size={18} />{t('password_security')}</div>
      </section>
    </main>
  )
}
