import React, { useState, useEffect, useRef } from 'react'

import Link from 'next/link'

import { useRouter } from 'next/router'

import { Logo } from './Logo'

import { FileText, Search, BarChart3, Users, Brain, FileCheck, Zap, Sun, Moon } from 'lucide-react'

import { useTheme } from '@/context/ThemeContext'



export function ModernNavBar() {

  const [hoveredMenu, setHoveredMenu] = useState<string | null>(null)

  const [isTransitioning, setIsTransitioning] = useState(false)

  const router = useRouter()

  const { theme, toggleTheme, isThemeTransitioning } = useTheme()

  const previousPathRef = useRef<string>('')



  // Handle route changes with smooth transitions

  useEffect(() => {

    const currentPath = router.pathname

    if (previousPathRef.current !== currentPath) {

      setIsTransitioning(true)

      const timer = setTimeout(() => setIsTransitioning(false), 150) // Reduced delay

      return () => clearTimeout(timer)

    }

    previousPathRef.current = currentPath

  }, [router.pathname])



  const menuItems = [

    {

      label: 'Dashboard',

      href: '/',

      icon: BarChart3,

      description: 'Risk analysis & scoring overview',

      color: 'from-blue-500 to-cyan-500'

    },

    {

      label: 'Documents',

      href: '/documents',

      icon: FileText,

      description: 'Upload & process documents',

      color: 'from-green-500 to-emerald-500'

    },

    {

      label: 'Data Ingestor',

      href: '/ingestor',

      icon: Search,

      description: 'Extract & reconcile data',

      color: 'from-purple-500 to-pink-500'

    },

    {

      label: 'Research',

      href: '/research',

      icon: Brain,

      description: 'Company research & analysis',

      color: 'from-orange-500 to-red-500'

    },

    {

      label: 'Credit Officer',

      href: '/credit-officer',

      icon: Users,

      description: 'Qualitative assessment',

      color: 'from-indigo-500 to-purple-500'

    },

    {

      label: 'Risk Scoring',

      href: '/risk-scoring',

      icon: Zap,

      description: 'ML model outputs',

      color: 'from-yellow-500 to-orange-500'

    },

    {

      label: 'CAM Generator',

      href: '/cam-generator',

      icon: FileCheck,

      description: 'Generate appraisal memo',

      color: 'from-teal-500 to-blue-500'

    },

  ]



  return (

    <>

      {/* Modern Header */}

      <header className={`sticky top-0 z-50 backdrop-blur-xl border-b shadow-sm transition-all duration-200 ease-out ${isTransitioning ? 'scale-[0.98]' : 'scale-100'}`} style={{ backgroundColor: 'var(--bg-primary)', borderColor: 'var(--border-color)' }}>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">

          <div className="flex items-center justify-between">

            {/* Logo */}

            <Link href="/">

              <Logo />

            </Link>



            {/* Center Navigation */}

            <nav className="hidden lg:flex items-center gap-1">

              {menuItems.map((item) => {

                const Icon = item.icon

                const isActive = router.pathname === item.href

                return (

                  <Link

                    key={item.href}

                    href={item.href}

                    onMouseEnter={() => setHoveredMenu(item.href)}

                    onMouseLeave={() => setHoveredMenu(null)}

                    className={`relative group px-3 py-2 rounded-lg transition-all duration-200 ease-out transform hover:scale-105 ${isTransitioning || isThemeTransitioning ? 'pointer-events-none' : 'pointer-events-auto'}`}

                  >

                    {/* Background Gradient on Hover */}

                    <div className={`absolute inset-0 rounded-lg opacity-0 group-hover:opacity-100 transition-all duration-200 ease-out bg-gradient-to-r ${item.color} ${isTransitioning ? 'animate-pulse' : ''}`} />



                    {/* Active Indicator */}

                    {isActive && (

                      <div className={`absolute inset-0 rounded-lg bg-gradient-to-r ${item.color} -z-10 transition-all duration-200 ${isTransitioning ? 'animate-pulse' : ''}`} />

                    )}



                    {/* Content */}

                    <div className={`relative flex items-center gap-2 text-sm font-medium transition-all duration-200 ${

                      isActive ? 'text-white' : ''

                    } ${isTransitioning || isThemeTransitioning ? 'opacity-60' : 'opacity-100'}`} style={{ color: isActive ? 'white' : 'var(--text-primary)' }}>

                      <Icon size={16} className={`transition-transform duration-200 ${isActive ? 'scale-110' : 'scale-100'}`} />

                      <span className={`transition-all duration-200 ${isActive ? 'font-semibold' : 'font-medium'}`}>{item.label}</span>

                    </div>



                    {/* Tooltip on Hover */}

                    {hoveredMenu === item.href && !isTransitioning && (

                      <div className="absolute top-full left-0 mt-2 px-3 py-2 text-white text-xs rounded-lg whitespace-nowrap z-50 animate-in fade-in slide-in-from-top-1 transition-all duration-200" style={{ backgroundColor: 'var(--bg-tertiary)' }}>

                        {item.description}

                        <div className="absolute -top-1 left-4 w-2 h-2 rotate-45 transition-all duration-200" style={{ backgroundColor: 'var(--bg-tertiary)' }} />

                      </div>

                    )}

                  </Link>

                )

              })}

            </nav>



            {/* Right Side Actions */}

            <div className="flex items-center gap-3">

              <button

                onClick={toggleTheme}

                aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}

                title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}

                className="flex items-center justify-center w-10 h-10 rounded-lg border hover:scale-105 hover:-translate-y-0.5 hover:shadow-lg transition-all duration-300 cursor-pointer-advanced" style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--card-bg)', color: 'var(--text-primary)' }}

              >

                {theme === 'light' ? <Moon size={17} /> : <Sun size={17} />}

              </button>

              <button className="hidden sm:flex items-center gap-2 px-4 py-2 rounded-lg transition-all duration-300 text-sm font-medium group" style={{ color: 'var(--text-primary)' }} onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--bg-tertiary)'} onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}>

                <Search size={16} />

                <span className="hidden lg:inline">Search</span>

              </button>

              

              {/* Profile or Settings */}

              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold cursor-pointer hover:shadow-lg hover:shadow-blue-500/50 transition-all duration-300 transform hover:scale-110">

                IC

              </div>

            </div>

          </div>

        </div>



        {/* Mobile Menu Toggle */}

        <div className="lg:hidden px-4 pb-4">

          <div className={`grid grid-cols-4 gap-2 transition-all duration-200 ${isTransitioning ? 'opacity-60 pointer-events-none' : 'opacity-100 pointer-events-auto'}`}>

            {menuItems.slice(0, 4).map((item) => (

              <Link

                key={item.href}

                href={item.href}

                className={`flex items-center justify-center gap-1 px-2 py-2 rounded-lg text-xs font-medium transition-all duration-200 transform hover:scale-105 ${

                  router.pathname === item.href

                    ? 'bg-blue-500 text-white'

                    : ''

                } ${isTransitioning ? 'pointer-events-none opacity-60' : 'pointer-events-auto opacity-100'}`} style={{ backgroundColor: router.pathname === item.href ? '' : 'var(--bg-tertiary)', color: router.pathname === item.href ? 'white' : 'var(--text-primary)' }}

              >

                {React.createElement(item.icon, { size: 14 })}

                <span className="hidden sm:inline">{item.label}</span>

              </Link>

            ))}

          </div>

        </div>

      </header>

    </>

  )

}

