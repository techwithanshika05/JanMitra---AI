import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState
} from 'react'
import { dictionary } from '@/i18n/dictionary'

export const LanguageContext = createContext(null)

const SUPPORTED_LANGUAGES = ['en', 'hi', 'hinglish']

const interpolate = (value, variables = {}) =>
  String(value).replace(/\{\{(\w+)\}\}/g, (_, key) =>
    variables[key] === undefined ? `{{${key}}}` : String(variables[key])
  )

export function useLanguage() {
  const context = useContext(LanguageContext)
  if (!context) throw new Error('useLanguage must be used within a LanguageProvider')
  return context
}

export function LanguageProvider({ children }) {
  const [language, setLanguage] = useState('en')

  useEffect(() => {
    const saved = localStorage.getItem('janmitra_lang')
    if (SUPPORTED_LANGUAGES.includes(saved)) setLanguage(saved)
  }, [])

  const t = useCallback((key, variables) => {
    const translated = dictionary[language]?.[key] ?? dictionary.en?.[key] ?? key
    return interpolate(translated, variables)
  }, [language])

  const changeLanguage = useCallback(lang => {
    if (!SUPPORTED_LANGUAGES.includes(lang)) return
    setLanguage(lang)
    localStorage.setItem('janmitra_lang', lang)
    document.documentElement.lang = lang === 'hinglish' ? 'en-IN' : lang
  }, [])

  useEffect(() => {
    const translateElement = element => {
      const textKey = element.getAttribute('data-i18n')
      const placeholderKey = element.getAttribute('data-i18n-placeholder')
      const titleKey = element.getAttribute('data-i18n-title')
      const ariaKey = element.getAttribute('data-i18n-aria-label')

      if (textKey) {
        const value = t(textKey)
        if (element.childElementCount === 0) {
          if (element.textContent !== value) element.textContent = value
        } else {
          const textNodes = Array.from(element.childNodes).filter(
            node => node.nodeType === Node.TEXT_NODE
          )
          const parts = value.split('\n')
          textNodes.forEach((node, index) => {
            const nextValue = parts.length > 1
              ? (parts[index] ?? '')
              : (index === 0 ? value : '')
            if (node.textContent !== nextValue) node.textContent = nextValue
          })
        }
      }
      if (placeholderKey) element.setAttribute('placeholder', t(placeholderKey))
      if (titleKey) element.setAttribute('title', t(titleKey))
      if (ariaKey) element.setAttribute('aria-label', t(ariaKey))
    }

    const applyToTree = root => {
      if (root.nodeType !== Node.ELEMENT_NODE && root !== document) return
      if (root !== document && root.matches?.('[data-i18n], [data-i18n-placeholder], [data-i18n-title], [data-i18n-aria-label]')) {
        translateElement(root)
      }
      root.querySelectorAll?.('[data-i18n], [data-i18n-placeholder], [data-i18n-title], [data-i18n-aria-label]').forEach(translateElement)
    }

    applyToTree(document)
    const observer = new MutationObserver(mutations => {
      mutations.forEach(mutation => {
        if (mutation.type === 'characterData') {
          applyToTree(mutation.target.parentElement)
          return
        }
        mutation.addedNodes.forEach(applyToTree)
      })
    })
    observer.observe(document.body, { childList: true, subtree: true, characterData: true })
    return () => observer.disconnect()
  }, [t])

  const value = useMemo(() => ({
    language,
    changeLanguage,
    t,
    supportedLanguages: SUPPORTED_LANGUAGES
  }), [language, changeLanguage, t])

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>
}
