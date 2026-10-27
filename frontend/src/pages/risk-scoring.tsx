import React from 'react'
import { Layout } from '@/components/Layout'
import { Badge, StatCard, Alert, Table, PDGaugeMeter, RiskHeatmapCard, AnomalyAlertPanel, ResearchIntelligenceTimeline, CovenantSuggestionsSection, SanctionSliderSimulator } from '@/components/UI'
import { AlertCircle, TrendingUp } from 'lucide-react'
import { useCreditApplication } from '@/context/CreditApplicationContext'

function badgeType(impact: string) {
  return impact === 'negative_to_credit' ? 'warning' : 'success'
}

export default function RiskScoringPage() {
  const { snapshot, runDecisioning, isLoading } = useCreditApplication()

  if (!snapshot?.scorecard) {
    return (
      <Layout>
        <Alert
          type="info"
          title="Scoring Not Available"
          message="Run backend decisioning after document upload to populate the score, grade, SHAP explanations, and recommendation."
        />
      </Layout>
    )
  }

  const { application, scorecard, research_hits, cockpit, anomaly_result, early_warning_result, research_graph } = snapshot
  const riskDrivers = scorecard.shap_explanation.filter((item) => item.impact === 'negative_to_credit')
  const positiveDrivers = scorecard.shap_explanation.filter((item) => item.impact === 'positive_to_credit')

  return (
    <Layout>
      <div className="space-y-8">
        <div>
          <h2 className="text-3xl font-bold" style={{ color: 'var(--text-primary)' }}>{application.borrower_name}</h2>
          <p className="mt-2" style={{ color: 'var(--text-secondary)' }}>Live backend scoring results</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard title="PD Score" value={(scorecard.probability_of_default * 100).toFixed(2)} unit="%" color="yellow" />
          <StatCard title="Credit Grade" value={scorecard.risk_grade} color="blue" />
          <StatCard title="Loan Limit" value={`₹${(scorecard.recommended_limit / 10000000).toFixed(2)}`} unit="Cr" color="green" />
          <StatCard title="Interest Rate" value={(scorecard.recommended_rate * 100).toFixed(2)} unit="%" color="blue" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <PDGaugeMeter pd={scorecard.probability_of_default} grade={scorecard.risk_grade} />
          <RiskHeatmapCard items={cockpit?.risk_heatmap || Object.entries(scorecard.score_breakdown).map(([dimension, value]) => ({ dimension, value }))} />
        </div>

        <Alert
          type="info"
          title="Model Information"
          message={`Model ${scorecard.model_version} generated this recommendation. ${scorecard.explanation_summary}`}
        />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <AnomalyAlertPanel title="Anomaly Alerts" items={anomaly_result?.anomaly_flags || cockpit?.anomaly_alerts || []} />
          <AnomalyAlertPanel title="Early Warning Signals" items={early_warning_result?.early_warning_flags || cockpit?.early_warning_signals || []} />
        </div>

        <div className="rounded-lg border p-6 shadow-sm glass-effect" style={{ borderColor: 'var(--border-color)' }}>
          <h3 className="text-lg font-semibold mb-6" style={{ color: 'var(--text-primary)' }}>SHAP-like Feature Contributions</h3>
          <div className="space-y-4">
            {scorecard.shap_explanation.map((item) => (
              <div key={item.feature} className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="font-medium" style={{ color: 'var(--text-primary)' }}>{item.feature}</span>
                  <span className={`font-bold ${item.contribution > 0 ? 'text-red-600' : 'text-green-600'}`}>
                    {item.contribution > 0 ? '+' : ''}{item.contribution.toFixed(4)}
                  </span>
                </div>
                {item.narrative_reason && <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>{item.narrative_reason}</p>}
                <div className="w-full rounded-full h-3 overflow-hidden" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
                  <div
                    className={item.contribution > 0 ? 'bg-red-500 h-full' : 'bg-green-500 h-full'}
                    style={{ width: `${Math.min(Math.abs(item.contribution) * 300, 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="rounded-lg border p-6 shadow-sm glass-effect" style={{ borderColor: 'var(--border-color)' }}>
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
              <AlertCircle className="text-red-600" size={20} />
              Risk Drivers
            </h3>
            <div className="space-y-4">
              {riskDrivers.map((driver) => (
                <div key={driver.feature} className="border-l-4 border-red-500 pl-4 py-2">
                  <p className="font-medium" style={{ color: 'var(--text-primary)' }}>{driver.feature}</p>
                  <div className="flex justify-between items-center mt-2">
                    <Badge label={driver.impact.replace(/_/g, ' ')} type={badgeType(driver.impact)} />
                    <span className="text-xs font-bold text-red-600">{driver.contribution.toFixed(4)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-lg border p-6 shadow-sm glass-effect" style={{ borderColor: 'var(--border-color)' }}>
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
              <TrendingUp className="text-green-600" size={20} />
              Positive Drivers
            </h3>
            <div className="space-y-4">
              {positiveDrivers.map((driver) => (
                <div key={driver.feature} className="border-l-4 border-green-500 pl-4 py-2">
                  <p className="font-medium" style={{ color: 'var(--text-primary)' }}>{driver.feature}</p>
                  <div className="flex justify-between items-center mt-2">
                    <Badge label={driver.impact.replace(/_/g, ' ')} type={badgeType(driver.impact)} />
                    <span className="text-xs font-bold text-green-600">{driver.contribution.toFixed(4)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="rounded-lg border p-6 shadow-sm glass-effect" style={{ borderColor: 'var(--border-color)' }}>
          <h3 className="text-lg font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>Five Cs Breakdown</h3>
          <Table
            headers={['Dimension', 'Score']}
            rows={Object.entries(scorecard.score_breakdown).map(([key, value]) => [
              key.toUpperCase(),
              `${(value * 10).toFixed(2)} / 10`,
            ])}
          />
        </div>

        <div className="rounded-lg border p-6 shadow-sm glass-effect" style={{ borderColor: 'var(--border-color)' }}>
          <h3 className="text-lg font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>Feature Vector</h3>
          <Table
            headers={['Feature', 'Backend Value']}
            rows={Object.entries(scorecard.feature_vector).map(([key, value]) => [key, Number(value).toFixed(4)])}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <SanctionSliderSimulator bands={scorecard.sanction_simulation || cockpit?.sanction_simulation_bands || {}} />
          <CovenantSuggestionsSection items={scorecard.covenant_recommendations || []} />
        </div>

        <ResearchIntelligenceTimeline
          items={(research_hits || []).map((item) => ({
            title: item.title,
            subtitle: item.summary,
            severity: item.severity,
          }))}
        />

        {research_graph && (
          <Alert
            type="info"
            title="Research Graph"
            message={`Promoter risk ${research_graph.promoter_risk.toFixed(2)}, litigation risk ${research_graph.litigation_risk.toFixed(2)}, sector outlook ${research_graph.sector_outlook}.`}
          />
        )}

        <div className="border-l-4 rounded-lg p-6" style={{ borderColor: 'var(--brand-blue)', backgroundColor: 'var(--bg-tertiary)' }}>
          <h3 className="text-lg font-semibold mb-3" style={{ color: 'var(--brand-blue)' }}>Recommendation</h3>
          <p className="mb-4" style={{ color: 'var(--text-secondary)' }}>
            {scorecard.decision.toUpperCase()} at ₹{(scorecard.recommended_limit / 10000000).toFixed(2)} Cr and {(scorecard.recommended_rate * 100).toFixed(2)}%.
          </p>
          {scorecard.pd_band && (
            <p className="mb-4" style={{ color: 'var(--text-secondary)' }}>
              PD band: {scorecard.pd_band.toUpperCase()} | Risk premium: {((scorecard.risk_premium || 0) * 100).toFixed(2)}%
            </p>
          )}
          <p className="mb-4" style={{ color: 'var(--text-secondary)' }}>
            Research hits considered: {research_hits.length}
          </p>
          <button
            onClick={() => runDecisioning()}
            disabled={isLoading}
            className="font-semibold py-2 px-4 rounded-lg"
            style={{ backgroundColor: 'var(--brand-blue)', color: 'white' }}
          >
            Recompute From Backend
          </button>
        </div>
      </div>
    </Layout>
  )
}
