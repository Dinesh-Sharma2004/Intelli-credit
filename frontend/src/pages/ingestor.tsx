import React from 'react'
import { Layout } from '@/components/Layout'
import { Table, Badge, StatCard } from '@/components/UI'
import { BarChart3, AlertTriangle, CheckCircle } from 'lucide-react'

export default function DataIngestorPage() {
  const gstrData = [
    ['April 2023', '₹15.45 Cr', '₹18.92 Cr', '22.5%', <Badge key="1" label="HIGH" type="warning" />],
    ['May 2023', '₹16.78 Cr', '₹17.45 Cr', '4.0%', <Badge key="2" label="LOW" type="success" />],
    ['June 2023', '₹17.34 Cr', '₹19.87 Cr', '14.6%', <Badge key="3" label="MEDIUM" type="warning" />],
    ['July 2023', '₹18.92 Cr', '₹20.34 Cr', '7.5%', <Badge key="4" label="LOW" type="success" />],
    ['August 2023', '₹19.56 Cr', '₹21.67 Cr', '10.8%', <Badge key="5" label="MEDIUM" type="warning" />],
    ['Sept 2023', '₹20.34 Cr', '₹22.45 Cr', '10.4%', <Badge key="6" label="MEDIUM" type="warning" />],
  ]

  const anomalies = [
    { type: 'Reversal Entries', count: 3, period: 'August 2023', severity: 'MEDIUM' },
    { type: 'Spike in Returns', count: 2, period: 'April 2023', severity: 'HIGH' },
    { type: 'Seasonal Variance', count: 1, period: 'Ongoing', severity: 'LOW' },
  ]

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <div>
          <h2 className="text-3xl font-bold theme-gradient-text">Data Ingestor & Extraction</h2>
          <p className="text-gray-600 dark:text-gray-300 mt-2">View extracted financial data, GST reconciliation, and anomaly detection</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard label="Documents Processed" value="127" color="blue" icon={<BarChart3 />} />
          <StatCard label="Extraction Accuracy" value="94.2" unit="%" color="green" />
          <StatCard label="Anomalies Detected" value="14" color="orange" icon={<AlertTriangle />} />
          <StatCard label="Data Quality" value="EXCELLENT" color="blue" />
        </div>

        {/* Extracted Financial Data */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm report-box advanced-hover cursor-zoom-card">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Extracted Financial Data (FY 2023-24)</h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 dark:bg-gray-800 border-b dark:border-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900 dark:text-gray-100">Metric</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900 dark:text-gray-100">Value</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900 dark:text-gray-100">Confidence</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900 dark:text-gray-100">Source</th>
                </tr>
              </thead>
              <tbody>
                {[
                  { metric: 'Total Revenue', value: '₹245.67 Cr', confidence: '97%', source: 'Financial Statements' },
                  { metric: 'EBITDA', value: '₹45.35 Cr', confidence: '94%', source: 'P&L Statement' },
                  { metric: 'Net Profit', value: '₹28.90 Cr', confidence: '96%', source: 'P&L Statement' },
                  { metric: 'Total Debt', value: '₹150.00 Cr', confidence: '98%', source: 'Balance Sheet' },
                  { metric: 'Cash Reserves', value: '₹38.50 Cr', confidence: '99%', source: 'Cash Flow' },
                  { metric: 'Current Assets', value: '₹95.60 Cr', confidence: '95%', source: 'Balance Sheet' },
                ].map((item, i) => (
                  <tr key={i} className={`border-b dark:border-gray-700 ${i % 2 === 0 ? 'bg-slate-50 dark:bg-gray-800' : 'bg-white dark:bg-gray-900'}`}>
                    <td className="px-6 py-4 text-sm font-medium text-gray-900 dark:text-gray-100">{item.metric}</td>
                    <td className="px-6 py-4 text-sm text-gray-900 dark:text-gray-100 font-semibold">{item.value}</td>
                    <td className="px-6 py-4 text-sm text-gray-700 dark:text-gray-300">{item.confidence}</td>
                    <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-300">{item.source}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* GST Reconciliation */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm report-box advanced-hover cursor-zoom-card">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">GST Reconciliation (GSTR-2A vs GSTR-3B)</h3>
          <Table
            headers={['Period', 'GSTR-2A (Purchases)', 'GSTR-3B (Sales)', 'Variance %', 'Risk Level']}
            rows={gstrData}
          />
          <div className="mt-4 p-4 bg-orange-50 dark:bg-orange-950/30 border border-orange-200 dark:border-orange-900/60 rounded-lg">
            <p className="text-sm text-orange-900 dark:text-orange-200">
              <strong>Alert:</strong> High variances detected in April, June, and August 2023. Recommend detailed review of GST filings.
            </p>
          </div>
        </div>

        {/* Anomaly Detection */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm report-box advanced-hover cursor-zoom-card">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Anomaly Detection Results</h3>
          <div className="space-y-3">
            {anomalies.map((anomaly, i) => (
              <div key={i} className="border dark:border-gray-700 rounded-lg p-4 hover:border-blue-400 dark:hover:border-blue-500 transition-all duration-300 advanced-hover cursor-focus">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-semibold text-gray-900 dark:text-gray-100">{anomaly.type}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                      Detected: {anomaly.count} instance{anomaly.count > 1 ? 's' : ''} • Period: {anomaly.period}
                    </p>
                  </div>
                  <Badge
                    label={anomaly.severity}
                    type={anomaly.severity === 'HIGH' ? 'error' : anomaly.severity === 'MEDIUM' ? 'warning' : 'success'}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Extracted Entities */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm report-box advanced-hover cursor-zoom-card">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Named Entity Extraction</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              {
                type: 'Company Information',
                entities: [
                  'Company: TechVenture Solutions Pvt Ltd',
                  'CIN: U72900GJ2005PLC047584',
                  'GST ID: 36AABCT1234A1Z0',
                ],
              },
              {
                type: 'Bank Details',
                entities: [
                  'Bank Name: HDFC Bank',
                  'Account: 50200071234567',
                  'IFSC: HDFC0000123',
                ],
              },
              {
                type: 'Key Persons',
                entities: ['Rajesh Kumar (MD)', 'Priya Sharma (CFO)', 'Amit Patel (COO)'],
              },
              {
                type: 'Locations',
                entities: ['HQ: Hyderabad', 'Regional Offices: Mumbai, Bangalore', 'Factories: 2 (Gujarat)'],
              },
            ].map((section, i) => (
              <div key={i} className="bg-slate-50 dark:bg-gray-800 rounded-lg p-4 border border-slate-200 dark:border-gray-700 advanced-hover cursor-pointer-advanced">
                <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-3">{section.type}</h4>
                <ul className="space-y-2">
                  {section.entities.map((entity, j) => (
                    <li key={j} className="text-sm text-gray-700 dark:text-gray-300 flex items-start gap-2">
                      <CheckCircle size={16} className="text-green-600 flex-shrink-0 mt-0.5" />
                      {entity}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>

        {/* Data Quality Metrics */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm report-box advanced-hover cursor-zoom-card">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Data Quality Metrics</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { metric: 'OCR Accuracy', value: 94.5 },
              { metric: 'Entity Detection', value: 91.3 },
              { metric: 'Data Completeness', value: 97.8 },
              { metric: 'Anomaly Detection', value: 88.6 },
            ].map((item) => (
              <div key={item.metric} className="space-y-2 advanced-hover cursor-pointer-advanced">
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{item.metric}</p>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                  <div className="h-full rounded-full bg-brand-blue" style={{ width: `${item.value}%` }} />
                </div>
                <p className="text-sm font-bold text-brand-blue">{item.value}%</p>
              </div>
            ))}
          </div>
        </div>

        {/* Translation & Language Support */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm report-box advanced-hover cursor-zoom-card">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Language Support</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {['English', 'Hindi', 'Tamil', 'Telugu', 'Kannada', 'Malayalam', 'Gujarati', 'Marathi'].map((lang) => (
              <div key={lang} className="bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-900/60 rounded-lg p-3 text-center advanced-hover cursor-pointer-advanced">
                <p className="text-sm font-semibold text-blue-900 dark:text-blue-200">{lang}</p>
                <p className="text-xs text-blue-700 dark:text-blue-300">Supported</p>
              </div>
            ))}
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-300 mt-4">
            All documents are translated to English using MarianMT for consistent processing.
          </p>
        </div>
      </div>
    </Layout>
  )
}
