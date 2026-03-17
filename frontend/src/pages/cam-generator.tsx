import React, { useState } from 'react'
import { Layout } from '@/components/Layout'
import { StatCard, Badge, Alert } from '@/components/UI'
import { FileText, Download, Eye } from 'lucide-react'
import { useDocumentDownload } from '@/hooks/useDocumentDownload'

interface GeneratedCAM {
  id: string
  filename: string
  status: string
  timestamp: string
  file_url: string
}

export default function CAMGeneratorPage() {
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [generatedCAM, setGeneratedCAM] = useState<GeneratedCAM | null>(null)
  const { downloadFromAPI, isDownloading } = useDocumentDownload()

  const handleGenerateCAM = async () => {
    setIsGenerating(true)
    setError(null)
    
    try {
      // Prepare request data
      const requestData = {
        borrower_profile: {
          company_name: "TechVenture Solutions",
          cin: "U72900GJ2005PLC047584",
          sector: "Information Technology",
          years_in_operation: 18,
          revenue: 245.67e7,
          employees: 450
        },
        financial_summary: {
          revenue: 245.67e7,
          ebitda: 45.35e7,
          net_profit: 28.90e7,
          total_debt: 150e7,
          cash_reserves: 38.50e7
        },
        risk_assessment: {
          debt_to_equity: 1.58,
          interest_coverage: 4.82,
          litigation_exposure: "MEDIUM"
        },
        credit_score: 6.5,
        loan_limit: 15.50e7,
        interest_rate: 0.1175,
        shap_drivers: [
          { feature: "Debt-to-Equity", contribution: -0.35 },
          { feature: "Litigation", contribution: -0.15 },
          { feature: "Revenue Growth", contribution: 0.28 }
        ]
      }

      console.log('Generating CAM with data:', requestData)

      const response = await fetch('http://localhost:8000/api/cam/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      })

      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`)
      }

      const data = await response.json()
      console.log('CAM generated:', data)

      setGeneratedCAM({
        id: data.cam_id,
        filename: data.filename,
        status: data.status,
        timestamp: new Date(data.generation_time).toLocaleString(),
        file_url: data.file_url
      })
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to generate CAM'
      setError(errorMsg)
      console.error('CAM generation error:', err)
    } finally {
      setIsGenerating(false)
    }
  }

  const handleDownload = async () => {
    if (!generatedCAM) return
    
    try {
      await downloadFromAPI(
        generatedCAM.file_url,
        generatedCAM.filename,
        {
          onSuccess: () => {
            console.log(`Successfully downloaded: ${generatedCAM.filename}`)
          },
          onError: (error) => {
            setError(`Download failed: ${error.message}`)
          }
        }
      )
    } catch (err) {
      console.error('Download error:', err)
      setError(err instanceof Error ? err.message : 'Download failed')
    }
  }

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <div>
          <h2 className="text-3xl font-bold text-gray-900">CAM Generator</h2>
          <p className="text-gray-600 mt-2">Generate professional Credit Appraisal Memorandum documents</p>
        </div>

        {/* Status */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <StatCard label="CAMs Generated" value="12" color="blue" icon={<FileText />} />
          <StatCard label="Latest CAM" value="March 4, 2024" color="green" icon={<FileText />} />
          <StatCard label="Avg. Generation Time" value="45" unit="sec" color="orange" icon={<FileText />} />
        </div>

        {/* Generation Status */}
        {error && (
          <Alert
            type="error"
            title="Error"
            message={error}
          />
        )}
        {generatedCAM ? (
          <Alert
            type="success"
            title="CAM Generated Successfully"
            message={`Document ${generatedCAM.filename} is ready for download`}
          />
        ) : (
          <Alert
            type="info"
            title="Ready to Generate"
            message="All required data is available. Click the button below to generate the CAM document."
          />
        )}

        {/* CAM Template Preview */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-6">CAM Document Sections</h3>
          <div className="space-y-3">
            {[
              { num: 1, title: 'Borrower Profile', fields: ['Company Name', 'CIN', 'Sector', 'Years in Operation'] },
              { num: 2, title: 'Financial Analysis', fields: ['Revenue', 'EBITDA', 'Debt', 'Cash Reserves', 'Key Ratios'] },
              { num: 3, title: 'Industry & Sector Analysis', fields: ['Market Overview', 'Competitive Position', 'Sector Risks'] },
              { num: 4, title: 'Five Cs of Credit', fields: ['Character', 'Capacity', 'Capital', 'Collateral', 'Covenants'] },
              { num: 5, title: 'Risk Assessment', fields: ['Risk Factors', 'Severity', 'Mitigation Strategies'] },
              { num: 6, title: 'Credit Scoring', fields: ['PD Score', 'Credit Grade', 'Loan Limit', 'Interest Rate'] },
              { num: 7, title: 'Final Recommendation', fields: ['Approval Status', 'Terms & Conditions', 'Covenants'] },
            ].map((section) => (
              <div key={section.num} className="border rounded-lg p-4 hover:border-blue-400 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex gap-4 flex-1">
                    <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                      <span className="font-bold text-blue-600">{section.num}</span>
                    </div>
                    <div className="flex-1">
                      <h4 className="font-semibold text-gray-900">{section.title}</h4>
                      <p className="text-sm text-gray-600 mt-1">
                        {section.fields.join(' • ')}
                      </p>
                    </div>
                  </div>
                  <Badge label="INCLUDED" type="success" />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Generation Controls */}
        <div className="relative overflow-hidden rounded-2xl p-8 text-white shadow-2xl group">
          {/* Animated Background Gradient */}
          <div className="absolute inset-0 bg-gradient-to-br from-blue-600 via-purple-600 to-blue-700 group-hover:from-blue-500 group-hover:via-purple-500 group-hover:to-blue-600 transition-all duration-500" />
          
          {/* Animated Orbs */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-blue-400 rounded-full mix-blend-multiply filter blur-2xl opacity-20 animate-blob" />
          <div className="absolute -bottom-8 left-20 w-64 h-64 bg-purple-400 rounded-full mix-blend-multiply filter blur-2xl opacity-20 animate-blob animation-delay-2000" />

          <div className="relative z-10">
            <h3 className="text-3xl font-bold mb-3">Generate Credit Appraisal Memorandum</h3>
            <p className="text-blue-100 mb-8 text-lg">
              Create a professional, comprehensive CAM document with AI-powered analysis
            </p>
            
            <button
              onClick={handleGenerateCAM}
              disabled={isGenerating}
              className={`relative group/btn px-8 py-4 rounded-xl font-bold text-lg overflow-hidden transition-all duration-300 transform ${
                isGenerating
                  ? 'opacity-75 cursor-not-allowed'
                  : 'hover:scale-105 hover:shadow-2xl active:scale-95'
              }`}
            >
              {/* Button Background */}
              <div className="absolute inset-0 bg-white rounded-xl transition-all duration-300" />
              
              {/* Shimmer Effect */}
              <div className="absolute inset-0 opacity-0 group-hover/btn:opacity-100 transition-opacity duration-300">
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent skew-x-12 animate-shimmer" />
              </div>
              
              {/* Text */}
              <span className="relative flex items-center justify-center gap-2 text-blue-600 font-bold">
                {isGenerating ? (
                  <>
                    <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Generating Document...
                  </>
                ) : (
                  <>
                    <FileText size={20} />
                    Generate CAM Document
                  </>
                )}
              </span>
            </button>
          </div>
        </div>

        {/* Generated Documents */}
        {generatedCAM && (
          <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Generated Documents</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center gap-3 flex-1">
                  <FileText className="text-green-600" size={24} />
                  <div>
                    <p className="font-semibold text-gray-900">{generatedCAM.filename}</p>
                    <p className="text-sm text-gray-600">{generatedCAM.timestamp}</p>
                  </div>
                </div>
                <div className="flex gap-3">
                  <button className="group/preview relative flex items-center gap-2 px-4 py-2 rounded-lg font-semibold overflow-hidden transition-all duration-300 transform hover:scale-105 active:scale-95">
                    {/* Background Gradient */}
                    <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-blue-600 group-hover/preview:from-blue-400 group-hover/preview:to-blue-500 transition-all" />
                    
                    {/* Shimmer */}
                    <div className="absolute inset-0 opacity-0 group-hover/preview:opacity-100">
                      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent skew-x-12 animate-shimmer" />
                    </div>
                    
                    <span className="relative text-white flex items-center gap-2">
                      <Eye size={16} />
                      Preview
                    </span>
                  </button>

                  <button
                    onClick={handleDownload}
                    disabled={isDownloading}
                    className="group/download relative flex items-center gap-2 px-4 py-2 rounded-lg font-semibold overflow-hidden transition-all duration-300 transform hover:scale-105 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {/* Background Gradient */}
                    <div className="absolute inset-0 bg-gradient-to-r from-green-500 to-emerald-600 group-hover/download:from-green-400 group-hover/download:to-emerald-500 transition-all" />
                    
                    {/* Shimmer */}
                    <div className="absolute inset-0 opacity-0 group-hover/download:opacity-100">
                      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent skew-x-12 animate-shimmer" />
                    </div>
                    
                    <span className="relative text-white flex items-center gap-2">
                      {isDownloading ? (
                        <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                      ) : (
                        <Download size={16} />
                      )}
                      {isDownloading ? 'Downloading...' : 'Download'}
                    </span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Output Formats */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Export Formats</h3>
          <div className="grid grid-cols-2 gap-4">
            {[
              { format: 'DOCX', desc: 'Microsoft Word document (.docx)', editable: 'Fully editable' },
              { format: 'PDF', desc: 'Portable document format (.pdf)', editable: 'Read-only' },
            ].map((fmt) => (
              <div key={fmt.format} className="border rounded-lg p-4 hover:border-blue-400 transition-colors">
                <p className="font-semibold text-gray-900">{fmt.format}</p>
                <p className="text-sm text-gray-600 mt-1">{fmt.desc}</p>
                <p className="text-xs text-gray-500 mt-2">{fmt.editable}</p>
              </div>
            ))}
          </div>
        </div>

        {/* CAM History */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">CAM History</h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Filename</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Generated</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Company</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Status</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Actions</th>
                </tr>
              </thead>
              <tbody>
                {[
                  { filename: 'CAM_TechVenture_20240304_143022.docx', generated: '2024-03-04 14:30', company: 'TechVenture Solutions', status: 'COMPLETED' },
                  { filename: 'CAM_CloudServices_20240303_101455.docx', generated: '2024-03-03 10:14', company: 'Cloud Services Inc', status: 'COMPLETED' },
                  { filename: 'CAM_FinTech_20240301_160230.docx', generated: '2024-03-01 16:02', company: 'FinTech Innovations', status: 'COMPLETED' },
                ].map((item, i) => (
                  <tr key={i} className={`border-b ${i % 2 === 0 ? 'bg-gray-50' : 'bg-white'} hover:bg-blue-50`}>
                    <td className="px-6 py-4 text-sm text-gray-900 font-medium">{item.filename}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">{item.generated}</td>
                    <td className="px-6 py-4 text-sm text-gray-900">{item.company}</td>
                    <td className="px-6 py-4">
                      <Badge label={item.status} type="success" />
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <div className="flex gap-2">
                        <button className="text-blue-600 hover:text-blue-700 font-medium">View</button>
                        <button className="text-green-600 hover:text-green-700 font-medium">Download</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </Layout>
  )
}
