import React from 'react'
import sample from './mock/phase9_sample.json'
import { Phase9Output } from './types/phase9'
import Dashboard from './components/Dashboard'
import ExplainabilityPanel from './components/ExplainabilityPanel'
import RiskFactorBreakdown from './components/RiskFactorBreakdown'
import Controls from './components/Controls'
import IntegrationViz from './components/IntegrationViz'

const App: React.FC = () => {
  const outputs: Phase9Output[] = sample as any
  const item = outputs[0]

  return (
    <div className="container">
      <h1>Phase 10 — Operator UI (Read-only)</h1>
      <Dashboard item={item} />
      <RiskFactorBreakdown factors={item.primary_risk_factors} />
      <ExplainabilityPanel item={item} />
      <IntegrationViz item={item} />
      <Controls />
    </div>
  )
}

export default App
