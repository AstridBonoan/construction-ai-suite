import React from 'react'

const Controls: React.FC = () => {
  const [state, setState] = React.useState<string | null>(null)
  return (
    <div className="card">
      <h3>Human Controls (UI-only)</h3>
      <div style={{ display: 'flex', gap: 8 }}>
        <button onClick={() => setState('approved')}>Approve Insight</button>
        <button onClick={() => setState('flagged')}>Flag for Review</button>
        <button onClick={() => setState('ignored')}>Ignore</button>
      </div>
      <div style={{ marginTop: 8 }} className="small">UI-state: {state ?? 'none'}</div>
    </div>
  )
}

export default Controls
