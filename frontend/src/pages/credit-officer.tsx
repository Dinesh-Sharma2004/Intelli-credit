import React from 'react'
import { Layout } from '@/components/Layout'
import { Badge, Alert } from '@/components/UI'
import { useCreditApplication } from '@/context/CreditApplicationContext'

type OfficerSliderKey =
  | 'capacity_utilization_pct'
  | 'management_quality'
  | 'inventory_observation'
  | 'customer_concentration'

interface OfficerSliderConfig {
  label: string
  key: OfficerSliderKey
  min: number
  max: number
  value: number
}

export default function CreditOfficerPortal() {
  const {
    applicationDraft,
    officerInput,
    setApplicationDraft,
    setOfficerInput,
    runDecisioning,
    isLoading,
    error,
  } = useCreditApplication()

  const qros =
    (officerInput.capacity_utilization_pct / 100) * 0.2 +
    (officerInput.management_quality / 10) * 0.25 +
    (officerInput.inventory_observation / 10) * 0.2 +
    ((100 - Math.min(officerInput.customer_concentration, 100)) / 100) * 0.15 +
    officerInput.governance_score * 0.2

  const sliderConfigs: OfficerSliderConfig[] = [
    {
      label: 'Factory Capacity Utilization (%)',
      key: 'capacity_utilization_pct',
      min: 0,
      max: 100,
      value: officerInput.capacity_utilization_pct,
    },
    {
      label: 'Management Quality (1-10)',
      key: 'management_quality',
      min: 1,
      max: 10,
      value: officerInput.management_quality,
    },
    {
      label: 'Inventory Quality (1-10)',
      key: 'inventory_observation',
      min: 1,
      max: 10,
      value: officerInput.inventory_observation,
    },
    {
      label: 'Top Customer Concentration (%)',
      key: 'customer_concentration',
      min: 0,
      max: 100,
      value: officerInput.customer_concentration,
    },
  ]

  return (
    <Layout>
      <div className="space-y-8">
        <div>
          <h2 className="text-3xl font-bold" style={{ color: 'var(--text-primary)' }}>Credit Officer Portal</h2>
          <p className="mt-2" style={{ color: 'var(--text-secondary)' }}>Maintain borrower inputs and qualitative overlays that feed backend scoring.</p>
        </div>

        {error && <Alert type="warning" title="Backend Message" message={error} />}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="rounded-lg border p-6 shadow-sm glass-effect" style={{ borderColor: 'var(--border-color)' }}>
            <h3 className="text-lg font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>Borrower Profile</h3>
            <div className="space-y-4">
              <input
                value={applicationDraft.borrower_name}
                onChange={(e) => setApplicationDraft({ borrower_name: e.target.value })}
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
                value={applicationDraft.cin}
                onChange={(e) => setApplicationDraft({ cin: e.target.value })}
                placeholder="CIN"
                className="w-full px-4 py-3 border rounded-lg"
              />
              <input
                value={applicationDraft.borrower_pan}
                onChange={(e) => setApplicationDraft({ borrower_pan: e.target.value })}
                placeholder="PAN"
                className="w-full px-4 py-3 border rounded-lg"
              />
              <input
                value={applicationDraft.borrower_gstin}
                onChange={(e) => setApplicationDraft({ borrower_gstin: e.target.value })}
                placeholder="GSTIN"
                className="w-full px-4 py-3 border rounded-lg"
              />
              <input
                type="number"
                value={applicationDraft.requested_amount || ''}
                onChange={(e) => setApplicationDraft({ requested_amount: Number(e.target.value) })}
                placeholder="Requested amount"
                className="w-full px-4 py-3 border rounded-lg"
              />
              <input
                type="number"
                value={applicationDraft.requested_tenor_months || ''}
                onChange={(e) => setApplicationDraft({ requested_tenor_months: Number(e.target.value) })}
                placeholder="Tenor in months"
                className="w-full px-4 py-3 border rounded-lg"
              />
            </div>
          </div>

          <div className="rounded-lg p-8 text-white shadow-lg" style={{ background: 'linear-gradient(to right, var(--brand-dark), var(--bg-tertiary))' }}>
            <h3 className="text-lg font-semibold mb-2">Qualitative Risk Override Score</h3>
            <div className="flex items-end gap-6">
              <div>
                <p className="text-5xl font-bold">{(qros * 10).toFixed(1)}</p>
                <p className="text-blue-100 text-sm mt-2">out of 10</p>
              </div>
              <p className="text-blue-100">
                {qros < 0.4 ? 'HIGH RISK' : qros < 0.6 ? 'MEDIUM RISK' : qros < 0.8 ? 'MEDIUM-LOW RISK' : 'LOW RISK'}
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {sliderConfigs.map((config) => (
            <div key={config.key} className="rounded-lg border p-6 shadow-sm glass-effect" style={{ borderColor: 'var(--border-color)' }}>
              <label className="block text-sm font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>{config.label}</label>
              <input
                type="range"
                min={config.min}
                max={config.max}
                value={config.value}
                onChange={(e) => setOfficerInput({ [config.key]: Number(e.target.value) })}
                className="w-full"
              />
              <div className="mt-4 flex justify-between">
                <span className="text-2xl font-bold text-brand-blue">{config.value}</span>
                <Badge label="LIVE INPUT" type="info" />
              </div>
            </div>
          ))}

          <div className="rounded-lg border p-6 shadow-sm glass-effect" style={{ borderColor: 'var(--border-color)' }}>
            <label className="block text-sm font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>Governance Score (0.0 - 1.0)</label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={officerInput.governance_score}
              onChange={(e) => setOfficerInput({ governance_score: Number(e.target.value) })}
              className="w-full"
            />
            <div className="mt-4 flex justify-between">
              <span className="text-2xl font-bold text-brand-blue">{officerInput.governance_score.toFixed(2)}</span>
              <Badge label="MODEL INPUT" type="success" />
            </div>
          </div>
        </div>

        <div className="rounded-lg border p-6 shadow-sm glass-effect" style={{ borderColor: 'var(--border-color)' }}>
          <label className="block text-sm font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>Officer Notes</label>
          <textarea
            value={officerInput.notes}
            onChange={(e) => setOfficerInput({ notes: e.target.value })}
            className="w-full px-4 py-3 border rounded-lg"
            rows={5}
            placeholder="Add management interview and site visit observations..."
          />
        </div>

        <div className="flex gap-4">
          <button
            onClick={() => runDecisioning()}
            disabled={isLoading}
            className="flex-1 font-semibold py-3 px-6 rounded-lg"
            style={{ backgroundColor: 'var(--brand-blue)', color: 'white' }}
          >
            {isLoading ? 'Running Backend Model...' : 'Save and Recompute'}
          </button>
        </div>
      </div>
    </Layout>
  )
}
