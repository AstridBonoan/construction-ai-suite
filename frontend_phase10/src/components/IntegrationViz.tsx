import React from 'react'
import { Phase9Output } from '../types/phase9'

const IntegrationViz: React.FC<{ item: Phase9Output }> = ({ item }) => {
  // Use same mapping keys as scripts/phase9/monday_mapping.py
  const mapping = {
    project_id: 'project_id',
    predicted_delay: 'predicted_delay',
    revenue: 'revenue',
    risk: 'risk',
    status: 'status'
  }
  const columnValues = {
    [mapping.predicted_delay]: item.predicted_delay_days ?? '',
    [mapping.risk]: item.risk_level,
    [mapping.status]: 'reported'
  }
  return (
    <div className="card">
      <h3>monday.com Mapping (visualization only)</h3>
      <div className="small">Column -> Value</div>
      <pre>{JSON.stringify(columnValues, null, 2)}</pre>
    </div>
  )
}

export default IntegrationViz
