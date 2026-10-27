import React, { createContext, useContext, useEffect, useState } from 'react'

type Theme = 'light' | 'dark'

interface ThemeContextType {
  theme: Theme
  toggleTheme: () => void
  isThemeTransitioning: boolean
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>('light')
  const [isThemeTransitioning, setIsThemeTransitioning] = useState(false)

  useEffect(() => {
    // Initialize from persisted value; fallback to system preference.
    const stored = localStorage.getItem('theme')
    const resolvedTheme: Theme =
      stored === 'light' || stored === 'dark'
        ? stored
        : window.matchMedia('(prefers-color-scheme: dark)').matches
          ? 'dark'
          : 'light'

    setTheme(resolvedTheme)
  }, [])

  useEffect(() => {
    const onStorage = (event: StorageEvent) => {
      if (event.key !== 'theme') return
      if (event.newValue === 'light' || event.newValue === 'dark') {
        setTheme(event.newValue)
      }
    }

    window.addEventListener('storage', onStorage)
    return () => window.removeEventListener('storage', onStorage)
  }, [])

  useEffect(() => {
    const htmlElement = document.documentElement
    
    // Add transition class during theme change
    if (isThemeTransitioning) {
      htmlElement.classList.add('theme-transitioning')
    } else {
      htmlElement.classList.remove('theme-transitioning')
    }
    
    // Force theme application with immediate DOM update
    requestAnimationFrame(() => {
      htmlElement.classList.toggle('dark', theme === 'dark')
      localStorage.setItem('theme', theme)
      
      // Force reflow of all elements
      htmlElement.style.display = 'none'
      htmlElement.offsetHeight // Trigger reflow
      htmlElement.style.display = ''
    })
  }, [theme, isThemeTransitioning])

  const toggleTheme = () => {
    setIsThemeTransitioning(true)
    setTheme(prev => prev === 'light' ? 'dark' : 'light')
    setTimeout(() => setIsThemeTransitioning(false), 300) // Match transition duration
  }

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, isThemeTransitioning }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider')
  }
  return context
}
