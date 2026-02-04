import React from 'react'
import { Phase9Output } from '../types/phase9'

const Dashboard: React.FC<{ item: Phase9Output }> = ({ item }) => {
  const riskPct = Math.round(item.risk_score * 100)
  const delayPct = Math.round(item.delay_probability * 100)
  return (
    <div className="card">
      <h2>{item.project_id} — {item.project_name}</h2>
      <div className="small">Model: {item.model_version} • Generated: {item.generated_at}</div>
      <div style={{ marginTop: 8 }}>
        <div className="small">Risk score: {riskPct}%</div>
        <div className="risk-bar" aria-label="risk">
          <div className="risk-fill" style={{ width: `${riskPct}%` }} />
        </div>
      </div>
      <div style={{ marginTop: 8 }}>
        <div className="small">Delay probability: {delayPct}%</div>
        <div className="risk-bar" aria-label="delay">
          <div className="risk-fill" style={{ width: `${delayPct}%`, background: '#3498db' }} />
        </div>
      </div>
      {typeof item.confidence_score !== 'undefined' && (
        <div style={{ marginTop: 8 }} className="small">Confidence: {Math.round((item.confidence_score||0)*100)}%</div>
      )}
    </div>
  )
}

export default Dashboard
