import { useState } from 'react'
import { useCreditApplication } from '@/context/CreditApplicationContext'
import { uploadDocuments } from '@/lib/intelliCreditApi'

export interface UploadedDocument {
  id: string
  name: string
  type: string
  uploadTime: string
  status: 'PROCESSING' | 'PROCESSED' | 'FAILED'
  confidence?: number
  pages_count?: number
  error?: string
}

interface IngestedDocument {
  id?: number | string
  document_name?: string
  document_type?: string
  processing_status?: string
  confidence_score?: number
  structured_data?: Record<string, any>
  error?: string
}

interface UploadOptions {
  language?: string
  onSuccess?: (doc: UploadedDocument) => void
  onError?: (error: Error) => void
  onProgress?: (progress: number) => void
}

function mapDocumentType(documentType: string) {
  return documentType
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase())
}

export function useDocumentUpload() {
  const { snapshot, ensureApplication, ingestCompleted } = useCreditApplication()
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const uploadedDocuments: UploadedDocument[] = (snapshot?.documents || []).map((doc) => ({
    id: String(doc.id),
    name: doc.document_name,
    type: mapDocumentType(doc.document_type),
    uploadTime: snapshot?.application?.external_id || '',
    status:
      doc.processing_status === 'completed'
        ? 'PROCESSED'
        : doc.processing_status === 'failed'
          ? 'FAILED'
          : 'PROCESSING',
    confidence: doc.confidence_score,
    pages_count: Number(doc.structured_data?.page_count || 1),
    error: doc.structured_data?.error || undefined,
  }))

  const mapResponseDocument = (doc: IngestedDocument, fallbackName: string): UploadedDocument => ({
    id: String(doc.id || fallbackName),
    name: doc.document_name || fallbackName,
    type: mapDocumentType(doc.document_type || 'generic_pdf'),
    uploadTime: new Date().toISOString(),
    status:
      doc.processing_status === 'completed'
        ? 'PROCESSED'
        : doc.processing_status === 'failed'
          ? 'FAILED'
          : 'PROCESSING',
    confidence: doc.confidence_score || 0,
    pages_count: Number(doc.structured_data?.page_count || 1),
    error: doc.error || (typeof doc.structured_data?.error === 'string' ? doc.structured_data.error : undefined),
  })

  const uploadFile = async (file: File, options?: UploadOptions) => {
    setIsUploading(true)
    setUploadProgress(0)
    setError(null)

    try {
      const applicationId = await ensureApplication()
      const response = await uploadDocuments(applicationId, [file], (progress) => {
        setUploadProgress(progress)
        options?.onProgress?.(progress)
      })
      await ingestCompleted(applicationId)
      const latest = mapResponseDocument(response?.documents?.[0] || {}, file.name)
      options?.onSuccess?.(latest)
      return latest
    } catch (err) {
      const nextError = err instanceof Error ? err.message : 'Upload failed'
      setError(nextError)
      options?.onError?.(err instanceof Error ? err : new Error(nextError))
      throw err
    } finally {
      setIsUploading(false)
      setUploadProgress(0)
    }
  }

  const uploadMultipleFiles = async (files: File[], options?: UploadOptions) => {
    setIsUploading(true)
    setUploadProgress(0)
    setError(null)

    try {
      const applicationId = await ensureApplication()
      const response = await uploadDocuments(applicationId, files, (progress) => {
        setUploadProgress(progress)
        options?.onProgress?.(progress)
      })
      await ingestCompleted(applicationId)
      const responseDocuments = Array.isArray(response?.documents) ? response.documents : []
      return files.map((file, index) => mapResponseDocument(responseDocuments[index] || {}, file.name))
    } catch (err) {
      const nextError = err instanceof Error ? err.message : 'Upload failed'
      setError(nextError)
      options?.onError?.(err instanceof Error ? err : new Error(nextError))
      throw err
    } finally {
      setIsUploading(false)
      setUploadProgress(0)
    }
  }

  const getDocuments = async () => uploadedDocuments

  return {
    uploadFile,
    uploadMultipleFiles,
    getDocuments,
    isUploading,
    uploadProgress,
    error,
    uploadedDocuments,
    clearError: () => setError(null),
    clearDocuments: () => undefined,
  }
}
