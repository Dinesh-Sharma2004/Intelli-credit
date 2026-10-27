import React, { useEffect, useState } from 'react'
import { useRouter } from 'next/router'
import { InteractiveBackground } from './InteractiveBackground'
import { ModernNavBar } from './ModernNavBar'

interface LayoutProps {
  children: React.ReactNode
}

export function Layout({ children }: LayoutProps) {
  const [isPageTransitioning, setIsPageTransitioning] = useState(false)
  const router = useRouter()

  // Handle page transitions
  useEffect(() => {
    const handleRouteChange = () => {
      setIsPageTransitioning(true)
      setTimeout(() => setIsPageTransitioning(false), 200)
    }

    router.events.on('routeChangeStart', handleRouteChange)
    return () => {
      router.events.off('routeChangeStart', handleRouteChange)
    }
  }, [router.events])

  return (
    <div className={`min-h-screen transition-colors duration-300 relative ${isPageTransitioning ? 'animate-pulse' : ''}`} style={{ backgroundColor: 'var(--bg-secondary)' }}>
      <InteractiveBackground />
      <div className={`relative z-10 transition-all duration-300 ${isPageTransitioning ? 'opacity-80 scale-[0.98]' : 'opacity-100 scale-100'}`}>
        <ModernNavBar />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          {children}
        </main>

        {/* Footer */}
        <footer className="mt-20 transition-colors duration-300" style={{ borderTop: '1px solid var(--border-color)', backgroundColor: 'var(--bg-primary)' }}>
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="flex justify-between items-center text-sm" style={{ color: 'var(--text-secondary)' }}>
              <p>&copy; 2026 Intelli-Credit. AI-Powered Credit Decisioning.</p>
              <div className="flex gap-6">
                <a href="#" className="transition-colors duration-300 hover:text-gray-900 dark:hover:text-gray-100" style={{ color: 'var(--text-secondary)' }}>Privacy</a>
                <a href="#" className="transition-colors duration-300 hover:text-gray-900 dark:hover:text-gray-100" style={{ color: 'var(--text-secondary)' }}>Terms</a>
                <a href="#" className="transition-colors duration-300 hover:text-gray-900 dark:hover:text-gray-100" style={{ color: 'var(--text-secondary)' }}>Support</a>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </div>
  )
}
