import React from 'react'
import { Layout } from '@/components/Layout'
import { StatCard, Table, Badge, Alert } from '@/components/UI'
import { Search, Briefcase, AlertCircle, TrendingUp } from 'lucide-react'
import { useCreditApplication } from '@/context/CreditApplicationContext'

function severityType(severity: string) {
  if (severity === 'high') return 'error'
  if (severity === 'medium') return 'warning'
  return 'success'
}

export default function ResearchAgent() {
  const { snapshot, runDecisioning, isLoading, error } = useCreditApplication()

  if (!snapshot) {
    return (
      <Layout>
        <Alert
          type="info"
          title="No Research Yet"
          message="Upload documents and run backend decisioning to populate MCA, litigation, RBI, and news research."
        />
      </Layout>
    )
  }

  const companyName = snapshot.application.borrower_name
  const litigationCases = snapshot.research_hits
    .filter((item) => item.finding_type === 'litigation')
    .map((item, index) => [
      `LIT-${index + 1}`,
      item.title,
      item.source_name,
      item.severity.toUpperCase(),
      item.payload?.early_warning_signals?.join(', ') || 'N/A',
      <Badge key={item.title} label={item.severity.toUpperCase()} type={severityType(item.severity)} />,
    ])

  return (
    <Layout>
      <div className="space-y-8">
        <div>
          <h2 className="text-3xl font-bold theme-gradient-text">Research Agent</h2>
          <p className="mt-2" style={{ color: 'var(--text-secondary)' }}>
            Secondary research is populated from backend orchestration rather than predefined demo results.
          </p>
        </div>

        {error && <Alert type="warning" title="Backend Message" message={error} />}

        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm report-box">
          <div className="flex gap-3 items-center">
            <input
              type="text"
              value={companyName}
              readOnly
              className="flex-1 px-4 py-2 border rounded-lg"
              style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--bg-primary)', color: 'var(--text-primary)' }}
            />
            <button
              onClick={() => runDecisioning()}
              disabled={isLoading}
              className="font-semibold py-2 px-6 rounded-lg"
              style={{ backgroundColor: 'var(--brand-blue)', color: 'white' }}
            >
              <Search size={18} />
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard title="Research Hits" value={snapshot.research_hits.length} color="blue" icon={<Briefcase />} />
          <StatCard title="Litigation Findings" value={litigationCases.length} color="yellow" icon={<AlertCircle />} />
          <StatCard
            title="Compliance Checks"
            value={snapshot.compliance_checks.length}
            color="green"
            icon={<TrendingUp />}
          />
          <StatCard title="Data Sources" value={new Set(snapshot.research_hits.map((item) => item.source_name)).size} color="blue" />
        </div>

        <div className="rounded-lg border p-6 shadow-sm glass-effect" style={{ borderColor: 'var(--border-color)' }}>
          <h3 className="text-lg font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>Research Results</h3>
          <div className="space-y-4">
            {snapshot.research_hits.map((item) => (
              <div key={`${item.source_name}-${item.title}`} className="border rounded-lg p-4" style={{ borderColor: 'var(--border-color)' }}>
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <p className="text-xs font-semibold text-brand-blue uppercase">{item.source_name}</p>
                    <h4 className="font-semibold mt-1" style={{ color: 'var(--text-primary)' }}>{item.title}</h4>
                  </div>
                  <Badge label={item.severity.toUpperCase()} type={severityType(item.severity)} />
                </div>
                <p className="text-sm mb-3" style={{ color: 'var(--text-secondary)' }}>{item.summary}</p>
                <a href={item.source_url} target="_blank" rel="noreferrer" className="text-xs text-blue-600 hover:underline">
                  {item.source_url}
                </a>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-lg border p-6 shadow-sm glass-effect" style={{ borderColor: 'var(--border-color)' }}>
          <h3 className="text-lg font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>Litigation & Legal Signals</h3>
          {litigationCases.length > 0 ? (
            <Table headers={['Case ID', 'Title', 'Source', 'Severity', 'Signals', 'Risk']} rows={litigationCases} />
          ) : (
            <p style={{ color: 'var(--text-secondary)' }}>No litigation findings have been returned for this application yet.</p>
          )}
        </div>

        <div className="rounded-lg border p-6 shadow-sm glass-effect" style={{ borderColor: 'var(--border-color)' }}>
          <h3 className="text-lg font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>Compliance Mapping</h3>
          <Table
            headers={['Code', 'Regulation', 'Status', 'Evidence']}
            rows={snapshot.compliance_checks.map((item) => [
              item.regulation_code,
              item.regulation_name,
              <Badge key={item.regulation_code} label={item.status.toUpperCase()} type={item.status === 'evidence_mapped' ? 'success' : item.status === 'not_applicable' ? 'info' : 'warning'} />,
              item.evidence.join(', ') || 'Awaiting evidence',
            ])}
          />
        </div>
      </div>
    </Layout>
  )
}
