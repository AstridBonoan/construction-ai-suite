"""
Assign an existing or new user as `admin` for a tenant identified by workspace_id.

Usage:
  set DATABASE_URL=postgresql://user:pass@host:5432/dbname
  python backend/app/scripts/assign_admin.py --workspace ws-123 --external-user-id u-abc --email admin@example.com --name "Alice Admin"

If the tenant does not exist, this script will create it. It will ensure the `admin` role exists and assign it.
"""
import os
import argparse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), '..', 'migrations') if False else None


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--workspace', required=True, help='workspace_id / tenant workspace')
    p.add_argument('--external-user-id', required=True)
    p.add_argument('--email', required=False)
    p.add_argument('--name', required=False)
    return p.parse_args()


def run():
    args = parse_args()
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print('DATABASE_URL not set. Aborting.')
        return 1

    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Ensure tenant
        tenant = session.execute(text("SELECT id FROM tenants WHERE workspace_id = :w"), {'w': args.workspace}).fetchone()
        if tenant is None:
            print('Creating tenant', args.workspace)
            session.execute(text("INSERT INTO tenants (name, workspace_id, created_at, updated_at) VALUES (:n, :w, :now, :now)"),
                            {'n': f'Tenant {args.workspace}', 'w': args.workspace, 'now': datetime.utcnow()})
            session.commit()
            tenant = session.execute(text("SELECT id FROM tenants WHERE workspace_id = :w"), {'w': args.workspace}).fetchone()
        tenant_id = tenant[0]

        # Ensure admin role exists
        role = session.execute(text("SELECT id FROM roles WHERE name = 'admin'")).fetchone()
        if role is None:
            session.execute(text("INSERT INTO roles (name, description, created_at) VALUES ('admin','Tenant administrator', :now)"), {'now': datetime.utcnow()})
            session.commit()
            role = session.execute(text("SELECT id FROM roles WHERE name = 'admin'" )).fetchone()
        role_id = role[0]

        # Ensure user
        user = session.execute(text("SELECT id FROM users WHERE external_user_id = :u AND tenant_id = :t"), {'u': args.external_user_id, 't': tenant_id}).fetchone()
        if user is None:
            session.execute(text("INSERT INTO users (tenant_id, external_user_id, email, name, created_at) VALUES (:t, :u, :e, :n, :now)"),
                            {'t': tenant_id, 'u': args.external_user_id, 'e': args.email, 'n': args.name, 'now': datetime.utcnow()})
            session.commit()
            user = session.execute(text("SELECT id FROM users WHERE external_user_id = :u AND tenant_id = :t"), {'u': args.external_user_id, 't': tenant_id}).fetchone()
        user_id = user[0]

        # Ensure mapping in user_roles
        existing = session.execute(text("SELECT 1 FROM user_roles WHERE user_id = :uid AND role_id = :rid"), {'uid': user_id, 'rid': role_id}).fetchone()
        if not existing:
            session.execute(text("INSERT INTO user_roles (user_id, role_id, created_at) VALUES (:uid, :rid, :now)"), {'uid': user_id, 'rid': role_id, 'now': datetime.utcnow()})
            session.commit()
            print('Assigned admin role to user', user_id)
        else:
            print('User already has admin role')

        print('Done')
        return 0
    except Exception as e:
        print('Failed', e)
        session.rollback()
        return 2
    finally:
        session.close()


if __name__ == '__main__':
    raise SystemExit(run())
