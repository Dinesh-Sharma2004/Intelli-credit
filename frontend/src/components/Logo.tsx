import React from 'react'

export function Logo() {
  return (
    <div className="flex items-center gap-3 group cursor-pointer">
      <div className="relative w-10 h-10">
        {/* 3D Cube Effect Logo */}
        <svg
          viewBox="0 0 100 100"
          className="w-full h-full transition-transform duration-300 group-hover:scale-110 group-hover:rotate-12"
        >
          {/* Gradient Definition */}
          <defs>
            <linearGradient id="logoGrad1" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#3B82F6" />
              <stop offset="100%" stopColor="#1E40AF" />
            </linearGradient>
            <linearGradient id="logoGrad2" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#60A5FA" />
              <stop offset="100%" stopColor="#3B82F6" />
            </linearGradient>
            <linearGradient id="logoGrad3" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#93C5FD" />
              <stop offset="100%" stopColor="#60A5FA" />
            </linearGradient>
            <filter id="shadow">
              <feDropShadow dx="2" dy="4" stdDeviation="3" floodOpacity="0.4" />
            </filter>
          </defs>

          {/* Front Face */}
          <polygon points="20,30 50,15 80,30 50,45" fill="url(#logoGrad1)" filter="url(#shadow)" />

          {/* Left Face */}
          <polygon points="20,30 20,70 50,85 50,45" fill="url(#logoGrad2)" filter="url(#shadow)" />

          {/* Right Face */}
          <polygon points="50,45 50,85 80,70 80,30" fill="url(#logoGrad3)" filter="url(#shadow)" />

          {/* Credit Symbol */}
          <circle cx="50" cy="50" r="35" fill="none" stroke="#FFF" strokeWidth="2" opacity="0.3" />
          <text x="50" y="57" fontSize="24" fontWeight="bold" fill="#FFF" textAnchor="middle" className="group-hover:animate-pulse">
            IC
          </text>
        </svg>
      </div>

      {/* Logo Text */}
      <div>
        <div className="font-bold text-lg bg-gradient-to-r from-blue-600 to-blue-800 bg-clip-text text-transparent group-hover:from-blue-500 group-hover:to-blue-700 transition-all">
          Intelli-Credit
        </div>
        <div className="text-xs text-gray-500 dark:text-gray-400 group-hover:text-gray-600 dark:group-hover:text-gray-300 transition-colors">
          AI-Powered Decisioning
        </div>
      </div>
    </div>
  )
}
