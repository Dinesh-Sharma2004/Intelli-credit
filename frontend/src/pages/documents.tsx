import React, { useEffect, useState } from 'react'
import { Layout } from '@/components/Layout'
import { Table, Badge, Alert } from '@/components/UI'
import { Upload, FileText, AlertCircle, Loader, Download } from 'lucide-react'
import { useDocumentUpload } from '@/hooks/useDocumentUpload'
import { useCreditApplication } from '@/context/CreditApplicationContext'

export default function DocumentUpload() {
  const { uploadMultipleFiles, isUploading, uploadProgress, error, uploadedDocuments, clearError } = useDocumentUpload()
  const { applicationDraft, setApplicationDraft, applicationId, snapshot } = useCreditApplication()
  const [dragActive, setDragActive] = useState(false)
  const [localError, setLocalError] = useState<string | null>(null)

  useEffect(() => {
    clearError()
  }, [])

  const handleFileUpload = async (files: File[]) => {
    if (files.length === 0) return
    if (!applicationDraft.borrower_name.trim()) {
      setLocalError('Enter borrower details before uploading documents.')
      return
    }
    try {
      setLocalError(null)
      await uploadMultipleFiles(files)
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : 'Upload failed')
    }
  }

  const tableRows = uploadedDocuments.map((file) => [
    <div key={`${file.id}-name`} className="flex items-center gap-2">
      <FileText size={16} className="text-blue-600" />
      {file.name}
    </div>,
    file.type,
    `${(file.confidence || 0).toFixed(2)}`,
    <Badge key={`${file.id}-status`} label={file.status} type={file.status === 'PROCESSED' ? 'success' : 'warning'} />,
  ])

  return (
    <Layout>
      <div className="space-y-8">
        <div>
          <h2 className="text-3xl font-bold" style={{ color: 'var(--text-primary)' }}>Document Upload & Processing</h2>
          <p className="mt-2" style={{ color: 'var(--text-secondary)' }}>Upload borrower documents and let the backend classify and extract them.</p>
        </div>

        {(error || localError) && (
          <Alert
            type="error"
            title="Upload Error"
            message={localError || error || 'Upload failed'}
            icon={<AlertCircle size={16} />}
          />
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="rounded-lg border p-6 shadow-sm glass-effect" style={{ borderColor: 'var(--border-color)' }}>
            <h3 className="text-lg font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>Active Borrower</h3>
            <div className="space-y-4">
              <input
                value={applicationDraft.borrower_name}
                onChange={(e) => {
                  setLocalError(null)
                  setApplicationDraft({ borrower_name: e.target.value })
                }}
                placeholder="Borrower name"
                className="w-full px-4 py-3 border rounded-lg"
              />
              <input
                value={applicationDraft.sector}
                onChange={(e) => setApplicationDraft({ sector: e.target.value })}
                placeholder="Sector"
                className="w-full px-4 py-3 border rounded-lg"
              />
              <input
                type="number"
                value={applicationDraft.requested_amount || ''}
                onChange={(e) => setApplicationDraft({ requested_amount: Number(e.target.value) })}
                placeholder="Requested amount"
                className="w-full px-4 py-3 border rounded-lg"
              />
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                Application ID: {applicationId || 'Not created yet'}
              </p>
            </div>
          </div>

          <div className="rounded-lg border p-6 shadow-sm glass-effect" style={{ borderColor: 'var(--border-color)' }}>
            <h3 className="text-lg font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>Backend Processing Summary</h3>
            <div className="space-y-3">
              <p style={{ color: 'var(--text-secondary)' }}>Documents processed: {snapshot?.documents.length || 0}</p>
              <p style={{ color: 'var(--text-secondary)' }}>Risk flags detected: {(snapshot?.documents || []).reduce((sum, doc) => sum + doc.risk_flags.length, 0)}</p>
              <p style={{ color: 'var(--text-secondary)' }}>Research ready: {snapshot?.research_hits.length || 0} hits</p>
            </div>
          </div>
        </div>

        <div className="rounded-lg border p-8 shadow-sm glass-effect" style={{ borderColor: 'var(--border-color)' }}>
          <div
            className={`border-2 border-dashed rounded-lg p-12 text-center transition-all duration-200 ${dragActive ? 'border-blue-500' : ''}`}
            style={{ borderColor: dragActive ? 'rgb(59,130,246)' : 'var(--border-color)' }}
            onDragEnter={(e) => {
              e.preventDefault()
              setDragActive(true)
            }}
            onDragLeave={(e) => {
              e.preventDefault()
              setDragActive(false)
            }}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault()
              setDragActive(false)
              handleFileUpload(Array.from(e.dataTransfer.files))
            }}
          >
            {isUploading ? (
              <>
                <Loader className="mx-auto h-12 w-12 animate-spin" style={{ color: 'var(--brand-blue)' }} />
                <p className="mt-4 font-semibold" style={{ color: 'var(--text-primary)' }}>
                  Uploading to backend: {Math.round(uploadProgress)}%
                </p>
              </>
            ) : (
              <>
                <Upload className="mx-auto h-12 w-12 mb-4" style={{ color: 'var(--text-secondary)' }} />
                <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>Drop borrower files here</h3>
                <p className="mb-4" style={{ color: 'var(--text-secondary)' }}>PDF, CSV, JSON, and statement files are sent to the live backend.</p>
                <label className="cursor-pointer inline-block font-semibold py-2 px-6 rounded-lg" style={{ backgroundColor: 'var(--brand-blue)', color: 'white' }}>
                  Select Files
                  <input
                    type="file"
                    multiple
                    accept=".pdf,.csv,.json,.txt,.xlsx,.xls"
                    className="hidden"
                    onChange={(e) => handleFileUpload(Array.from(e.target.files || []))}
                  />
                </label>
              </>
            )}
          </div>
          {!applicationDraft.borrower_name.trim() && (
            <p className="text-sm mt-4" style={{ color: 'var(--text-secondary)' }}>
              Add the borrower name above before uploading files so the backend can create the application correctly.
            </p>
          )}
        </div>

        <div className="rounded-lg border p-6 shadow-sm glass-effect" style={{ borderColor: 'var(--border-color)' }}>
          <h3 className="text-lg font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>Live Uploaded Documents</h3>
          {uploadedDocuments.length > 0 ? (
            <Table headers={['File Name', 'Document Type', 'Confidence', 'Status']} rows={tableRows} />
          ) : (
            <p style={{ color: 'var(--text-secondary)' }}>No live documents yet.</p>
          )}
        </div>

        {snapshot?.documents && snapshot.documents.length > 0 && (
          <div className="rounded-lg border p-6 shadow-sm glass-effect" style={{ borderColor: 'var(--border-color)' }}>
            <h3 className="text-lg font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>Backend Risk Flags</h3>
            <div className="space-y-4">
              {snapshot.documents.map((doc) => (
                <div key={doc.id} className="rounded-lg p-4" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
                  <p className="font-semibold" style={{ color: 'var(--text-primary)' }}>{doc.document_name}</p>
                  <p className="text-sm mb-2" style={{ color: 'var(--text-secondary)' }}>{doc.document_type}</p>
                  {(doc.risk_flags.length > 0 ? doc.risk_flags : ['No explicit risk flags']).map((flag) => (
                    <div key={flag} className="text-sm" style={{ color: 'var(--text-secondary)' }}>• {flag}</div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        )}

        <button
          disabled={!snapshot?.documents?.length}
          onClick={() => {
            const rows = (snapshot?.documents || []).map((doc) => [
              doc.document_name,
              doc.document_type,
              doc.confidence_score.toFixed(2),
              doc.risk_flags.join('; '),
            ])
            const csv = [['Document Name', 'Document Type', 'Confidence', 'Risk Flags'], ...rows]
              .map((row) => row.map((cell) => `"${cell}"`).join(','))
              .join('\n')
            const blob = new Blob([csv], { type: 'text/csv' })
            const link = document.createElement('a')
            link.href = URL.createObjectURL(blob)
            link.download = 'document-processing-results.csv'
            link.click()
          }}
          className="flex items-center gap-2 font-semibold py-3 px-6 rounded-lg"
          style={{ backgroundColor: 'var(--brand-blue)', color: 'white', opacity: snapshot?.documents?.length ? 1 : 0.5 }}
        >
          <Download size={18} />
          Export Live Results
        </button>
      </div>
    </Layout>
  )
}
