import React from 'react'
import { ModernNavBar } from './ModernNavBar'

interface LayoutProps {
  children: React.ReactNode
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-white via-blue-50 to-blue-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 transition-colors duration-300">
      <ModernNavBar />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {children}
      </main>

      {/* Footer */}
      <footer className="mt-20 border-t border-gray-200 dark:border-gray-700 bg-white/50 dark:bg-gray-900/50 backdrop-blur transition-colors duration-300">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex justify-between items-center text-sm text-gray-600 dark:text-gray-400">
            <p>&copy; 2026 Intelli-Credit. AI-Powered Credit Decisioning.</p>
            <div className="flex gap-6">
              <a href="#" className="hover:text-gray-900 dark:hover:text-gray-100 transition-colors duration-300">Privacy</a>
              <a href="#" className="hover:text-gray-900 dark:hover:text-gray-100 transition-colors duration-300">Terms</a>
              <a href="#" className="hover:text-gray-900 dark:hover:text-gray-100 transition-colors duration-300">Support</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
