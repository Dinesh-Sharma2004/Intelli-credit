import React from 'react'
import { Layout } from '@/components/Layout'
import { PDScoreGauge } from '@/components/Gauges'
import { FeatureImportanceChart, FinancialRatioRadar, RevenueGrowthChart } from '@/components/Charts'
import { StatCard, Table, Badge } from '@/components/UI'
import { TrendingUp, DollarSign, Activity } from 'lucide-react'

const featureImportanceData = [
  { feature: 'Debt-to-Equity', importance: 0.18 },
  { feature: 'Revenue Growth', importance: 0.16 },
  { feature: 'Interest Coverage', importance: 0.14 },
  { feature: 'Current Ratio', importance: 0.12 },
  { feature: 'EBITDA Margin', importance: 0.11 },
  { feature: 'Industry Risk', importance: 0.09 },
  { feature: 'Management Quality', importance: 0.08 },
  { feature: 'Litigation Risk', importance: 0.07 },
  { feature: 'Working Capital', importance: 0.05 },
]

const radarData = [
  { metric: 'Profitability', actual: 75, benchmark: 65 },
  { metric: 'Liquidity', actual: 70, benchmark: 70 },
  { metric: 'Leverage', actual: 55, benchmark: 60 },
  { metric: 'Growth', actual: 85, benchmark: 70 },
  { metric: 'Efficiency', actual: 72, benchmark: 68 },
]

const revenueData = [
  { period: 'Q1', revenue: 52.3, ebitda: 8.5 },
  { period: 'Q2', revenue: 61.2, ebitda: 11.2 },
  { period: 'Q3', revenue: 68.4, ebitda: 12.7 },
  { period: 'Q4', revenue: 63.6, ebitda: 11.8 },
]

const riskFactorsTable = [
  ['Debt-to-Equity', '1.50x', 'Benchmark: 1.20x', <Badge key="1" label="MEDIUM" type="warning" />],
  ['Current Ratio', '1.20x', 'Industry: 1.50x', <Badge key="2" label="ADEQUATE" type="info" />],
  ['Interest Coverage', '4.50x', 'Safe Level: 3.00x', <Badge key="3" label="HEALTHY" type="success" />],
  ['Litigation Cases', '2 Active', '1 Settled', <Badge key="4" label="MEDIUM-LOW" type="warning" />],
  ['Revenue Growth', '32%', 'Sector: 28%', <Badge key="5" label="STRONG" type="success" />],
]

export default function Dashboard() {
  const pd = 0.0625
  const creditGrade = 'A'
  const loanLimit = 15.50
  const interestRate = 11.75

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard
            label="Company Name"
            value="TechVenture Solutions"
            color="blue"
            icon={<Activity />}
            trend="up"
            trendValue="32% revenue growth"
          />
          <StatCard
            label="PD Score"
            value={`${(pd * 100).toFixed(2)}%`}
            unit="Risk"
            color="green"
            icon={<TrendingUp />}
          />
          <StatCard
            label="Credit Grade"
            value={creditGrade}
            color="blue"
            icon={<DollarSign />}
          />
          <StatCard
            label="Loan Recommendation"
            value={`₹${loanLimit}`}
            unit="Cr"
            color="orange"
            icon={<DollarSign />}
          />
        </div>

        {/* Main Metrics Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Risk Gauge */}
          <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
            <h3 className="text-lg font-semibold theme-gradient-text mb-6">Risk Assessment</h3>
            <div className="flex justify-center">
              <div className="text-center">
                <div className="relative w-40 h-40">
                  <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="45" stroke="#e5e7eb" strokeWidth="2" fill="none" />
                    <circle
                      cx="50"
                      cy="50"
                      r="45"
                      stroke="#f59e0b"
                      strokeWidth="2"
                      fill="none"
                      strokeDasharray="141.37 251.33"
                      strokeLinecap="round"
                    />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-3xl font-bold text-orange-500">6.5</span>
                    <span className="text-sm text-gray-600">out of 10</span>
                  </div>
                </div>
                <p className="mt-4 text-sm font-semibold text-orange-600">MEDIUM-LOW RISK</p>
              </div>
            </div>
          </div>

          {/* PD Score */}
          <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
            <h3 className="text-lg font-semibold theme-gradient-text mb-6">Probability of Default</h3>
            <div className="flex justify-center">
              <PDScoreGauge pd={pd} />
            </div>
          </div>

          {/* Credit Details */}
          <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
            <h3 className="text-lg font-semibold theme-gradient-text mb-4">Credit Details</h3>
            <div className="space-y-4">
              <div>
                <p className="text-sm text-gray-600">Interest Rate</p>
                <p className="text-2xl font-bold text-brand-blue">{interestRate.toFixed(2)}%</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Loan Tenor</p>
                <p className="text-2xl font-bold text-brand-blue">60 months</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Security Required</p>
                <p className="text-sm font-semibold text-gray-900">Asset Pledge + PG</p>
              </div>
              <button className="w-full mt-6 bg-brand-blue hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors">
                View Full Analysis
              </button>
            </div>
          </div>
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Feature Importance */}
          <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
            <h3 className="text-lg font-semibold theme-gradient-text mb-4">Feature Importance (SHAP)</h3>
            <FeatureImportanceChart data={featureImportanceData} />
          </div>

          {/* Financial Ratio Radar */}
          <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
            <h3 className="text-lg font-semibold theme-gradient-text mb-4">Financial Ratio Analysis</h3>
            <FinancialRatioRadar data={radarData} />
          </div>
        </div>

        {/* Revenue & Documents */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Revenue Growth */}
          <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
            <h3 className="text-lg font-semibold theme-gradient-text mb-4">Revenue & EBITDA Trend</h3>
            <RevenueGrowthChart data={revenueData} />
          </div>

          {/* Document Status */}
          <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
            <h3 className="text-lg font-semibold theme-gradient-text mb-4">Document Processing Status</h3>
            <div className="space-y-3">
              {[
                { name: 'Financial Statements', status: 'Completed', progress: 100 },
                { name: 'GST Filings', status: 'Completed', progress: 100 },
                { name: 'Bank Statements', status: 'Completed', progress: 100 },
                { name: 'Legal Documents', status: 'Processing', progress: 75 },
              ].map((doc) => (
                <div key={doc.name} className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span className="font-medium text-gray-900">{doc.name}</span>
                    <Badge label={doc.status} type={doc.status === 'Completed' ? 'success' : 'info'} />
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="h-full rounded-full bg-brand-blue transition-all"
                      style={{ width: `${doc.progress}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Risk Factors Table */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <h3 className="text-lg font-semibold theme-gradient-text mb-4">Key Risk Factors</h3>
          <Table
            headers={['Risk Factor', 'Current Value', 'Benchmark', 'Status']}
            rows={riskFactorsTable}
          />
        </div>

        {/* Bottom Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="bg-white border border-gray-200 hover:border-brand-blue text-gray-900 font-semibold py-3 px-6 rounded-lg transition-all">
            Download Report
          </button>
          <button className="bg-white border border-gray-200 hover:border-brand-blue text-gray-900 font-semibold py-3 px-6 rounded-lg transition-all">
            Export to PDF
          </button>
          <button className="bg-brand-blue hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-all">
            Generate CAM
          </button>
        </div>
      </div>
    </Layout>
  )
}
