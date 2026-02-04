import { render, screen } from '@testing-library/react'
import App from '../src/App'

test('renders dashboard with project id and risk', () => {
  render(<App />)
  expect(screen.getByText(/Phase 10 — Operator UI/)).toBeInTheDocument()
  expect(screen.getByText(/P-1001/)).toBeInTheDocument()
  expect(screen.getByLabelText('risk')).toBeInTheDocument()
})
