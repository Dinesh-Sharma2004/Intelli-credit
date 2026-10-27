import React, { createContext, useContext, useEffect, useState } from 'react'
import {
  type ApplicationDraft,
  type ApplicationSnapshot,
  type OfficerInput,
  createApplication,
  getApplication,
  runDecision,
} from '@/lib/intelliCreditApi'

interface CreditApplicationContextValue {
  applicationDraft: ApplicationDraft
  officerInput: OfficerInput
  applicationId: number | null
  snapshot: ApplicationSnapshot | null
  isLoading: boolean
  error: string | null
  setApplicationDraft: (patch: Partial<ApplicationDraft>) => void
  setOfficerInput: (patch: Partial<OfficerInput>) => void
  ensureApplication: () => Promise<number>
  refreshSnapshot: (nextApplicationId?: number) => Promise<void>
  ingestCompleted: (nextApplicationId?: number) => Promise<void>
  runDecisioning: () => Promise<void>
  clearError: () => void
}

const defaultApplicationDraft: ApplicationDraft = {
  borrower_name: '',
  borrower_pan: '',
  borrower_gstin: '',
  cin: '',
  sector: '',
  requested_amount: 0,
  requested_tenor_months: 12,
  notes: '',
}

const defaultOfficerInput: OfficerInput = {
  capacity_utilization_pct: 75,
  governance_score: 0.7,
  management_quality: 8,
  inventory_observation: 7,
  customer_concentration: 35,
  notes: '',
}

const CreditApplicationContext = createContext<CreditApplicationContextValue | undefined>(undefined)

function readStorage<T>(key: string, fallback: T): T {
  if (typeof window === 'undefined') return fallback
  try {
    const raw = window.localStorage.getItem(key)
    return raw ? (JSON.parse(raw) as T) : fallback
  } catch {
    return fallback
  }
}

export function CreditApplicationProvider({ children }: { children: React.ReactNode }) {
  const [applicationDraft, setApplicationDraftState] = useState<ApplicationDraft>(defaultApplicationDraft)
  const [officerInput, setOfficerInputState] = useState<OfficerInput>(defaultOfficerInput)
  const [applicationId, setApplicationId] = useState<number | null>(null)
  const [snapshot, setSnapshot] = useState<ApplicationSnapshot | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  // Persist only after the initial read; otherwise the first render (run twice under
  // StrictMode) overwrites the stored application id with null before it is read.
  const [hasHydrated, setHasHydrated] = useState(false)

  useEffect(() => {
    setApplicationDraftState(readStorage('intelli-credit-application-draft', defaultApplicationDraft))
    setOfficerInputState(readStorage('intelli-credit-officer-input', defaultOfficerInput))
    setApplicationId(readStorage<number | null>('intelli-credit-application-id', null))
    setHasHydrated(true)
  }, [])

  useEffect(() => {
    if (hasHydrated) {
      window.localStorage.setItem('intelli-credit-application-draft', JSON.stringify(applicationDraft))
    }
  }, [applicationDraft, hasHydrated])

  useEffect(() => {
    if (hasHydrated) {
      window.localStorage.setItem('intelli-credit-officer-input', JSON.stringify(officerInput))
    }
  }, [officerInput, hasHydrated])

  useEffect(() => {
    if (hasHydrated) {
      window.localStorage.setItem('intelli-credit-application-id', JSON.stringify(applicationId))
    }
  }, [applicationId, hasHydrated])

  useEffect(() => {
    if (applicationId) {
      refreshSnapshot()
    }
  }, [applicationId])

  const setApplicationDraft = (patch: Partial<ApplicationDraft>) => {
    setApplicationDraftState((current) => ({ ...current, ...patch }))
  }

  const setOfficerInput = (patch: Partial<OfficerInput>) => {
    setOfficerInputState((current) => ({ ...current, ...patch }))
  }

  const ensureApplication = async (): Promise<number> => {
    if (applicationId) return applicationId
    if (!applicationDraft.borrower_name.trim()) {
      const validationError = 'Enter borrower details before uploading documents.'
      setError(validationError)
      throw new Error(validationError)
    }

    setIsLoading(true)
    setError(null)
    try {
      const created = await createApplication(applicationDraft)
      setApplicationId(created.id)
      return created.id
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create application'
      setError(message)
      throw err
    } finally {
      setIsLoading(false)
    }
  }

  const refreshSnapshot = async (nextApplicationId?: number) => {
    const targetApplicationId = nextApplicationId ?? applicationId
    if (!targetApplicationId) return
    setIsLoading(true)
    setError(null)
    try {
      const nextSnapshot = await getApplication(targetApplicationId)
      setSnapshot(nextSnapshot)
      setApplicationDraftState({
        borrower_name: nextSnapshot.application.borrower_name,
        borrower_pan: nextSnapshot.application.borrower_pan,
        borrower_gstin: nextSnapshot.application.borrower_gstin,
        cin: nextSnapshot.application.cin,
        sector: nextSnapshot.application.sector,
        requested_amount: nextSnapshot.application.requested_amount,
        requested_tenor_months: nextSnapshot.application.requested_tenor_months,
        notes: nextSnapshot.application.notes,
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load application'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }

  const ingestCompleted = async (nextApplicationId?: number) => {
    await refreshSnapshot(nextApplicationId)
  }

  const runDecisioning = async () => {
    const ensuredId = await ensureApplication()
    setIsLoading(true)
    setError(null)
    try {
      await runDecision(ensuredId, officerInput)
      const nextSnapshot = await getApplication(ensuredId)
      setSnapshot(nextSnapshot)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to run decisioning'
      setError(message)
      throw err
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <CreditApplicationContext.Provider
      value={{
        applicationDraft,
        officerInput,
        applicationId,
        snapshot,
        isLoading,
        error,
        setApplicationDraft,
        setOfficerInput,
        ensureApplication,
        refreshSnapshot,
        ingestCompleted,
        runDecisioning,
        clearError: () => setError(null),
      }}
    >
      {children}
    </CreditApplicationContext.Provider>
  )
}

export function useCreditApplication() {
  const context = useContext(CreditApplicationContext)
  if (!context) {
    throw new Error('useCreditApplication must be used within CreditApplicationProvider')
  }
  return context
}
