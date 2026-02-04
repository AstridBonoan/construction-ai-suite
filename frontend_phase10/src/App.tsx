import React from 'react'
import sample from './mock/phase9_sample.json'
import { Phase9Output } from './types/phase9'
import Dashboard from './components/Dashboard'
import ExplainabilityPanel from './components/ExplainabilityPanel'
import RiskFactorBreakdown from './components/RiskFactorBreakdown'
import Controls from './components/Controls'
import IntegrationViz from './components/IntegrationViz'

const BACKEND_URL = 'http://localhost:5000/phase9/outputs'

const App: React.FC = () => {
  const [mode, setMode] = React.useState<'mock' | 'live'>('mock')
  const [outputs, setOutputs] = React.useState<Phase9Output[] | null>(null)
  const [loading, setLoading] = React.useState(false)

  React.useEffect(() => {
    let cancelled = false

    const load = async () => {
      if (mode === 'mock') {
        setOutputs(sample as any)
        return
      }

      setLoading(true)
      try {
        const url = mode === 'live' ? `${BACKEND_URL}?variant=live` : BACKEND_URL
        const res = await fetch(url)
        if (!res.ok) throw new Error('Network response not ok')
        const data = await res.json()
        if (!cancelled) setOutputs(data)
      } catch (e) {
        // fallback to mock on error
        if (!cancelled) setOutputs(sample as any)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [mode])

  const item = outputs?.[0] ?? (sample as any)[0]

  return (
    <div className="container">
      <h1>Phase 10 — Operator UI (Read-only)</h1>

      <div style={{ marginBottom: 12 }}>
        <label style={{ marginRight: 8 }}>Data:</label>
        <button onClick={() => setMode('mock')} disabled={mode === 'mock'}>Mock</button>
        <button onClick={() => setMode('live')} disabled={mode === 'live'} style={{ marginLeft: 8 }}>Live</button>
        {loading && <span style={{ marginLeft: 12 }}>Loading live data…</span>}
      </div>

      <Dashboard item={item} />
      <RiskFactorBreakdown factors={item.primary_risk_factors} />
      <ExplainabilityPanel item={item} />
      <IntegrationViz item={item} />
      <Controls />
    </div>
  )
}

export default App
