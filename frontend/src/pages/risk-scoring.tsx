import React, { useState } from 'react'
import { Layout } from '@/components/Layout'
import { Badge, StatCard, Alert } from '@/components/UI'
import { AlertCircle, TrendingUp } from 'lucide-react'

export default function RiskScoringPage() {
  const [selectedCompany] = useState({
    name: 'TechVenture Solutions Pvt Ltd',
    revenue: 245.67,
    ebitda: 45.35,
    debt: 150.0,
    cash: 38.5,
    pd: 0.0625,
    grade: 'A',
    loanLimit: 15.50,
    rate: 0.1175,
  })

  const riskDrivers = [
    {
      factor: 'Debt-to-Equity Ratio',
      value: 1.50,
      threshold: 1.20,
      status: 'MEDIUM',
      impact: -0.15,
    },
    {
      factor: 'Litigation Exposure',
      value: 2,
      threshold: 0,
      status: 'MEDIUM-LOW',
      impact: -0.08,
    },
    {
      factor: 'Industry Competition',
      value: 0.68,
      threshold: 0.75,
      status: 'MEDIUM',
      impact: -0.12,
    },
  ]

  const positiveDrivers = [
    {
      factor: 'Revenue Growth',
      value: 0.32,
      benchmark: 0.15,
      status: 'STRONG',
      impact: 0.25,
    },
    {
      factor: 'EBITDA Margin',
      value: 0.185,
      benchmark: 0.12,
      status: 'STRONG',
      impact: 0.20,
    },
    {
      factor: 'Interest Coverage',
      value: 4.5,
      benchmark: 3.0,
      status: 'HEALTHY',
      impact: 0.22,
    },
  ]

  const featureContribution = [
    { feature: 'Debt-to-Equity', contribution: -12, pct: '-15%' },
    { feature: 'Interest Coverage', contribution: 18, pct: '+22%' },
    { feature: 'Revenue Growth', contribution: 20, pct: '+25%' },
    { feature: 'EBITDA Margin', contribution: 16, pct: '+20%' },
    { feature: 'Current Ratio', contribution: 15, pct: '+18%' },
    { feature: 'Management Quality', contribution: 12, pct: '+15%' },
  ]

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <div>
          <h2 className="text-3xl font-bold text-gray-900">{selectedCompany.name}</h2>
          <p className="text-gray-600 mt-2">Comprehensive Risk Assessment & Scoring</p>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard label="PD Score" value={(selectedCompany.pd * 100).toFixed(2)} unit="%" color="orange" />
          <StatCard label="Credit Grade" value={selectedCompany.grade} color="blue" />
          <StatCard label="Loan Limit" value={`₹${selectedCompany.loanLimit}`} unit="Cr" color="green" />
          <StatCard label="Interest Rate" value={(selectedCompany.rate * 100).toFixed(2)} unit="%" color="blue" />
        </div>

        {/* Alerts */}
        <div className="space-y-4">
          <Alert
            type="info"
            title="Model Information"
            message="Based on XGBoost ensemble with SHAP explainability. Model accuracy: 87%, AUC score: 0.92"
          />
        </div>

        {/* SHAP Feature Contribution */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-6">SHAP Feature Contributions</h3>
          <div className="space-y-4">
            {featureContribution.map((item) => (
              <div key={item.feature} className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="font-medium text-gray-900">{item.feature}</span>
                  <span className={`font-bold ${item.contribution > 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {item.contribution > 0 ? '+' : ''}{item.contribution} ({item.pct})
                  </span>
                </div>
                <div className="w-full flex gap-2">
                  <div className="flex-1 bg-gray-200 rounded-full h-3 overflow-hidden">
                    <div
                      className={`h-full ${item.contribution > 0 ? 'bg-green-500' : 'bg-red-500'}`}
                      style={{ width: `${Math.abs(item.contribution)}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Risk Drivers vs Positive Drivers */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Risk Drivers */}
          <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <AlertCircle className="text-red-600" size={20} />
              Risk Drivers
            </h3>
            <div className="space-y-4">
              {riskDrivers.map((driver) => (
                <div key={driver.factor} className="border-l-4 border-red-500 pl-4 py-2">
                  <p className="font-medium text-gray-900">{driver.factor}</p>
                  <p className="text-sm text-gray-600">Current: {driver.value} | Threshold: {driver.threshold}</p>
                  <div className="flex justify-between items-center mt-2">
                    <Badge label={driver.status} type="warning" />
                    <span className="text-xs font-bold text-red-600">-{(Math.abs(driver.impact) * 100).toFixed(0)}% impact</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Positive Drivers */}
          <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <TrendingUp className="text-green-600" size={20} />
              Positive Drivers
            </h3>
            <div className="space-y-4">
              {positiveDrivers.map((driver) => (
                <div key={driver.factor} className="border-l-4 border-green-500 pl-4 py-2">
                  <p className="font-medium text-gray-900">{driver.factor}</p>
                  <p className="text-sm text-gray-600">Current: {driver.value} | Benchmark: {driver.benchmark}</p>
                  <div className="flex justify-between items-center mt-2">
                    <Badge label={driver.status} type="success" />
                    <span className="text-xs font-bold text-green-600">+{(driver.impact * 100).toFixed(0)}% impact</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Detailed Risk Assessment */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Risk Assessment Summary</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              {
                title: 'Financial Risk',
                components: ['Debt Levels', 'Profitability', 'Liquidity', 'Cash Flows'],
                score: 7.2,
              },
              {
                title: 'Operational Risk',
                components: ['Management Quality', 'Customer Concentration', 'Supplier Risk'],
                score: 7.8,
              },
              {
                title: 'Market Risk',
                components: ['Industry Growth', 'Competition', 'Regulatory Environment'],
                score: 6.8,
              },
            ].map((risk) => (
              <div
                key={risk.title}
                className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4"
              >
                <h4 className="font-semibold text-gray-900 mb-3">{risk.title}</h4>
                <ul className="space-y-2 mb-4">
                  {risk.components.map((comp) => (
                    <li key={comp} className="text-sm text-gray-700">
                      ✓ {comp}
                    </li>
                  ))}
                </ul>
                <div className="flex items-end gap-2">
                  <span className="text-2xl font-bold text-blue-600">{risk.score}</span>
                  <span className="text-xs text-gray-600">/10</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Model Details */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Model Information</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'Model Type', value: 'XGBoost Ensemble' },
              { label: 'Training Samples', value: '45,000' },
              { label: 'Model Accuracy', value: '87%' },
              { label: 'AUC Score', value: '0.92' },
              { label: 'Calibration', value: 'EXCELLENT' },
              { label: 'Features Used', value: '42' },
              { label: 'Last Validation', value: '2024-02-28' },
              { label: 'Version', value: 'v2.1.0' },
            ].map((item) => (
              <div key={item.label} className="bg-slate-50 rounded-lg p-4">
                <p className="text-xs text-gray-600 mb-1">{item.label}</p>
                <p className="font-semibold text-gray-900">{item.value}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Recommendations */}
        <div className="bg-blue-50 border-l-4 border-blue-500 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-3">Recommendation</h3>
          <p className="text-blue-800 mb-4">
            APPROVE credit facility with recommended terms: ₹15.50 Cr @ 11.75% for 60 months
          </p>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            <button className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors">
              Generate CAM
            </button>
            <button className="bg-white hover:bg-gray-50 border border-blue-600 text-blue-600 font-semibold py-2 px-4 rounded-lg transition-all">
              Download Report
            </button>
            <button className="bg-white hover:bg-gray-50 border border-blue-600 text-blue-600 font-semibold py-2 px-4 rounded-lg transition-all">
              View Details
            </button>
          </div>
        </div>
      </div>
    </Layout>
  )
}
