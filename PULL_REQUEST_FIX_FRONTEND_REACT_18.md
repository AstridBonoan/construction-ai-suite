Title: chore(frontend): pin React to ^18 for framer-motion compatibility

Why:
- `framer-motion@^9` requires React ^18; keeping React at ^19 causes ERESOLVE
  dependency resolution failures in some environments and CI.

What:
- Pins `react`, `react-dom`, and `@types/*` to ^18 in `frontend/package.json`.
- Adds small placeholder SaaS components so the frontend build stays green while
  final UI work is completed.

Validation performed:
- `cd frontend && npm ci && npm run build` — build succeeds locally.
- ESLint report saved at `frontend/eslint_report.json` (no errors for current files).

How to review & merge:
1. Open the PR URL: https://github.com/AstridBonoan/construction-ai-suite/compare/main...fix/frontend-react-18?expand=1
2. Confirm CI checks pass on the PR.
3. Merge into `main` (or request review / changes as needed).

Notes:
- After merge, consider replacing placeholder SaaS components with final UI.
- Alternatively, update `framer-motion` to a React-19-compatible release if
  one becomes available.
