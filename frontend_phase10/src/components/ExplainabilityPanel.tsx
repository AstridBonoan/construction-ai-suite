import React from 'react'
import { Phase9Output } from '../types/phase9'

const ExplainabilityPanel: React.FC<{ item: Phase9Output }> = ({ item }) => {
  const explanation = item.explanation && String(item.explanation).trim()
  return (
    <div className="card">
      <h3>Explainability</h3>
      <p>{explanation || 'No explanation provided.'}</p>
      <div className="small">Model: {item.model_version} • Generated: {item.generated_at}</div>
    </div>
  )
}

export default ExplainabilityPanel
