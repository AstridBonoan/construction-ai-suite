import { render } from '@testing-library/react'
import Dashboard from '../src/components/Dashboard'

const item = {
  schema_version: 'phase9-v1',
  project_id: 'P-3000',
  project_name: 'Determinism Project',
  risk_score: 0.42,
  risk_level: 'medium',
  delay_probability: 0.25,
  confidence_score: 0.8,
  primary_risk_factors: [],
  recommended_actions: [],
  explanation: 'Deterministic test',
  model_version: 'v1',
  generated_at: '2026-02-03T12:00:00Z'
}

test('dashboard renders deterministically', () => {
  const r1 = render(<Dashboard item={item as any} />)
  const html1 = r1.container.innerHTML
  r1.unmount()
  const r2 = render(<Dashboard item={item as any} />)
  const html2 = r2.container.innerHTML
  expect(html1).toEqual(html2)
})
