import React from 'react'
import { Layout } from '@/components/Layout'
import { Table, StatCard, Alert, Badge } from '@/components/UI'
import { useCreditApplication } from '@/context/CreditApplicationContext'

function formatFactValue(value: any) {
  if (Array.isArray(value)) return value.join(', ') || 'N/A'
  if (value === null || value === undefined || value === '') return 'N/A'
  return String(value)
}

export default function DataIngestorPage() {
  const { snapshot } = useCreditApplication()

  if (!snapshot) {
    return (
      <Layout>
        <Alert type="info" title="No Ingestion Data" message="Upload documents to inspect extracted backend facts and processing confidence." />
      </Layout>
    )
  }

  const processedCount = snapshot.documents.filter((doc) => doc.processing_status === 'completed').length
  const avgConfidence = snapshot.documents.length
    ? (snapshot.documents.reduce((sum, doc) => sum + doc.confidence_score, 0) / snapshot.documents.length) * 100
    : 0

  const factRows = snapshot.documents.flatMap((doc) =>
    Object.entries(doc.structured_data || {}).slice(0, 5).map(([key, value]) => [
      doc.document_name,
      key,
      formatFactValue(value),
      `${(doc.confidence_score * 100).toFixed(1)}%`,
    ]),
  )

  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold" style={{ color: 'var(--text-primary)' }}>Data Ingestion & Processing</h1>
          <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>All values below are sourced from the current backend application snapshot.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard title="Total Documents" value={snapshot.documents.length} />
          <StatCard title="Processed" value={processedCount} color="green" />
          <StatCard title="Avg Confidence" value={`${avgConfidence.toFixed(1)}%`} color="blue" />
          <StatCard title="Compliance Checks" value={snapshot.compliance_checks.length} color="yellow" />
        </div>

        <div className="rounded-lg border p-6 shadow-sm glass-effect" style={{ borderColor: 'var(--border-color)' }}>
          <h2 className="text-xl font-bold mb-4" style={{ color: 'var(--text-primary)' }}>Documents</h2>
          <Table
            headers={['Document Name', 'Type', 'Confidence', 'Status', 'Flags']}
            rows={snapshot.documents.map((doc) => [
              doc.document_name,
              doc.document_type,
              `${(doc.confidence_score * 100).toFixed(1)}%`,
              <Badge key={`${doc.id}-status`} label={doc.processing_status.toUpperCase()} type="success" />,
              doc.risk_flags.join(', ') || 'None',
            ])}
          />
        </div>

        <div className="rounded-lg border p-6 shadow-sm glass-effect" style={{ borderColor: 'var(--border-color)' }}>
          <h3 className="text-lg font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>Extracted Structured Facts</h3>
          {factRows.length > 0 ? (
            <Table headers={['Document', 'Field', 'Value', 'Confidence']} rows={factRows} />
          ) : (
            <p style={{ color: 'var(--text-secondary)' }}>No structured facts extracted yet.</p>
          )}
        </div>
      </div>
    </Layout>
  )
}
