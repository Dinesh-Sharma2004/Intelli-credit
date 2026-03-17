import React from 'react'
import { Layout } from '@/components/Layout'
import { StatCard, Table, Badge } from '@/components/UI'
import { Search, Briefcase, AlertCircle, TrendingUp } from 'lucide-react'

export default function ResearchAgent() {
  const [companyName, setCompanyName] = React.useState('TechVenture Solutions')

  const litigationCases = [
    ['CS-2023-001', 'TechVenture vs. Supplier XYZ', 'Delhi High Court', 'PENDING', '₹2.50 Cr', <Badge key="1" label="MEDIUM" type="warning" />],
    ['CS-2022-045', 'Employee vs. TechVenture', 'Industrial Tribunal', 'SETTLED', '₹15.00 Lk', <Badge key="2" label="LOW" type="success" />],
  ]

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <div>
          <h2 className="text-3xl font-bold theme-gradient-text">Research Agent (RAG)</h2>
          <p className="text-gray-600 dark:text-gray-300 mt-2">Comprehensive company research using web scraping, MCA data, and litigation search</p>
        </div>

        {/* Search */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm report-box advanced-hover cursor-zoom-card">
          <div className="flex gap-3">
            <input
              type="text"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              placeholder="Enter company name"
              className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg focus:outline-none focus:border-brand-blue bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
            />
            <button className="bg-brand-blue hover:bg-blue-700 text-white font-semibold py-2 px-6 rounded-lg transition-all duration-300 flex items-center gap-2 advanced-hover cursor-pointer-advanced">
              <Search size={18} />
              Research
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard label="Web Sources" value="342" color="blue" icon={<Briefcase />} />
          <StatCard label="Litigation Cases" value="2" color="orange" icon={<AlertCircle />} />
          <StatCard label="Credit Score" value="75" color="green" icon={<TrendingUp />} />
          <StatCard label="Data Sources" value="5" color="blue" />
        </div>

        {/* MCA Data */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm report-box advanced-hover cursor-zoom-card">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">MCA Company Registration</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'CIN', value: 'U72900GJ2005PLC047584' },
              { label: 'Registration Date', value: '2005-03-15' },
              { label: 'Status', value: 'ACTIVE' },
              { label: 'Authorized Capital', value: '₹10.00 Cr' },
              { label: 'Paid-up Capital', value: '₹8.50 Cr' },
              { label: 'Filing Status', value: 'COMPLIANT' },
              { label: 'Last Annual Filing', value: '2024-02-28' },
              { label: 'Directors', value: '2 (Both Active)' },
            ].map((item) => (
              <div key={item.label} className="border dark:border-gray-700 rounded-lg p-3 hover:border-blue-400 dark:hover:border-blue-500 transition-all duration-300 advanced-hover cursor-focus">
                <p className="text-xs text-gray-600 dark:text-gray-300 mb-1">{item.label}</p>
                <p className="font-semibold text-gray-900 dark:text-gray-100 text-sm">{item.value}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Web Research Results */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm report-box advanced-hover cursor-zoom-card">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Web Research Results</h3>
          <div className="space-y-4">
            {[
              {
                source: 'Industry News',
                title: 'TechVenture Solutions Wins Major Contract in Q1 2024',
                excerpt: 'Leading cloud infrastructure provider has secured a major enterprise contract worth ₹50 Cr.',
                score: 0.92,
                url: 'https://news.example.com',
              },
              {
                source: 'Business Database',
                title: 'Financial Performance Analysis: TechVenture Solutions',
                excerpt: 'Reported strong financial performance with 32% revenue growth YoY and 18.5% operating margins.',
                score: 0.88,
                url: 'https://business.example.com',
              },
              {
                source: 'Sector Analysis',
                title: 'Cloud Services Sector Growth Trends 2024',
                excerpt: 'Industry projected to grow at 28% CAGR driven by digital transformation.',
                score: 0.85,
                url: 'https://sector.example.com',
              },
            ].map((item, i) => (
              <div key={i} className="border dark:border-gray-700 rounded-lg p-4 hover:border-blue-400 dark:hover:border-blue-500 transition-all duration-300 advanced-hover cursor-zoom-card">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <p className="text-xs font-semibold text-brand-blue uppercase">{item.source}</p>
                    <h4 className="font-semibold text-gray-900 dark:text-gray-100 mt-1">{item.title}</h4>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-bold text-blue-600">{(item.score * 100).toFixed(0)}%</p>
                    <p className="text-xs text-gray-600 dark:text-gray-300">Relevance</p>
                  </div>
                </div>
                <p className="text-sm text-gray-700 dark:text-gray-300 mb-3">{item.excerpt}</p>
                <a href={item.url} className="text-xs text-blue-600 hover:underline">
                  {item.url}
                </a>
              </div>
            ))}
          </div>
        </div>

        {/* Litigation Data */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm report-box advanced-hover cursor-zoom-card">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Litigation & Legal Cases</h3>
          <Table
            headers={['Case ID', 'Case Name', 'Court', 'Status', 'Amount', 'Risk Level']}
            rows={litigationCases}
          />
          <p className="text-sm text-gray-600 dark:text-gray-300 mt-4">
            Data source: e-Courts portal (eCourts.gov.in) | Last updated: 2024-03-04
          </p>
        </div>

        {/* Sector Analysis */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm report-box advanced-hover cursor-zoom-card">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Sector Analysis</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-3">Market Overview</h4>
              <ul className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
                <li>• <strong>Market Size:</strong> ₹45,000+ Cr</li>
                <li>• <strong>Growth Rate:</strong> 28% CAGR</li>
                <li>• <strong>Key Drivers:</strong> Digital transformation, Enterprise migration</li>
                <li>• <strong>Market Share:</strong> ~3.2% (Company position)</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-3">Key Opportunities & Risks</h4>
              <div className="space-y-2">
                <div className="bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-900/60 rounded p-2">
                  <p className="text-xs font-semibold text-green-700 dark:text-green-200">+28% Annual Growth</p>
                </div>
                <div className="bg-orange-50 dark:bg-orange-950/30 border border-orange-200 dark:border-orange-900/60 rounded p-2">
                  <p className="text-xs font-semibold text-orange-700 dark:text-orange-200">Competition from hyperscalers</p>
                </div>
                <div className="bg-orange-50 dark:bg-orange-950/30 border border-orange-200 dark:border-orange-900/60 rounded p-2">
                  <p className="text-xs font-semibold text-orange-700 dark:text-orange-200">Data residency regulations</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Risk Summary */}
        <div className="bg-blue-50 dark:bg-blue-950/30 border-l-4 border-blue-500 rounded-lg p-6 report-box advanced-hover cursor-zoom-card">
          <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-200 mb-3">Credit Worthiness Assessment</h3>
          <p className="text-blue-800 dark:text-blue-300 mb-4">
            Based on comprehensive research data from multiple sources including MCA registry, litigation databases, and industry research:
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            <div className="bg-white dark:bg-gray-900 rounded p-3 advanced-hover cursor-pointer-advanced">
              <p className="text-xs text-gray-600 dark:text-gray-300">Research Score</p>
              <p className="font-bold text-2xl text-blue-600">75/100</p>
            </div>
            <div className="bg-white dark:bg-gray-900 rounded p-3 advanced-hover cursor-pointer-advanced">
              <p className="text-xs text-gray-600 dark:text-gray-300">Litigation Risk</p>
              <p className="font-bold text-2xl text-orange-600">Medium-Low</p>
            </div>
            <div className="bg-white dark:bg-gray-900 rounded p-3 advanced-hover cursor-pointer-advanced">
              <p className="text-xs text-gray-600 dark:text-gray-300">Compliance Status</p>
              <p className="font-bold text-2xl text-green-600">Excellent</p>
            </div>
            <div className="bg-white dark:bg-gray-900 rounded p-3 advanced-hover cursor-pointer-advanced">
              <p className="text-xs text-gray-600 dark:text-gray-300">Industry Growth</p>
              <p className="font-bold text-2xl text-green-600">28% CAGR</p>
            </div>
          </div>
          <p className="text-sm text-blue-800 dark:text-blue-300">
            Recommendation: Research validates company's credibility. Combined with financial metrics, credit approval is recommended.
          </p>
        </div>
      </div>
    </Layout>
  )
}
