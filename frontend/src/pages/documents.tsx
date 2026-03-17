import React, { useState } from 'react'
import { Layout } from '@/components/Layout'
import { StatCard, Table, Badge } from '@/components/UI'
import { Upload, FileText, CheckCircle } from 'lucide-react'

export default function DocumentUpload() {
  const [uploadedFiles, _setUploadedFiles] = useState([
    {
      id: 1,
      name: 'financial_statements_2024.pdf',
      type: 'Financial Statement',
      uploadTime: '2024-03-04 10:30',
      status: 'PROCESSED',
      confidence: 0.94,
    },
    {
      id: 2,
      name: 'gst_filing_2024.pdf',
      type: 'GST Filing',
      uploadTime: '2024-03-04 11:15',
      status: 'PROCESSED',
      confidence: 0.97,
    },
    {
      id: 3,
      name: 'bank_statement_march_2024.pdf',
      type: 'Bank Statement',
      uploadTime: '2024-03-04 12:00',
      status: 'PROCESSED',
      confidence: 0.91,
    },
  ])

  const [dragActive, setDragActive] = useState(false)

  const tableRows = uploadedFiles.map((file) => [
    <div key={`${file.id}-name`} className="flex items-center gap-2">
      <FileText size={16} className="text-blue-600" />
      {file.name}
    </div>,
    file.type,
    file.uploadTime,
    `${(file.confidence * 100).toFixed(1)}%`,
    <Badge key={`${file.id}-status`} label={file.status} type="success" />,
  ])

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header Info */}
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Document Upload & Processing</h2>
          <p className="text-gray-600 mt-2">Upload financial documents for OCR extraction and processing</p>
        </div>

        {/* Upload Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard label="Total Documents" value={uploadedFiles.length} color="blue" icon={<FileText />} />
          <StatCard
            label="Processed"
            value={uploadedFiles.filter((f) => f.status === 'PROCESSED').length}
            color="green"
            icon={<CheckCircle />}
          />
          <StatCard label="Avg Confidence" value={(0.94).toFixed(0)} unit="%" color="orange" />
          <StatCard label="Processing Time" value="2.3" unit="min" color="blue" />
        </div>

        {/* Upload Area */}
        <div className="bg-white rounded-lg border border-gray-200 p-8 shadow-sm">
          <div
            className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
              dragActive ? 'border-brand-blue bg-blue-50' : 'border-gray-300 hover:border-brand-blue'
            }`}
            onDragEnter={() => setDragActive(true)}
            onDragLeave={() => setDragActive(false)}
            onDrop={() => setDragActive(false)}
          >
            <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Drag and drop your documents</h3>
            <p className="text-gray-600 mb-4">or click to select files</p>
            <button className="bg-brand-blue hover:bg-blue-700 text-white font-semibold py-2 px-6 rounded-lg transition-colors">
              Select Files
            </button>
            <p className="text-sm text-gray-500 mt-4">
              Supported formats: PDF, Images (JPG, PNG), GST files, Bank statements
            </p>
          </div>
        </div>

        {/* Accepted File Types */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[
            { name: 'PDF Documents', icon: '📄', desc: 'Financial statements, bank statements' },
            { name: 'Images', icon: '🖼️', desc: 'Scanned documents, receipts' },
            { name: 'GST Filings', icon: '📊', desc: 'GSTR-1, 2A, 3B forms' },
            { name: 'Bank Statements', icon: '🏦', desc: 'Current account, savings account' },
          ].map((type) => (
            <div
              key={type.name}
              className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4"
            >
              <div className="text-3xl mb-2">{type.icon}</div>
              <h4 className="font-semibold text-gray-900">{type.name}</h4>
              <p className="text-sm text-gray-600 mt-1">{type.desc}</p>
            </div>
          ))}
        </div>

        {/* Recent Uploads */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Uploads</h3>
          <Table
            headers={['File Name', 'Document Type', 'Upload Time', 'Confidence', 'Status']}
            rows={tableRows}
          />
        </div>

        {/* Processing Pipeline */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-6">Document Processing Pipeline</h3>
          <div className="space-y-4">
            {[
              { step: 1, name: 'File Upload', status: 'Completed', time: '< 1 second' },
              { step: 2, name: 'OCR Extraction', status: 'Completed', time: '2.3 seconds' },
              { step: 3, name: 'Language Detection', status: 'Completed', time: '0.8 seconds' },
              { step: 4, name: 'Translation (if needed)', status: 'Completed', time: '3.1 seconds' },
              { step: 5, name: 'NER Extraction', status: 'Completed', time: '1.5 seconds' },
              { step: 6, name: 'Anomaly Detection', status: 'Completed', time: '0.9 seconds' },
            ].map((item) => (
              <div key={item.step} className="flex items-center gap-4 pb-4 border-b last:border-b-0">
                <div className="flex-shrink-0 w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                  <span className="text-green-700 font-bold">{item.step}</span>
                </div>
                <div className="flex-1">
                  <p className="font-medium text-gray-900">{item.name}</p>
                  <p className="text-sm text-gray-600">Processing time: {item.time}</p>
                </div>
                <Badge label={item.status} type="success" />
              </div>
            ))}
          </div>
        </div>

        {/* Extraction Quality */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-6">Extraction Quality Metrics</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[
              { metric: 'OCR Accuracy', value: 94.5, unit: '%' },
              { metric: 'Entity Recognition', value: 91.3, unit: '%' },
              { metric: 'Data Completeness', value: 97.8, unit: '%' },
              { metric: 'Anomaly Detection', value: 88.6, unit: '%' },
            ].map((item) => (
              <div key={item.metric} className="space-y-2">
                <div className="flex justify-between">
                  <p className="font-medium text-gray-900">{item.metric}</p>
                  <p className="font-bold text-brand-blue">{item.value}{item.unit}</p>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div className="h-full rounded-full bg-brand-blue" style={{ width: `${item.value}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4">
          <button className="flex-1 bg-brand-blue hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors">
            Process Selected Documents
          </button>
          <button className="flex-1 bg-white border border-gray-200 hover:border-brand-blue text-gray-900 font-semibold py-3 px-6 rounded-lg transition-all">
            View Extraction Details
          </button>
        </div>
      </div>
    </Layout>
  )
}
