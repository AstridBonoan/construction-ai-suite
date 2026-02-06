import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import AnalystReviewPanel from '../src/components/AnalystReviewPanel'
import { Phase9Output } from '../src/types/phase9'

const mockItem: Phase9Output = {
  schema_version: 'phase9-v1',
  project_id: 'P-TEST-001',
  project_name: 'Test Project',
  risk_score: 0.75,
  risk_level: 'high',
  predicted_delay_days: 10,
  delay_probability: 0.60,
  confidence_score: 0.85,
  primary_risk_factors: [
    { factor: 'schedule_risk', contribution: 0.4 },
    { factor: 'resource_risk', contribution: 0.35 }
  ],
  recommended_actions: ['audit-schedule'],
  explanation: 'Test explanation',
  model_version: 'v1',
  generated_at: '2026-02-04T00:00:00Z'
}

describe('AnalystReviewPanel', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  test('renders review status dropdown', () => {
    render(<AnalystReviewPanel item={mockItem} />)
    expect(screen.getByDisplayValue('unreviewed')).toBeInTheDocument()
  })

  test('renders notes textarea', () => {
    render(<AnalystReviewPanel item={mockItem} />)
    const textarea = screen.getByPlaceholderText(/Add non-destructive observations/)
    expect(textarea).toBeInTheDocument()
  })

  test('renders save button', () => {
    render(<AnalystReviewPanel item={mockItem} />)
    expect(screen.getByText('Save Annotation')).toBeInTheDocument()
  })

  test('saves annotation to localStorage', async () => {
    render(<AnalystReviewPanel item={mockItem} />)
    
    const textarea = screen.getByPlaceholderText(/Add non-destructive observations/)
    fireEvent.change(textarea, { target: { value: 'Test analyst note' } })
    
    const saveButton = screen.getByText('Save Annotation')
    fireEvent.click(saveButton)

    await waitFor(() => {
      expect(screen.getByText(/Last saved:/)).toBeInTheDocument()
    })

    const stored = localStorage.getItem('phase11_analyst_annotations')
    expect(stored).toBeTruthy()
    const data = JSON.parse(stored!)
    expect(data['P-TEST-001'].notes).toBe('Test analyst note')
  })

  test('restores annotation on mount', () => {
    // First render - save annotation
    const { unmount } = render(<AnalystReviewPanel item={mockItem} />)
    const textarea = screen.getByPlaceholderText(/Add non-destructive observations/)
    fireEvent.change(textarea, { target: { value: 'Persisted note' } })
    const saveButton = screen.getByText('Save Annotation')
    fireEvent.click(saveButton)

    unmount()

    // Second render - should restore
    render(<AnalystReviewPanel item={mockItem} />)
    const restoredTextarea = screen.getByPlaceholderText(/Add non-destructive observations/) as HTMLTextAreaElement
    expect(restoredTextarea.value).toBe('Persisted note')
  })

  test('updates review status and persists', async () => {
    render(<AnalystReviewPanel item={mockItem} />)
    
    const select = screen.getByDisplayValue('unreviewed') as HTMLSelectElement
    fireEvent.change(select, { target: { value: 'reviewed' } })
    
    const saveButton = screen.getByText('Save Annotation')
    fireEvent.click(saveButton)

    await waitFor(() => {
      const stored = localStorage.getItem('phase11_analyst_annotations')
      const data = JSON.parse(stored!)
      expect(data['P-TEST-001'].reviewStatus).toBe('reviewed')
    })
  })

  test('AI output remains immutable', () => {
    render(<AnalystReviewPanel item={mockItem} />)
    
    // Verify AI data is displayed read-only
    expect(screen.getByText(/AI output is immutable/)).toBeInTheDocument()
    
    // Add notes
    const textarea = screen.getByPlaceholderText(/Add non-destructive observations/)
    fireEvent.change(textarea, { target: { value: 'Test note' } })
    
    const saveButton = screen.getByText('Save Annotation')
    fireEvent.click(saveButton)

    // Verify original Phase 9 output is unchanged
    const stored = localStorage.getItem('phase11_analyst_annotations')
    const data = JSON.parse(stored!)
    expect(data['P-TEST-001'].projectId).toBe('P-TEST-001')
    expect(data['P-TEST-001'].notes).toBe('Test note')
    // Risk score not in annotations - remains in original Phase 9 output
    expect(data['P-TEST-001'].risk_score).toBeUndefined()
  })
})
