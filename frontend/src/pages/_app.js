import '@/styles/globals.css'
import Head from 'next/head'
import { ThemeProvider } from '@/contexts/ThemeContext'
import { LanguageProvider } from '@/contexts/LanguageContext'
import Layout from '@/components/Layout'
import { AuthProvider } from '@/contexts/AuthContext'

export default function App({ Component, pageProps }) {
  return (
    <>
      <Head>
        <title>JanMitra AI — AI-Powered Citizen Welfare Assistant</title>
        <meta name="description" content="AI-powered citizen welfare assistance for schemes, documents, grievances, and conversational guidance." />
      </Head>
      <ThemeProvider>
        <LanguageProvider>
          <AuthProvider>
            <Layout>
              <Component {...pageProps} />
            </Layout>
          </AuthProvider>
        </LanguageProvider>
      </ThemeProvider>
    </>
  )
}
