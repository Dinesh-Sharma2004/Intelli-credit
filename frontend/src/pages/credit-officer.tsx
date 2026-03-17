import React, { useState } from 'react'
import { Layout } from '@/components/Layout'
import { Badge } from '@/components/UI'

export default function CreditOfficerPortal() {
  const [formData, setFormData] = useState({
    capacity_utilization: 75,
    management_quality: 8,
    inventory_observation: 7,
    customer_concentration: 35,
    governance_observation: 8,
    notes: 'Company demonstrates strong operational efficiency. Management team is experienced.',
  })

  const [qros, setQROS] = useState(0)

  const handleChange = (field: string, value: any) => {
    setFormData({ ...formData, [field]: value })
    calculateQROS({ ...formData, [field]: value })
  }

  const calculateQROS = (data: any) => {
    const rawScore =
      (data.capacity_utilization / 100) * 0.2 +
      (data.management_quality / 10) * 0.25 +
      (data.inventory_observation / 10) * 0.2 +
      ((100 - Math.min(data.customer_concentration, 100)) / 100) * 0.15 +
      (data.governance_observation / 10) * 0.2
    setQROS(rawScore)
  }

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Credit Officer Portal</h2>
          <p className="text-gray-600 mt-2">Input qualitative factors for Qualitative Risk Override Score (QROS)</p>
        </div>

        {/* Current QROS */}
        <div className="bg-gradient-to-r from-brand-dark to-slate-dark rounded-lg p-8 text-white shadow-lg">
          <h3 className="text-lg font-semibold mb-2">Qualitative Risk Override Score</h3>
          <div className="flex items-end gap-6">
            <div>
              <p className="text-5xl font-bold">{(qros * 10).toFixed(1)}</p>
              <p className="text-blue-100 text-sm mt-2">out of 10</p>
            </div>
            <p className="text-blue-100">
              {qros < 4 ? 'HIGH RISK' : qros < 6 ? 'MEDIUM RISK' : qros < 8 ? 'MEDIUM-LOW RISK' : 'LOW RISK'}
            </p>
          </div>
        </div>

        {/* Form */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Factory Capacity Utilization */}
          <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
            <label className="block text-sm font-semibold text-gray-900 mb-4">
              Factory Capacity Utilization (%)
            </label>
            <input
              type="range"
              min="0"
              max="100"
              value={formData.capacity_utilization}
              onChange={(e) => handleChange('capacity_utilization', Number(e.target.value))}
              className="w-full"
            />
            <div className="mt-4 flex justify-between">
              <span className="text-2xl font-bold text-brand-blue">{formData.capacity_utilization}%</span>
              <Badge
                label={
                  formData.capacity_utilization > 80
                    ? 'EXCELLENT'
                    : formData.capacity_utilization > 60
                    ? 'GOOD'
                    : 'LOW'
                }
                type={
                  formData.capacity_utilization > 80
                    ? 'success'
                    : formData.capacity_utilization > 60
                    ? 'info'
                    : 'warning'
                }
              />
            </div>
            <p className="text-xs text-gray-600 mt-3">
              {formData.capacity_utilization > 80
                ? 'Excellent utilization of assets'
                : formData.capacity_utilization > 60
                ? 'Good operational efficiency'
                : 'Significant spare capacity available'}
            </p>
          </div>

          {/* Management Quality */}
          <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
            <label className="block text-sm font-semibold text-gray-900 mb-4">
              Management Quality (1-10)
            </label>
            <input
              type="range"
              min="1"
              max="10"
              value={formData.management_quality}
              onChange={(e) => handleChange('management_quality', Number(e.target.value))}
              className="w-full"
            />
            <div className="mt-4 flex justify-between">
              <span className="text-2xl font-bold text-brand-blue">{formData.management_quality}/10</span>
              <Badge
                label={
                  formData.management_quality > 8
                    ? 'STRONG'
                    : formData.management_quality > 6
                    ? 'ADEQUATE'
                    : 'WEAK'
                }
                type={
                  formData.management_quality > 8
                    ? 'success'
                    : formData.management_quality > 6
                    ? 'info'
                    : 'warning'
                }
              />
            </div>
            <p className="text-xs text-gray-600 mt-3">
              {formData.management_quality > 8
                ? 'Experienced and competent leadership'
                : formData.management_quality > 6
                ? 'Management capabilities are adequate'
                : 'Concerns about management capability'}
            </p>
          </div>

          {/* Inventory Observation */}
          <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
            <label className="block text-sm font-semibold text-gray-900 mb-4">
              Inventory Quality (1-10)
            </label>
            <input
              type="range"
              min="1"
              max="10"
              value={formData.inventory_observation}
              onChange={(e) => handleChange('inventory_observation', Number(e.target.value))}
              className="w-full"
            />
            <div className="mt-4 flex justify-between">
              <span className="text-2xl font-bold text-brand-blue">{formData.inventory_observation}/10</span>
              <Badge
                label={
                  formData.inventory_observation > 7
                    ? 'GOOD'
                    : formData.inventory_observation > 5
                    ? 'AVERAGE'
                    : 'POOR'
                }
                type={
                  formData.inventory_observation > 7
                    ? 'success'
                    : formData.inventory_observation > 5
                    ? 'info'
                    : 'warning'
                }
              />
            </div>
            <p className="text-xs text-gray-600 mt-3">
              {formData.inventory_observation > 7
                ? 'Inventory appears well-maintained'
                : formData.inventory_observation > 5
                ? 'Inventory shows average quality'
                : 'Concerns about inventory obsolescence'}
            </p>
          </div>

          {/* Customer Concentration */}
          <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
            <label className="block text-sm font-semibold text-gray-900 mb-4">
              Top Customer Concentration (%)
            </label>
            <input
              type="range"
              min="0"
              max="100"
              value={formData.customer_concentration}
              onChange={(e) => handleChange('customer_concentration', Number(e.target.value))}
              className="w-full"
            />
            <div className="mt-4 flex justify-between">
              <span className="text-2xl font-bold text-brand-blue">{formData.customer_concentration}%</span>
              <Badge
                label={
                  formData.customer_concentration < 25
                    ? 'EXCELLENT'
                    : formData.customer_concentration < 50
                    ? 'GOOD'
                    : 'HIGH RISK'
                }
                type={
                  formData.customer_concentration < 25
                    ? 'success'
                    : formData.customer_concentration < 50
                    ? 'info'
                    : 'warning'
                }
              />
            </div>
            <p className="text-xs text-gray-600 mt-3">
              {formData.customer_concentration < 25
                ? 'Well-diversified customer base'
                : formData.customer_concentration < 50
                ? 'Moderate customer concentration'
                : 'High dependency on few customers'}
            </p>
          </div>

          {/* Governance Observation */}
          <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
            <label className="block text-sm font-semibold text-gray-900 mb-4">
              Governance & Compliance (1-10)
            </label>
            <input
              type="range"
              min="1"
              max="10"
              value={formData.governance_observation}
              onChange={(e) => handleChange('governance_observation', Number(e.target.value))}
              className="w-full"
            />
            <div className="mt-4 flex justify-between">
              <span className="text-2xl font-bold text-brand-blue">{formData.governance_observation}/10</span>
              <Badge
                label={
                  formData.governance_observation > 8
                    ? 'STRONG'
                    : formData.governance_observation > 6
                    ? 'ADEQUATE'
                    : 'WEAK'
                }
                type={
                  formData.governance_observation > 8
                    ? 'success'
                    : formData.governance_observation > 6
                    ? 'info'
                    : 'warning'
                }
              />
            </div>
            <p className="text-xs text-gray-600 mt-3">
              {formData.governance_observation > 8
                ? 'Strong governance practices'
                : formData.governance_observation > 6
                ? 'Adequate governance structures'
                : 'Governance concerns noted'}
            </p>
          </div>
        </div>

        {/* Notes */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <label className="block text-sm font-semibold text-gray-900 mb-3">Credit Officer Notes</label>
          <textarea
            value={formData.notes}
            onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:border-brand-blue"
            rows={5}
            placeholder="Add your observations and notes here..."
          />
        </div>

        {/* QROS Calculation Details */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-4">QROS Calculation</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
            <div>
              <p className="text-xs text-blue-700">Capacity Utilization (20%)</p>
              <p className="font-bold text-blue-600">{((formData.capacity_utilization / 100) * 0.2 * 10).toFixed(2)}/10</p>
            </div>
            <div>
              <p className="text-xs text-blue-700">Management Quality (25%)</p>
              <p className="font-bold text-blue-600">{((formData.management_quality / 10) * 0.25 * 10).toFixed(2)}/10</p>
            </div>
            <div>
              <p className="text-xs text-blue-700">Inventory Quality (20%)</p>
              <p className="font-bold text-blue-600">{((formData.inventory_observation / 10) * 0.2 * 10).toFixed(2)}/10</p>
            </div>
            <div>
              <p className="text-xs text-blue-700">Diversification (15%)</p>
              <p className="font-bold text-blue-600">
                {(((100 - Math.min(formData.customer_concentration, 100)) / 100) * 0.15 * 10).toFixed(2)}/10
              </p>
            </div>
            <div>
              <p className="text-xs text-blue-700">Governance (20%)</p>
              <p className="font-bold text-blue-600">{((formData.governance_observation / 10) * 0.2 * 10).toFixed(2)}/10</p>
            </div>
            <div className="bg-white rounded p-3 border border-blue-300">
              <p className="text-xs text-blue-700 font-semibold">TOTAL QROS</p>
              <p className="font-bold text-2xl text-blue-600">{(qros * 10).toFixed(1)}/10</p>
            </div>
          </div>
        </div>

        {/* Override Recommendation */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Override Recommendations</h3>
          <div className="space-y-3">
            {qros > 7 && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <p className="text-sm font-semibold text-green-900">✓ Can override to lower risk grade</p>
              </div>
            )}
            {qros > 6 && qros <= 7 && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm font-semibold text-blue-900">⚠ Consider minor overrides if justified</p>
              </div>
            )}
            {qros <= 6 && (
              <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                <p className="text-sm font-semibold text-orange-900">⚠ Not recommended for grade override</p>
              </div>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4">
          <button className="flex-1 bg-brand-blue hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors">
            Save Changes
          </button>
          <button className="flex-1 bg-white border border-gray-200 hover:border-brand-blue text-gray-900 font-semibold py-3 px-6 rounded-lg transition-all">
            Apply QROS Override
          </button>
        </div>
      </div>
    </Layout>
  )
}
