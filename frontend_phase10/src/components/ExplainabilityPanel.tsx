import React from 'react'
import { Phase9Output } from '../types/phase9'

const ExplainabilityPanel: React.FC<{ item: Phase9Output }> = ({ item }) => {
  return (
    <div className="card">
      <h3>Explainability</h3>
      <p>{item.explanation}</p>
      <div className="small">Model: {item.model_version} • Generated: {item.generated_at}</div>
    </div>
  )
}

export default ExplainabilityPanel
