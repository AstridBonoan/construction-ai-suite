# Feature 13 — Customer-Facing SaaS Frontend (v1)

This feature adds a customer-facing SaaS UI and monday.com OAuth integration for the Construction AI Suite.

Overview
- Branch: `feature/customer-saas-frontend-v1`
- Frontend: `frontend/` (React + Vite)
- Backend OAuth routes: `backend/app/feature13_monday_oauth.py`

Quick start (development)
1. Backend: ensure environment variables are set (MONDAY_CLIENT_ID, MONDAY_CLIENT_SECRET, MONDAY_OAUTH_REDIRECT_URI, JWT_SECRET).
2. From repo root, activate backend venv and run the Flask app.
3. Frontend: from `frontend/`, run `npm install` then `npm run dev`.

Security notes
- Do not check in `MONDAY_CLIENT_SECRET` or `JWT_SECRET`.
- Frontend never contains secrets; OAuth is initiated via backend.

Next steps
- Persist installed accounts and refresh tokens to DB.
- Implement tenant-aware role handling and RBAC.
- Add UI polish, onboarding flows, and e2e tests (Playwright/Cypress).

DB migrations
- A SQL migration is available at `backend/app/migrations/0001_create_tenant_tables.sql` to create `tenants`, `users`, `roles`, `user_roles`, and `oauth_installations`.
- Run the migration against your production DB (or use Alembic to integrate) before enabling OAuth persistence.

RBAC
- Admin endpoints are exposed under `/api/saas/admin/*`. They require an `admin` role in the tenant. You can assign roles using the DB `roles` and `user_roles` tables.
- Middleware is implemented in `backend/app/rbac.py` as `require_role('admin')` decorator. It prefers DB-backed role checks if the DB is configured, otherwise it falls back to `roles` claim in the JWT.

Migration runner & admin bootstrap
- Use `backend/app/scripts/run_migrations.py` to apply SQL migrations. Ensure `DATABASE_URL` environment variable is set.
- Use `backend/app/scripts/assign_admin.py` to create or assign an admin user to a tenant after running migrations.

Examples:
```bash
# Apply migrations
export DATABASE_URL=postgresql://user:pass@host:5432/db
python backend/app/scripts/run_migrations.py

# Bootstrap an admin user for workspace ws-123
python backend/app/scripts/assign_admin.py --workspace ws-123 --external-user-id u-1 --email admin@org.com --name "Admin User"
```

Local DB init (dev)

If you want a quick local DB setup (dev only), you can use:

```bash
export DATABASE_URL=postgresql://user:pass@localhost:5432/devdb
python backend/app/scripts/init_db.py
```

This calls `SQLAlchemy.create_all()` and is intended only for development convenience. Use migrations for production.
