import React from 'react'
import { Layout } from '@/components/Layout'
import { StatCard, Badge, Alert, Table, AnomalyAlertPanel, CovenantSuggestionsSection, ResearchIntelligenceTimeline } from '@/components/UI'
import { FileText, Download } from 'lucide-react'
import { useDocumentDownload } from '@/hooks/useDocumentDownload'
import { useCreditApplication } from '@/context/CreditApplicationContext'

export default function CAMGeneratorPage() {
  const { snapshot, runDecisioning, isLoading, error } = useCreditApplication()
  const { downloadFile, isDownloading } = useDocumentDownload()

  const cam = snapshot?.cam_artifact
  const memo = cam?.memo_json

  const handleDownload = async (path: string) => {
    const filename = path.split(/[\\/]/).pop() || 'cam-output'
    await downloadFile(`http://127.0.0.1:5000/api/v1/cams/download?path=${encodeURIComponent(path)}`, filename)
  }

  return (
    <Layout>
      <div className="space-y-8">
        <div>
          <h2 className="text-3xl font-bold" style={{ color: 'var(--text-primary)' }}>CAM Generator</h2>
          <p className="mt-2" style={{ color: 'var(--text-secondary)' }}>Live CAM artifacts from backend decisioning</p>
        </div>

        {error && <Alert type="warning" title="Backend Message" message={error} />}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <StatCard title="CAM Status" value={cam?.generation_status || 'Pending'} color="blue" icon={<FileText />} />
          <StatCard title="Sections" value={memo ? Object.keys(memo).length : 0} color="green" icon={<FileText />} />
          <StatCard title="Decision" value={snapshot?.scorecard?.decision?.toUpperCase() || 'Pending'} color="yellow" icon={<FileText />} />
        </div>

        {!cam ? (
          <Alert
            type="info"
            title="No CAM Yet"
            message="Run backend decisioning to generate DOCX and PDF CAM artifacts."
          />
        ) : (
          <Alert
            type="success"
            title="CAM Ready"
            message={`Backend generated CAM for ${snapshot?.application.borrower_name}.`}
          />
        )}

        <div className="rounded-lg border p-6 shadow-sm glass-effect" style={{ borderColor: 'var(--border-color)' }}>
          <h3 className="text-lg font-semibold mb-6" style={{ color: 'var(--text-primary)' }}>Generation Controls</h3>
          <button
            onClick={() => runDecisioning()}
            disabled={isLoading}
            className="font-semibold py-3 px-6 rounded-lg"
            style={{ backgroundColor: 'var(--brand-blue)', color: 'white' }}
          >
            {isLoading ? 'Generating...' : 'Generate / Refresh CAM'}
          </button>
        </div>

        {cam && (
          <>
            <div className="rounded-lg border p-6 shadow-sm glass-effect" style={{ borderColor: 'var(--border-color)' }}>
              <h3 className="text-lg font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>Generated Artifacts</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-4 rounded-lg" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
                  <div>
                    <p className="font-semibold" style={{ color: 'var(--text-primary)' }}>DOCX CAM</p>
                    <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>{cam.docx_path}</p>
                  </div>
                  <button
                    onClick={() => handleDownload(cam.docx_path)}
                    disabled={isDownloading}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg"
                    style={{ backgroundColor: 'var(--brand-blue)', color: 'white' }}
                  >
                    <Download size={16} />
                    Download
                  </button>
                </div>
                <div className="flex items-center justify-between p-4 rounded-lg" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
                  <div>
                    <p className="font-semibold" style={{ color: 'var(--text-primary)' }}>PDF CAM</p>
                    <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>{cam.pdf_path}</p>
                  </div>
                  <button
                    onClick={() => handleDownload(cam.pdf_path)}
                    disabled={isDownloading}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg"
                    style={{ backgroundColor: 'var(--brand-blue)', color: 'white' }}
                  >
                    <Download size={16} />
                    Download
                  </button>
                </div>
              </div>
            </div>

            <div className="rounded-lg border p-6 shadow-sm glass-effect" style={{ borderColor: 'var(--border-color)' }}>
              <h3 className="text-lg font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>CAM Summary</h3>
              <Table
                headers={['Section', 'Value']}
                rows={[
                  ['Borrower', memo?.header?.borrower_name || 'N/A'],
                  ['Decision', memo?.executive_summary?.decision || 'N/A'],
                  ['Recommended Limit', memo?.executive_summary?.recommended_limit || 'N/A'],
                  ['Recommended Rate', memo?.executive_summary?.recommended_rate || 'N/A'],
                  ['Risk Grade', memo?.executive_summary?.risk_grade || 'N/A'],
                ]}
              />
            </div>

            <div className="rounded-lg border p-6 shadow-sm glass-effect" style={{ borderColor: 'var(--border-color)' }}>
              <h3 className="text-lg font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>Compliance Summary</h3>
              <div className="space-y-3">
                {(memo?.compliance_summary || []).map((item: any) => (
                  <div key={item.regulation_code} className="flex items-center justify-between p-3 rounded-lg" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
                    <div>
                      <p className="font-medium" style={{ color: 'var(--text-primary)' }}>{item.regulation_name}</p>
                      <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>{item.rationale}</p>
                    </div>
                    <Badge label={item.status} type={item.status === 'evidence_mapped' ? 'success' : 'warning'} />
                  </div>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <AnomalyAlertPanel title="Anomaly Summary" items={memo?.anomaly_summary?.anomaly_flags || []} />
              <AnomalyAlertPanel title="Monitoring Triggers" items={memo?.early_warning_summary?.early_warning_flags || []} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <CovenantSuggestionsSection items={memo?.covenant_recommendations || []} />
              <div className="rounded-lg border p-6 shadow-sm glass-effect" style={{ borderColor: 'var(--border-color)' }}>
                <h3 className="text-lg font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>Officer Insight Adjustment</h3>
                <p className="text-sm mb-3" style={{ color: 'var(--text-secondary)' }}>{memo?.qualitative_intelligence?.summary || 'No officer note summary available.'}</p>
                <Table
                  headers={['Signal', 'Value']}
                  rows={[
                    ['Sentiment', memo?.qualitative_intelligence?.sentiment_score?.toFixed?.(2) || '0.00'],
                    ['Utilization Detected', memo?.qualitative_intelligence?.utilization_pct_detected || 'N/A'],
                    ['Keywords', (memo?.qualitative_intelligence?.keywords_detected || []).join(', ') || 'None'],
                  ]}
                />
              </div>
            </div>

            <ResearchIntelligenceTimeline
              items={(memo?.research_summary || []).map((item: any) => ({
                title: `${item.source_name} - ${item.title}`,
                subtitle: item.summary,
                severity: item.severity,
              }))}
            />

            <div className="rounded-lg border p-6 shadow-sm glass-effect" style={{ borderColor: 'var(--border-color)' }}>
              <h3 className="text-lg font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>Transformer Explainability</h3>
              <p className="text-sm mb-4" style={{ color: 'var(--text-secondary)' }}>
                Method: {memo?.transformer_explainability?.method || 'N/A'} | Average evidence score: {memo?.transformer_explainability?.average_evidence_score || 0}
              </p>
              <div className="space-y-4">
                {(memo?.transformer_explainability?.driver_evidence || []).slice(0, 4).map((item: any) => (
                  <div key={item.label} className="rounded-lg border p-4" style={{ borderColor: 'var(--border-color)' }}>
                    <div className="flex items-center justify-between mb-2">
                      <p className="font-medium" style={{ color: 'var(--text-primary)' }}>{item.label}</p>
                      <Badge label={`${item.top_similarity}`} type="info" />
                    </div>
                    {(item.evidence || []).slice(0, 1).map((evidence: any) => (
                      <p key={`${item.label}-${evidence.chunk_index}`} className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                        {evidence.document_name}: {evidence.snippet}
                      </p>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </Layout>
  )
}
