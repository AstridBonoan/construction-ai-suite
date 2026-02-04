import { render, screen } from '@testing-library/react'
import ExplainabilityPanel from '../src/components/ExplainabilityPanel'

const itemMissingExplanation: any = {
  schema_version: 'phase9-v1',
  project_id: 'P-2000',
  project_name: 'Missing Explanation Project',
  risk_score: 0.1,
  risk_level: 'low',
  delay_probability: 0.05,
  primary_risk_factors: [],
  recommended_actions: [],
  model_version: 'v1',
  generated_at: '2026-02-03T12:00:00Z'
}

test('explainability panel shows fallback when explanation missing', () => {
  render(<ExplainabilityPanel item={itemMissingExplanation} />)
  expect(screen.getByText(/No explanation provided\./)).toBeInTheDocument()
})
