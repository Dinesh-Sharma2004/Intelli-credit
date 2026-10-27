import React from 'react'
import Link from 'next/link'
import { Layout } from '@/components/Layout'
import { PDScoreGauge } from '@/components/Gauges'
import { FeatureImportanceChart, FinancialRatioRadar, RevenueGrowthChart } from '@/components/Charts'
import { StatCard, Table, Badge, ProgressBar, Alert } from '@/components/UI'
import { useCreditApplication } from '@/context/CreditApplicationContext'

function formatCurrency(value: number) {
  return `₹${(value / 10000000).toFixed(2)}`
}

export default function Dashboard() {
  const { snapshot, error } = useCreditApplication()

  if (!snapshot) {
    return (
      <Layout>
        <Alert
          type="info"
          title="No Live Credit Case Yet"
          message="Create a borrower profile, upload documents, and run decisioning to populate the dashboard with real backend values."
        />
      </Layout>
    )
  }

  const { application, documents, scorecard, research_hits, compliance_checks } = snapshot
  const pd = scorecard?.probability_of_default || 0
  const featureImportanceData = (scorecard?.shap_explanation || []).map((item) => ({
    feature: item.feature,
    importance: Math.abs(item.contribution),
  }))

  const radarData = Object.entries(scorecard?.score_breakdown || {}).map(([metric, actual]) => ({
    metric: metric.charAt(0).toUpperCase() + metric.slice(1),
    actual: Number(actual) * 100,
    benchmark: 65,
  }))

  const revenueData = documents.slice(0, 4).map((doc, index) => ({
    period: `Doc ${index + 1}`,
    revenue: Number(doc.structured_data?.currency_amounts_detected?.length || 0) * 10,
    ebitda: Number(doc.confidence_score || 0) * 10,
  }))

  const riskFactorsTable = (scorecard?.shap_explanation || []).slice(0, 5).map((item) => [
    item.feature,
    item.contribution.toFixed(4),
    item.impact.replace(/_/g, ' '),
    <Badge
      key={item.feature}
      label={item.contribution > 0 ? 'NEGATIVE' : 'POSITIVE'}
      type={item.contribution > 0 ? 'warning' : 'success'}
    />,
  ])

  return (
    <Layout>
      <div className="space-y-8">
        {error && <Alert type="warning" title="Backend Message" message={error} />}

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <StatCard title="Borrower" value={application.borrower_name} color="blue" />
          <StatCard title="PD Score" value={`${(pd * 100).toFixed(2)}%`} color="green" />
          <StatCard title="Credit Grade" value={scorecard?.risk_grade || 'Pending'} color="blue" />
          <StatCard
            title="Recommended Limit"
            value={scorecard ? formatCurrency(scorecard.recommended_limit) : 'Pending'}
            unit="Cr"
            color="yellow"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="glass-effect rounded-xl p-6 shadow-lg">
            <h3 className="text-lg font-semibold theme-gradient-text mb-6">Probability of Default</h3>
            <div className="flex justify-center">
              <PDScoreGauge pd={pd} />
            </div>
          </div>

          <div className="glass-effect rounded-xl p-6 shadow-lg">
            <h3 className="text-lg font-semibold theme-gradient-text mb-4">Decision Summary</h3>
            <div className="space-y-3">
              <p style={{ color: 'var(--text-secondary)' }}>Decision</p>
              <p className="text-2xl font-bold text-brand-blue">{scorecard?.decision?.toUpperCase() || 'Pending'}</p>
              <p style={{ color: 'var(--text-secondary)' }}>Interest Rate</p>
              <p className="text-2xl font-bold text-brand-blue">
                {scorecard ? `${(scorecard.recommended_rate * 100).toFixed(2)}%` : 'Pending'}
              </p>
              <p style={{ color: 'var(--text-secondary)' }}>Tenor</p>
              <p className="text-xl font-bold text-brand-blue">{application.requested_tenor_months} months</p>
            </div>
          </div>

          <div className="glass-effect rounded-xl p-6 shadow-lg">
            <h3 className="text-lg font-semibold theme-gradient-text mb-4">Coverage</h3>
            <div className="space-y-4">
              <ProgressBar
                label="Document Coverage"
                value={Math.min(documents.length * 20, 100)}
                color="blue"
              />
              <ProgressBar
                label="Research Coverage"
                value={Math.min(research_hits.length * 25, 100)}
                color="green"
              />
              <ProgressBar
                label="Compliance Mapping"
                value={Math.min(compliance_checks.length * 20, 100)}
                color="yellow"
              />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="glass-effect rounded-xl p-6 shadow-lg">
            <h3 className="text-lg font-semibold theme-gradient-text mb-4">Feature Importance</h3>
            {featureImportanceData.length > 0 ? (
              <FeatureImportanceChart data={featureImportanceData} />
            ) : (
              <p style={{ color: 'var(--text-secondary)' }}>Run decisioning to see explainability.</p>
            )}
          </div>

          <div className="glass-effect rounded-xl p-6 shadow-lg">
            <h3 className="text-lg font-semibold theme-gradient-text mb-4">Five Cs Radar</h3>
            {radarData.length > 0 ? (
              <FinancialRatioRadar data={radarData} />
            ) : (
              <p style={{ color: 'var(--text-secondary)' }}>Five Cs scores will appear after backend scoring.</p>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="glass-effect rounded-xl p-6 shadow-lg">
            <h3 className="text-lg font-semibold theme-gradient-text mb-4">Document-Derived Trend</h3>
            {revenueData.length > 0 ? (
              <RevenueGrowthChart data={revenueData} />
            ) : (
              <p style={{ color: 'var(--text-secondary)' }}>Upload documents to populate trend visuals.</p>
            )}
          </div>

          <div className="glass-effect rounded-xl p-6 shadow-lg">
            <h3 className="text-lg font-semibold theme-gradient-text mb-4">Document Status</h3>
            <div className="space-y-3">
              {documents.length > 0 ? (
                documents.map((doc) => (
                  <div key={doc.id} className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span style={{ color: 'var(--text-primary)' }}>{doc.document_name}</span>
                      <Badge label={doc.processing_status.toUpperCase()} type="success" />
                    </div>
                    <ProgressBar value={doc.confidence_score * 100} label="Confidence" />
                  </div>
                ))
              ) : (
                <p style={{ color: 'var(--text-secondary)' }}>No uploaded documents yet.</p>
              )}
            </div>
          </div>
        </div>

        <div className="glass-effect rounded-xl p-6 shadow-lg">
          <h3 className="text-lg font-semibold theme-gradient-text mb-4">Top Model Drivers</h3>
          {riskFactorsTable.length > 0 ? (
            <Table headers={['Feature', 'Contribution', 'Impact', 'Direction']} rows={riskFactorsTable} />
          ) : (
            <p style={{ color: 'var(--text-secondary)' }}>No model drivers available until scoring completes.</p>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link href="/documents" className="glass-effect border font-semibold py-3 px-6 rounded-xl text-center" style={{ color: 'var(--text-primary)' }}>
            Upload Documents
          </Link>
          <Link href="/risk-scoring" className="glass-effect border font-semibold py-3 px-6 rounded-xl text-center" style={{ color: 'var(--text-primary)' }}>
            View Scoring
          </Link>
          <Link href="/cam-generator" className="bg-brand-blue text-white font-semibold py-3 px-6 rounded-xl text-center">
            Open CAM
          </Link>
        </div>
      </div>
    </Layout>
  )
}
