import React from 'react'
import { Phase9Output } from '../types/phase9'
import { ReviewStatus, AnalystAnnotation } from '../types/analyst'
import { useAnalystNotes } from '../hooks/useAnalystNotes'

const AnalystReviewPanel: React.FC<{ item: Phase9Output }> = ({ item }) => {
  const { getAnnotation, saveAnnotation } = useAnalystNotes()
  const [annotation, setAnnotation] = React.useState<AnalystAnnotation | null>(null)
  const [notes, setNotes] = React.useState('')
  const [status, setStatus] = React.useState<ReviewStatus>('unreviewed')

  React.useEffect(() => {
    const existing = getAnnotation(item.project_id)
    if (existing) {
      setAnnotation(existing)
      setNotes(existing.notes)
      setStatus(existing.reviewStatus)
    }
  }, [item.project_id])

  const handleSave = () => {
    const updated: AnalystAnnotation = {
      projectId: item.project_id,
      timestamp: new Date().toISOString(),
      reviewStatus: status,
      notes: notes.trim(),
      flaggedRisks: item.primary_risk_factors?.map(f => f.factor)
    }
    if (saveAnnotation(updated)) {
      setAnnotation(updated)
      alert('Analyst notes saved (non-destructive annotation)')
    }
  }

  return (
    <div className="card" style={{ backgroundColor: '#f8f9fa', borderLeft: '4px solid #3498db' }}>
      <h3>📋 Analyst Review (Read-Only Intelligence)</h3>
      <div className="small" style={{ marginBottom: 12, color: '#7f8c8d' }}>
        ⚠️ AI output is immutable. Only your notes are saved below.
      </div>

      <div style={{ marginBottom: 12 }}>
        <label style={{ display: 'block', marginBottom: 4 }}>
          <strong>Review Status:</strong>
        </label>
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value as ReviewStatus)}
          style={{
            padding: '6px 8px',
            borderRadius: 4,
            border: '1px solid #bdc3c7',
            width: '100%'
          }}
        >
          <option value="unreviewed">Unreviewed</option>
          <option value="reviewed">Reviewed</option>
          <option value="needs_followup">Needs Follow-Up</option>
        </select>
      </div>

      <div style={{ marginBottom: 12 }}>
        <label style={{ display: 'block', marginBottom: 4 }}>
          <strong>Analyst Notes:</strong>
        </label>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Add non-destructive observations (e.g., 'Schedule risk aligns with project updates', 'Subcontractor churn confirmed')"
          style={{
            width: '100%',
            minHeight: 80,
            padding: 8,
            borderRadius: 4,
            border: '1px solid #bdc3c7',
            fontFamily: 'monospace',
            fontSize: 12
          }}
        />
      </div>

      <button
        onClick={handleSave}
        style={{
          padding: '8px 16px',
          backgroundColor: '#3498db',
          color: 'white',
          border: 'none',
          borderRadius: 4,
          cursor: 'pointer'
        }}
      >
        Save Annotation
      </button>

      {annotation && (
        <div
          style={{
            marginTop: 12,
            padding: 8,
            backgroundColor: '#ecf0f1',
            borderRadius: 4,
            fontSize: 11
          }}
        >
          <div className="small">
            Last saved: {new Date(annotation.timestamp).toLocaleString()}
          </div>
        </div>
      )}
    </div>
  )
}

export default AnalystReviewPanel
