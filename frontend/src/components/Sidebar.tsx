import React from 'react'
import Link from 'next/link'
import { BarChart3, TrendingUp, AlertCircle, CheckCircle } from 'lucide-react'

interface NavItem {
  label: string
  href: string
  icon: React.ReactNode
}

export function Sidebar() {
  const navItems: NavItem[] = [
    { label: 'Dashboard', href: '/', icon: <BarChart3 size={20} /> },
    { label: 'Document Upload', href: '/documents', icon: <TrendingUp size={20} /> },
    { label: 'Data Ingestor', href: '/ingestor', icon: <AlertCircle size={20} /> },
    { label: 'Research Agent', href: '/research', icon: <CheckCircle size={20} /> },
    { label: 'Credit Officer', href: '/credit-officer', icon: <TrendingUp size={20} /> },
    { label: 'Risk Scoring', href: '/risk-scoring', icon: <BarChart3 size={20} /> },
    { label: 'CAM Generator', href: '/cam-generator', icon: <CheckCircle size={20} /> },
  ]

  return (
    <aside className="w-64 bg-gradient-to-b from-brand-dark to-slate-dark text-white h-screen fixed left-0 top-0">
      {/* Logo */}
      <div className="p-6 border-b border-gray-700">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <span className="text-blue-300">⚡</span>
          Intelli-Credit
        </h1>
        <p className="text-xs text-gray-400 mt-1">AI Credit Engine</p>
      </div>

      {/* Navigation */}
      <nav className="mt-8 space-y-2 px-4">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-blue-700 transition-colors group"
          >
            <span className="text-gray-300 group-hover:text-white">{item.icon}</span>
            <span className="text-sm font-medium">{item.label}</span>
          </Link>
        ))}
      </nav>

      {/* Footer */}
      <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-700">
        <p className="text-xs text-gray-400">v1.0.0 • Hackathon Demo</p>
      </div>
    </aside>
  )
}
