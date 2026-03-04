import React from 'react'
import { useTheme } from '@/context/ThemeContext'

interface GaugeProps {
  value: number
  max?: number
  label: string
  unit?: string
  color?: string
}

export function RiskGauge({ value, max = 100, label, unit = '%' }: GaugeProps) {
  const { theme } = useTheme()
  const percentage = (value / max) * 100
  const circumference = 2 * Math.PI * 45
  const strokeDashoffset = circumference - (percentage / 100) * circumference
  const trackColor = theme === 'dark' ? '#374151' : '#e5e7eb'
  
  const getCenterColor = () => {
    if (percentage < 30) return '#10b981'
    if (percentage < 60) return '#f59e0b'
    return '#ef4444'
  }

  return (
    <div className="flex flex-col items-center gap-4">
      <div className="relative w-32 h-32">
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="45" stroke={trackColor} strokeWidth="2" fill="none" />
          <circle
            cx="50"
            cy="50"
            r="45"
            stroke={getCenterColor()}
            strokeWidth="2"
            fill="none"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-500"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold" style={{ color: getCenterColor() }}>
            {value.toFixed(1)}{unit}
          </span>
          <span className="text-xs text-gray-600 dark:text-gray-300 mt-1">{label}</span>
        </div>
      </div>
    </div>
  )
}

export function PDScoreGauge({ pd }: { pd: number }) {
  const { theme } = useTheme()
  const risk = pd < 0.05 ? 'LOW' : pd < 0.10 ? 'MEDIUM' : 'HIGH'
  const trackColor = theme === 'dark' ? '#374151' : '#e5e7eb'
  const colors = {
    LOW: '#10b981',
    MEDIUM: '#f59e0b',
    HIGH: '#ef4444'
  }

  return (
    <div className="text-center">
      <div className="relative w-28 h-28 mx-auto mb-2">
        <svg className="w-full h-full" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="40" stroke={trackColor} strokeWidth="2" fill="none" />
          <circle
            cx="50"
            cy="50"
            r="40"
            stroke={colors[risk]}
            strokeWidth="2"
            fill="none"
            strokeDasharray={`${(pd / 0.30) * 251.3} 251.3`}
            strokeLinecap="round"
            className="transform -rotate-90 origin-center"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-xl font-bold" style={{ color: colors[risk] }}>
            {(pd * 100).toFixed(1)}%
          </span>
          <span className="text-xs text-gray-600 dark:text-gray-300">PD Score</span>
        </div>
      </div>
      <p className="text-sm font-semibold mt-2" style={{ color: colors[risk] }}>
        {risk} RISK
      </p>
    </div>
  )
}
