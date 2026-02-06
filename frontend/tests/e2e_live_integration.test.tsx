import React from 'react'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import App from '../src/App'

// This test performs a lightweight E2E: it fetches the backend endpoint
// and stubs the app's fetch to return that payload, then renders the UI
// and asserts the primary project title is shown when Live mode is selected.
test('Live mode renders backend project name', async () => {
  // fetch the backend payload (backend should be running locally)
  const backendRes = await fetch('http://localhost:5000/phase9/outputs')
  const data = await backendRes.json()
  const proj = Array.isArray(data) ? data[0] : data[0]

  // stub global fetch for the app to return the backend payload
  const stub = () => Promise.resolve({ ok: true, json: () => Promise.resolve(data) } as any)
  // @ts-ignore
  vi.stubGlobal('fetch', stub)

  render(<App />)

  // click Live button
  const liveBtn = screen.getByText('Live')
  fireEvent.click(liveBtn)

  // wait for the project title to appear
  await waitFor(() => {
    expect(screen.getByText(new RegExp(proj.project_id))).toBeInTheDocument()
  })
})
