import { useState, useCallback } from 'react'
import { API_BASE_URL } from '@/lib/intelliCreditApi'

interface DownloadOptions {
  onSuccess?: () => void
  onError?: (error: Error) => void
}

export function useDocumentDownload() {
  const [isDownloading, setIsDownloading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const downloadFile = useCallback(
    async (
      url: string,
      filename: string,
      options?: DownloadOptions
    ) => {
      setIsDownloading(true)
      setError(null)

      try {
        console.log(`Downloading: ${filename} from ${url}`)

        const response = await fetch(url, {
          method: 'GET',
          headers: {
            'Accept': '*/*'
          }
        })

        if (!response.ok) {
          throw new Error(`HTTP Error: ${response.status} ${response.statusText}`)
        }

        const blob = await response.blob()
        console.log(`Blob size: ${blob.size} bytes`)

        // Create a temporary URL for the blob
        const objectUrl = URL.createObjectURL(blob)
        
        // Create an anchor element and trigger click
        const link = document.createElement('a')
        link.href = objectUrl
        link.download = filename
        link.style.display = 'none'

        // Try multiple approaches for different browsers
        try {
          // Modern approach
          document.body.appendChild(link)
          link.click()
          
          // Cleanup
          setTimeout(() => {
            document.body.removeChild(link)
            URL.revokeObjectURL(objectUrl)
          }, 100)
        } catch (err) {
          // Fallback for restrictive browsers
          console.log('Primary download method failed, trying alternative...')
          
          // Window.open fallback
          if (blob.type) {
            const blobUrl = URL.createObjectURL(blob)
            window.open(blobUrl, '_blank')
            setTimeout(() => URL.revokeObjectURL(blobUrl), 1000)
          }
        }

        options?.onSuccess?.()
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Download failed')
        setError(error.message)
        console.error('Download error:', error)
        options?.onError?.(error)
      } finally {
        setIsDownloading(false)
      }
    },
    []
  )

  const downloadFromAPI = useCallback(
    async (
      endpoint: string,
      filename: string,
      options?: DownloadOptions
    ) => {
      const apiUrl = endpoint.startsWith('http')
        ? endpoint
        : `${API_BASE_URL.replace('/api/v1', '')}${endpoint}`
      
      await downloadFile(apiUrl, filename, options)
    },
    [downloadFile]
  )

  return {
    downloadFile,
    downloadFromAPI,
    isDownloading,
    error
  }
}
