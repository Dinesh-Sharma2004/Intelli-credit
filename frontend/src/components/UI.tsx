import React from 'react'

// StatCard Component
interface StatCardProps {
  title: string
  value: string | number
  unit?: string
  trend?: number
  icon?: React.ReactNode
  color?: 'blue' | 'green' | 'red' | 'yellow' | 'purple'
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  unit = '',
  trend,
  icon,
  color = 'blue',
}) => {
  const colorClass = {
    blue: 'bg-blue-50 border-blue-200 text-blue-900',
    green: 'bg-green-50 border-green-200 text-green-900',
    red: 'bg-red-50 border-red-200 text-red-900',
    yellow: 'bg-yellow-50 border-yellow-200 text-yellow-900',
    purple: 'bg-purple-50 border-purple-200 text-purple-900',
  }[color]

  const trendColor = trend && trend > 0 ? 'text-green-600' : trend && trend < 0 ? 'text-red-600' : 'text-gray-600'

  return (
    <div className={`${colorClass} border rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600 mb-2">{title}</p>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold">{value}</span>
            {unit && <span className="text-sm text-gray-500">{unit}</span>}
          </div>
          {trend !== undefined && (
            <p className={`text-sm mt-2 ${trendColor}`}>
              {trend > 0 ? '↑' : trend < 0 ? '↓' : '→'} {Math.abs(trend)}%
            </p>
          )}
        </div>
        {icon && <div className="text-2xl ml-4">{icon}</div>}
      </div>
    </div>
  )
}

// Badge Component
interface BadgeProps {
  label: string
  type?: 'success' | 'warning' | 'error' | 'info' | 'default'
  size?: 'sm' | 'md' | 'lg'
}

export const Badge: React.FC<BadgeProps> = ({ label, type = 'default', size = 'md' }) => {
  const typeClass = {
    success: 'bg-green-100 text-green-800',
    warning: 'bg-yellow-100 text-yellow-800',
    error: 'bg-red-100 text-red-800',
    info: 'bg-blue-100 text-blue-800',
    default: 'bg-gray-100 text-gray-800',
  }[type]

  const sizeClass = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-1 text-sm',
    lg: 'px-4 py-2 text-base',
  }[size]

  return <span className={`${typeClass} ${sizeClass} font-semibold rounded-full inline-block`}>{label}</span>
}

// Table Component
interface TableProps {
  columns?: string[]
  headers?: string[]
  rows?: (string | number | React.ReactNode)[][]
  striped?: boolean
  hoverable?: boolean
}

export const Table: React.FC<TableProps> = ({ columns, headers, rows, striped = true, hoverable = true }) => {
  const cols = headers || columns || []
  const tableRows = rows || []

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
      <table className="w-full">
        <thead>
          <tr className="bg-gray-50 border-b border-gray-200">
            {cols.map((col, idx) => (
              <th key={idx} className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {tableRows.map((row, rowIdx) => (
            <tr
              key={rowIdx}
              className={`border-b border-gray-200 ${
                striped && rowIdx % 2 === 1 ? 'bg-gray-50' : ''
              } ${hoverable ? 'hover:bg-gray-100 transition-colors' : ''}`}
            >
              {row && row.map((cell, cellIdx) => (
                <td key={cellIdx} className="px-6 py-4 text-sm text-gray-700">
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

// ProgressBar Component
interface ProgressBarProps {
  value: number
  max?: number
  label?: string
  showLabel?: boolean
  color?: 'blue' | 'green' | 'red' | 'yellow' | 'purple'
  animated?: boolean
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  max = 100,
  label,
  showLabel = true,
  color = 'blue',
  animated = true,
}) => {
  const percentage = (value / max) * 100
  const colorClass = {
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    red: 'bg-red-500',
    yellow: 'bg-yellow-500',
    purple: 'bg-purple-500',
  }[color]

  return (
    <div>
      {showLabel && (
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">{label}</span>
          <span className="text-sm font-semibold text-gray-900">{Math.round(percentage)}%</span>
        </div>
      )}
      <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
        <div
          className={`h-full ${colorClass} rounded-full transition-all ${animated ? 'duration-500' : ''}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}

// Alert Component
interface AlertProps {
  type?: 'success' | 'warning' | 'error' | 'info'
  title?: string
  message: string
  icon?: React.ReactNode
  closable?: boolean
  onClose?: () => void
}

export const Alert: React.FC<AlertProps> = ({
  type = 'info',
  title,
  message,
  icon,
  closable = false,
  onClose,
}) => {
  const typeClass = {
    success: 'bg-green-50 border-green-200 text-green-900',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-900',
    error: 'bg-red-50 border-red-200 text-red-900',
    info: 'bg-blue-50 border-blue-200 text-blue-900',
  }[type]

  const iconColor = {
    success: 'text-green-600',
    warning: 'text-yellow-600',
    error: 'text-red-600',
    info: 'text-blue-600',
  }[type]

  return (
    <div className={`${typeClass} border border-current rounded-lg p-4 mb-4 flex items-start`}>
      {icon && <div className={`${iconColor} mr-3 flex-shrink-0 mt-0.5`}>{icon}</div>}
      <div className="flex-1">
        {title && <h4 className="font-semibold mb-1">{title}</h4>}
        <p className="text-sm">{message}</p>
      </div>
      {closable && (
        <button onClick={onClose} className="ml-3 text-gray-400 hover:text-gray-600 flex-shrink-0">
          ✕
        </button>
      )}
    </div>
  )
}

interface PDGaugeProps {
  pd: number
  grade?: string
}

export const PDGaugeMeter: React.FC<PDGaugeProps> = ({ pd, grade }) => {
  const percentage = Math.max(0, Math.min(pd * 100, 100))
  const stroke = 2 * Math.PI * 52
  const offset = stroke - (percentage / 100) * stroke

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">PD Gauge</h3>
        {grade && <Badge label={grade} type="info" />}
      </div>
      <div className="flex items-center gap-6">
        <svg width="140" height="140" viewBox="0 0 140 140">
          <circle cx="70" cy="70" r="52" stroke="#e5e7eb" strokeWidth="12" fill="none" />
          <circle
            cx="70"
            cy="70"
            r="52"
            stroke={percentage > 16 ? '#dc2626' : percentage > 8 ? '#d97706' : '#2563eb'}
            strokeWidth="12"
            fill="none"
            strokeDasharray={stroke}
            strokeDashoffset={offset}
            strokeLinecap="round"
            transform="rotate(-90 70 70)"
          />
          <text x="70" y="66" textAnchor="middle" className="fill-gray-900 text-2xl font-bold">
            {percentage.toFixed(1)}%
          </text>
          <text x="70" y="88" textAnchor="middle" className="fill-gray-500 text-xs">
            PD
          </text>
        </svg>
        <p className="text-sm text-gray-600">Lower probability of default indicates stronger underwriting quality and pricing flexibility.</p>
      </div>
    </div>
  )
}

interface HeatmapProps {
  items: Array<{ dimension: string; value: number }>
}

export const RiskHeatmapCard: React.FC<HeatmapProps> = ({ items }) => (
  <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
    <h3 className="text-lg font-semibold text-gray-900 mb-4">Risk Heatmap</h3>
    <div className="grid grid-cols-2 gap-3">
      {items.map((item) => (
        <div key={item.dimension} className="rounded-lg p-4" style={{ backgroundColor: `rgba(37, 99, 235, ${Math.max(item.value, 0.08)})` }}>
          <p className="text-xs uppercase tracking-wide text-white/80">{item.dimension}</p>
          <p className="text-2xl font-bold text-white mt-2">{(item.value * 10).toFixed(1)}</p>
        </div>
      ))}
    </div>
  </div>
)

interface AlertPanelProps {
  title: string
  items: string[]
}

export const AnomalyAlertPanel: React.FC<AlertPanelProps> = ({ title, items }) => (
  <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
    <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
    {items.length === 0 ? (
      <p className="text-sm text-gray-500">No material alerts detected.</p>
    ) : (
      <div className="space-y-2">
        {items.map((item) => (
          <div key={item} className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-800">
            {item}
          </div>
        ))}
      </div>
    )}
  </div>
)

interface TimelineProps {
  items: Array<{ title: string; subtitle?: string; severity?: string }>
}

export const ResearchIntelligenceTimeline: React.FC<TimelineProps> = ({ items }) => (
  <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
    <h3 className="text-lg font-semibold text-gray-900 mb-4">Research Intelligence Timeline</h3>
    <div className="space-y-4">
      {items.map((item, index) => (
        <div key={`${item.title}-${index}`} className="flex gap-3">
          <div className="mt-1 h-3 w-3 rounded-full bg-blue-600" />
          <div>
            <p className="font-medium text-gray-900">{item.title}</p>
            {item.subtitle && <p className="text-sm text-gray-600 mt-1">{item.subtitle}</p>}
            {item.severity && <p className="text-xs text-gray-500 mt-1 uppercase">{item.severity}</p>}
          </div>
        </div>
      ))}
    </div>
  </div>
)

export const CovenantSuggestionsSection: React.FC<{ items: string[] }> = ({ items }) => (
  <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
    <h3 className="text-lg font-semibold text-gray-900 mb-4">Covenant Suggestions</h3>
    <div className="space-y-2">
      {items.length === 0 ? <p className="text-sm text-gray-500">No additional covenants suggested.</p> : items.map((item) => (
        <div key={item} className="rounded-lg bg-slate-50 border border-slate-200 px-4 py-3 text-sm text-slate-800">{item}</div>
      ))}
    </div>
  </div>
)

export const SanctionSliderSimulator: React.FC<{ bands: Record<string, number> }> = ({ bands }) => {
  const entries = Object.entries(bands)
  if (entries.length === 0) return null
  const maxValue = Math.max(...entries.map(([, value]) => Number(value)), 1)
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Sanction Simulator</h3>
      <div className="space-y-4">
        {entries.map(([label, value]) => (
          <div key={label}>
            <div className="flex items-center justify-between text-sm mb-2">
              <span className="font-medium text-gray-700 capitalize">{label}</span>
              <span className="text-gray-900 font-semibold">₹{(Number(value) / 10000000).toFixed(2)} Cr</span>
            </div>
            <div className="h-3 rounded-full bg-gray-200 overflow-hidden">
              <div className="h-full rounded-full bg-blue-600" style={{ width: `${(Number(value) / maxValue) * 100}%` }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
