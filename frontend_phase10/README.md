Frontend Phase 10 - Operator UI

Entry point: `src/main.tsx` -> `src/App.tsx`

Components:
- `components/Dashboard.tsx` — top-level project view with risk and delay bars
- `components/RiskFactorBreakdown.tsx` — ranked factors and contribution bars
- `components/ExplainabilityPanel.tsx` — natural-language explanation and metadata
- `components/Controls.tsx` — UI-only human controls (Approve/Flag/Ignore)
- `components/IntegrationViz.tsx` — visualization of monday.com mapping (no API)

Mock data: `src/mock/phase9_sample.json` (matches Phase 9 schema)

Tests: `tests/App.test.tsx` (Vitest + React Testing Library)

To run locally (install dependencies first):

```
cd frontend_phase10
npm install
npm run dev
npm run test
```
