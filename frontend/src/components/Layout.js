import Sidebar from './Sidebar'
import Navbar from './Navbar'
import Footer from './Footer'
import QuickDock from './QuickDock'
import LoadingScreen from './LoadingScreen'
import { useState, useEffect } from 'react'

export default function Layout({ children }) {
  const [loading, setLoading] = useState(true)
  const [sidebarOpen, setSidebarOpen] = useState(false)

  useEffect(() => {
    setTimeout(() => setLoading(false), 1800)
  }, [])

  return (
    <>
      <LoadingScreen visible={loading} />
      <div className="site-atmosphere fixed inset-0 pointer-events-none z-[-5] overflow-hidden">
        <div className="absolute w-[520px] h-[520px] -top-[230px] -right-[170px] rounded-full bg-[radial-gradient(circle,rgba(255,107,53,.14),transparent_68%)]"></div>
        <div className="absolute w-[600px] h-[600px] -bottom-[330px] -left-[230px] rounded-full bg-[radial-gradient(circle,rgba(13,124,102,.14),transparent_68%)]"></div>
        <div className="absolute inset-0 opacity-25 bg-[linear-gradient(rgba(20,40,30,.035)_1px,transparent_1px),linear-gradient(90deg,rgba(20,40,30,.035)_1px,transparent_1px)] bg-[length:45px_45px] [mask-image:linear-gradient(to_bottom,transparent,black_25%,black_70%,transparent)]"></div>
      </div>

      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className={`sidebar-overlay fixed inset-0 z-[2900] bg-black/50 backdrop-blur-sm transition-all duration-300 ${sidebarOpen ? 'opacity-100 visible pointer-events-auto' : 'opacity-0 invisible pointer-events-none'}`} onClick={() => setSidebarOpen(false)}></div>

      <div className="main-wrapper min-h-screen flex flex-col overflow-x-clip">
        <Navbar onMenuClick={() => setSidebarOpen(true)} />
        <main className="workspace-content w-full flex-1 mx-auto pt-3 sm:pt-5 pb-[120px]">
          {children}
        </main>
        <QuickDock />
        <Footer />
      </div>
    </>
  )
}
