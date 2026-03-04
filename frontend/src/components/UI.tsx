import React from 'react'
import { AlertCircle, CheckCircle, XCircle } from 'lucide-react'

interface AlertProps {
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message: string
  onClose?: () => void
}

export function Alert({ type, title, message, onClose }: AlertProps) {
  const colors = {
    success: { bg: 'bg-green-50 dark:bg-green-950/30', border: 'border-green-200 dark:border-green-900/60', icon: 'text-green-600', title: 'text-green-900 dark:text-green-200' },
    error: { bg: 'bg-red-50 dark:bg-red-950/30', border: 'border-red-200 dark:border-red-900/60', icon: 'text-red-600', title: 'text-red-900 dark:text-red-200' },
    warning: { bg: 'bg-amber-50 dark:bg-amber-950/30', border: 'border-amber-200 dark:border-amber-900/60', icon: 'text-amber-600', title: 'text-amber-900 dark:text-amber-200' },
    info: { bg: 'bg-blue-50 dark:bg-blue-950/30', border: 'border-blue-200 dark:border-blue-900/60', icon: 'text-blue-600', title: 'text-blue-900 dark:text-blue-200' },
  }
  const closeColors = {
    success: 'text-green-600',
    error: 'text-red-600',
    warning: 'text-amber-600',
    info: 'text-blue-600',
  }

  const color = colors[type]
  const Icon = type === 'success' ? CheckCircle : type === 'error' ? XCircle : AlertCircle

  return (
    <div className={`${color.bg} border ${color.border} rounded-lg p-4 flex gap-3`}>
      <Icon className={`flex-shrink-0 w-5 h-5 ${color.icon}`} />
      <div className="flex-1">
        <h3 className={`font-medium ${color.title}`}>{title}</h3>
        <p className={`text-sm ${color.title} opacity-75`}>{message}</p>
      </div>
      {onClose && (
        <button onClick={onClose} className={`${closeColors[type]} hover:opacity-75`}>
          ✕
        </button>
      )}
    </div>
  )
}

interface StatCardProps {
  label: string
  value: string | number
  unit?: string
  icon?: React.ReactNode
  trend?: 'up' | 'down' | 'neutral'
  trendValue?: string
  color?: 'blue' | 'green' | 'orange' | 'red'
}

export function StatCard({ label, value, unit = '', icon, trend, trendValue, color = 'blue' }: StatCardProps) {
  const colors = {
    blue: 'bg-blue-50 border-blue-200 dark:bg-blue-950/30 dark:border-blue-900/60',
    green: 'bg-green-50 border-green-200 dark:bg-green-950/30 dark:border-green-900/60',
    orange: 'bg-orange-50 border-orange-200 dark:bg-orange-950/30 dark:border-orange-900/60',
    red: 'bg-red-50 border-red-200 dark:bg-red-950/30 dark:border-red-900/60',
  }

  const textColors = {
    blue: 'text-blue-900 dark:text-blue-200',
    green: 'text-green-900 dark:text-green-200',
    orange: 'text-orange-900 dark:text-orange-200',
    red: 'text-red-900 dark:text-red-200',
  }

  const trendColors = {
    up: 'text-green-600',
    down: 'text-red-600',
    neutral: 'text-gray-600',
  }

  return (
    <div className={`${colors[color]} border rounded-lg p-6 report-box advanced-hover cursor-zoom-card`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-gray-600 dark:text-gray-300 font-medium">{label}</p>
          <p className={`text-3xl font-bold mt-2 ${textColors[color]}`}>
            {value} <span className="text-lg">{unit}</span>
          </p>
          {trend && trendValue && (
            <p className={`text-xs mt-2 ${trendColors[trend]}`}>
              {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'} {trendValue}
            </p>
          )}
        </div>
        {icon && <div className={`text-2xl ${textColors[color]} opacity-50`}>{icon}</div>}
      </div>
    </div>
  )
}

interface TableProps {
  headers: string[]
  rows: (string | number | React.ReactNode)[][]
  striped?: boolean
  hoverable?: boolean
}

export function Table({ headers, rows, striped = true, hoverable = true }: TableProps) {
  return (
    <div className="overflow-x-auto border rounded-lg dark:border-gray-700">
      <table className="w-full">
        <thead className="bg-slate-50 border-b dark:bg-gray-800 dark:border-gray-700">
          <tr>
            {headers.map((header, i) => (
              <th key={i} className="px-6 py-3 text-left text-sm font-semibold text-gray-900 dark:text-gray-100">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr
              key={i}
              className={`border-b dark:border-gray-700 ${striped && i % 2 === 0 ? 'bg-slate-50 dark:bg-gray-800' : 'bg-white dark:bg-gray-900'} ${
                hoverable ? 'hover:bg-blue-50 dark:hover:bg-gray-800 transition-colors' : ''
              }`}
            >
              {row.map((cell, j) => (
                <td key={j} className="px-6 py-4 text-sm text-gray-900 dark:text-gray-100">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

interface BadgeProps {
  label: string
  type?: 'success' | 'error' | 'warning' | 'info' | 'default'
}

export function Badge({ label, type = 'default' }: BadgeProps) {
  const colors = {
    success: 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-200',
    error: 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-200',
    warning: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200',
    info: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-200',
    default: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200',
  }

  return (
    <span className={`inline-block px-3 py-1 text-xs font-semibold rounded-full ${colors[type]}`}>
      {label}
    </span>
  )
}

interface ProgressBarProps {
  value: number
  max?: number
  label?: string
  color?: 'blue' | 'green' | 'orange' | 'red'
}

export function ProgressBar({ value, max = 100, label, color = 'blue' }: ProgressBarProps) {
  const percentage = (value / max) * 100
  const colors = {
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    orange: 'bg-orange-500',
    red: 'bg-red-500',
  }

  return (
    <div className="space-y-1">
      {label && <p className="text-xs font-medium text-gray-700 dark:text-gray-300">{label}</p>}
      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
        <div
          className={`h-full ${colors[color]} transition-all duration-300`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
      <p className="text-xs text-gray-600 dark:text-gray-300">{value.toFixed(0)} / {max.toFixed(0)}</p>
    </div>
  )
}
