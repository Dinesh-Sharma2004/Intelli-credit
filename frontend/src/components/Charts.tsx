import React from 'react'
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
  ComposedChart,
  Area,
  AreaChart
} from 'recharts'
import { useTheme } from '@/context/ThemeContext'

function useChartTheme() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  return {
    isDark,
    grid: isDark ? '#334155' : '#e5e7eb',
    axis: isDark ? '#cbd5e1' : '#475569',
    tooltipBg: isDark ? '#111827' : '#ffffff',
    tooltipBorder: isDark ? '#374151' : '#d1d5db',
    tooltipText: isDark ? '#e5e7eb' : '#0f172a',
  }
}

export function FeatureImportanceChart({ data }: { data: any[] }) {
  const colors = ['#0066CC', '#00a8e8', '#00d9ff', '#f59e0b', '#ef4444']
  const chartTheme = useChartTheme()

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} margin={{ top: 20, right: 30, left: 0, bottom: 20 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={chartTheme.grid} />
        <XAxis dataKey="feature" tick={{ fontSize: 12, fill: chartTheme.axis }} angle={-45} textAnchor="end" height={80} />
        <YAxis tick={{ fontSize: 12, fill: chartTheme.axis }} />
        <Tooltip
          contentStyle={{
            backgroundColor: chartTheme.tooltipBg,
            border: `1px solid ${chartTheme.tooltipBorder}`,
            color: chartTheme.tooltipText
          }}
          labelStyle={{ color: chartTheme.tooltipText }}
        />
        <Bar dataKey="importance" fill="#0066CC" radius={[8, 8, 0, 0]}>
          {data.map((_entry: any, index: number) => (
            <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

export function PDProbabilityChart({ data }: { data: any[] }) {
  const chartTheme = useChartTheme()
  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={data}>
        <defs>
          <linearGradient id="colorPD" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#0066CC" stopOpacity={0.8} />
            <stop offset="95%" stopColor="#0066CC" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke={chartTheme.grid} />
        <XAxis dataKey="period" tick={{ fill: chartTheme.axis }} />
        <YAxis tick={{ fill: chartTheme.axis }} />
        <Tooltip
          contentStyle={{
            backgroundColor: chartTheme.tooltipBg,
            border: `1px solid ${chartTheme.tooltipBorder}`,
            color: chartTheme.tooltipText
          }}
          labelStyle={{ color: chartTheme.tooltipText }}
        />
        <Area type="monotone" dataKey="value" stroke="#0066CC" fillOpacity={1} fill="url(#colorPD)" />
      </AreaChart>
    </ResponsiveContainer>
  )
}

export function FinancialRatioRadar({ data }: { data: any[] }) {
  const chartTheme = useChartTheme()
  return (
    <ResponsiveContainer width="100%" height={350}>
      <RadarChart data={data}>
        <PolarGrid stroke={chartTheme.grid} />
        <PolarAngleAxis dataKey="metric" tick={{ fontSize: 11, fill: chartTheme.axis }} />
        <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: chartTheme.axis }} />
        <Radar name="Actual" dataKey="actual" stroke="#0066CC" fill="#0066CC" fillOpacity={0.6} />
        <Radar name="Benchmark" dataKey="benchmark" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.6} />
        <Legend wrapperStyle={{ color: chartTheme.axis }} />
        <Tooltip
          contentStyle={{
            backgroundColor: chartTheme.tooltipBg,
            border: `1px solid ${chartTheme.tooltipBorder}`,
            color: chartTheme.tooltipText
          }}
          labelStyle={{ color: chartTheme.tooltipText }}
        />
      </RadarChart>
    </ResponsiveContainer>
  )
}

export function LoanLimitMeter({ current, max }: { current: number; max: number }) {
  const percentage = (current / max) * 100

  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span className="font-medium text-gray-900 dark:text-gray-100">Loan Limit Utilization</span>
        <span className="font-bold text-brand-blue">₹{(current / 10000000).toFixed(2)}Cr</span>
      </div>
      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${
            percentage > 80 ? 'bg-red-500' : percentage > 50 ? 'bg-yellow-500' : 'bg-green-500'
          }`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
      <p className="text-xs text-gray-600 dark:text-gray-300">
        {percentage.toFixed(0)}% of ₹{(max / 10000000).toFixed(2)}Cr recommended limit
      </p>
    </div>
  )
}

export function SHAPWaterfallChart({ data }: { data: any[] }) {
  const chartTheme = useChartTheme()
  return (
    <ResponsiveContainer width="100%" height={350}>
      <ComposedChart
        data={data}
        margin={{ top: 20, right: 30, left: 20, bottom: 80 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke={chartTheme.grid} />
        <XAxis dataKey="feature" angle={-45} textAnchor="end" height={80} tick={{ fontSize: 11, fill: chartTheme.axis }} />
        <YAxis tick={{ fontSize: 11, fill: chartTheme.axis }} />
        <Tooltip
          contentStyle={{
            backgroundColor: chartTheme.tooltipBg,
            border: `1px solid ${chartTheme.tooltipBorder}`,
            color: chartTheme.tooltipText
          }}
          labelStyle={{ color: chartTheme.tooltipText }}
        />
        <Bar dataKey="contribution" fill="#0066CC" radius={[4, 4, 0, 0]}>
          {data.map((entry: any, index: number) => (
            <Cell key={`cell-${index}`} fill={entry.contribution > 0 ? '#10b981' : '#ef4444'} />
          ))}
        </Bar>
      </ComposedChart>
    </ResponsiveContainer>
  )
}

export function RevenueGrowthChart({ data }: { data: any[] }) {
  const chartTheme = useChartTheme()
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke={chartTheme.grid} />
        <XAxis dataKey="period" tick={{ fill: chartTheme.axis }} />
        <YAxis tick={{ fill: chartTheme.axis }} />
        <Tooltip
          contentStyle={{
            backgroundColor: chartTheme.tooltipBg,
            border: `1px solid ${chartTheme.tooltipBorder}`,
            color: chartTheme.tooltipText,
            borderRadius: '8px'
          }}
          labelStyle={{ color: chartTheme.tooltipText }}
        />
        <Legend wrapperStyle={{ color: chartTheme.axis }} />
        <Line
          type="monotone"
          dataKey="revenue"
          stroke="#0066CC"
          strokeWidth={3}
          dot={{ fill: '#0066CC', r: 4 }}
          activeDot={{ r: 6 }}
        />
        <Line
          type="monotone"
          dataKey="ebitda"
          stroke="#10b981"
          strokeWidth={3}
          dot={{ fill: '#10b981', r: 4 }}
          activeDot={{ r: 6 }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
