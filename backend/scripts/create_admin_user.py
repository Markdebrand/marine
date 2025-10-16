#!/usr/bin/env python3
"""Create an admin user in the database for local development.

Usage:
  python scripts/create_admin_user.py --email admin@example.com --password secret
  or run without password to be prompted.
"""
from __future__ import annotations
import argparse
from getpass import getpass
from sqlalchemy import create_engine, text
from passlib.context import CryptContext
import re
from pathlib import Path


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def read_db_url() -> str:
    env = Path(__file__).parent.parent / '.env'
    content = env.read_text()
    m = re.search(r'^ALEMBIC_DATABASE_URL\s*=\s*"?([^"\n]+)"?', content, flags=re.M)
    if m:
        return m.group(1)
    raise SystemExit('ALEMBIC_DATABASE_URL not found in .env')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--email', required=False, default='admin@local')
    p.add_argument('--password', required=False)
    args = p.parse_args()
    password = args.password or getpass('Password for admin: ')
    try:
        pw_hash = pwd_context.hash(password)
    except Exception:
        # Fallback: call scripts/hash_password.py to generate a bcrypt hash
        import subprocess
        import shlex
        cmd = f'python "{Path(__file__).parent / "hash_password.py"}" {shlex.quote(password)}'
        out = subprocess.check_output(cmd, shell=True, text=True)
        pw_hash = out.strip()
    db = read_db_url()
    eng = create_engine(db)
    with eng.begin() as conn:
        # ensure role exists
        conn.execute(text("INSERT INTO roles (name, slug) VALUES (:name, :slug) ON CONFLICT (slug) DO NOTHING"), {'name':'Administrator','slug':'admin'})

        # check if user exists
        res = conn.execute(text('SELECT id FROM "user" WHERE email = :email'), {'email': args.email}).fetchone()
        if res:
            user_id = res[0]
            # update password
            conn.execute(text('UPDATE "user" SET password_hash = :pw WHERE id = :id'), {'pw': pw_hash, 'id': user_id})
        else:
            r = conn.execute(text('INSERT INTO "user" (email, password_hash, role, is_superadmin, is_active) VALUES (:email, :pw, '"'"'admin'"'"', true, true) RETURNING id'), {'email': args.email, 'pw': pw_hash})
            row = r.fetchone()
            user_id = row[0] if row else None

        if not user_id:
            print('Failed to create or find user')
            return

        # attach role if not already attached
        role_row = conn.execute(text("SELECT id FROM roles WHERE slug='admin'"))
        role = role_row.fetchone()
        if role:
            role_id = role[0]
            exists = conn.execute(text('SELECT 1 FROM user_roles WHERE user_id = :uid AND role_id = :rid'), {'uid': user_id, 'rid': role_id}).fetchone()
            if not exists:
                conn.execute(text('INSERT INTO user_roles (user_id, role_id) VALUES (:uid, :rid)'), {'uid': user_id, 'rid': role_id})
        print('Admin user ensured:', args.email)


if __name__ == '__main__':
    main()
