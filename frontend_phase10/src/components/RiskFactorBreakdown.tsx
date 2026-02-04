import React from 'react'
import { PrimaryRiskFactor } from '../types/phase9'

const RiskFactorBreakdown: React.FC<{ factors: PrimaryRiskFactor[] }> = ({ factors }) => {
  const total = factors.reduce((s, f) => s + (f.contribution || 0), 0) || 1
  return (
    <div className="card">
      <h3>Primary Risk Factors</h3>
      <ul>
        {factors.map((f, i) => (
          <li key={i} style={{ marginBottom: 6 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <strong>{f.factor}</strong>
              <span>{Math.round((f.contribution/total)*100)}%</span>
            </div>
            <div className="risk-bar" style={{ marginTop: 6 }}>
              <div className="risk-fill" style={{ width: `${Math.round((f.contribution/total)*100)}%`, background: '#2ecc71' }} />
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default RiskFactorBreakdown
