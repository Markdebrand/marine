#!/usr/bin/env python3
"""
Script to rebaseline Alembic migrations:
- moves existing files from app/db/alembic/versions -> legacy_versions
- creates a simple baseline migration file in versions/0001_baseline_hsomarine.py

Run locally from the repo root:
    python backend/scripts/rebaseline_alembic.py

This script modifies files in-place. It creates a backup copy of the versions folder
as a zip named versions_backup_<timestamp>.zip before moving.
"""
import os
import shutil
import zipfile
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ALEMBIC_DIR = os.path.join(ROOT, 'app', 'db', 'alembic')
VERSIONS_DIR = os.path.join(ALEMBIC_DIR, 'versions')
LEGACY_DIR = os.path.join(ALEMBIC_DIR, 'legacy_versions')

BASELINE_NAME = '0001_baseline_hsomarine.py'


def backup_versions():
    if not os.path.isdir(VERSIONS_DIR):
        print(f'Versions directory not found: {VERSIONS_DIR}')
        return None
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    zipname = os.path.join(ALEMBIC_DIR, f'versions_backup_{timestamp}.zip')
    with zipfile.ZipFile(zipname, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(VERSIONS_DIR):
            for f in files:
                full = os.path.join(root, f)
                arc = os.path.relpath(full, VERSIONS_DIR)
                zf.write(full, arc)
    print('Backup created:', zipname)
    return zipname


def ensure_dirs():
    os.makedirs(LEGACY_DIR, exist_ok=True)
    os.makedirs(VERSIONS_DIR, exist_ok=True)


def move_old_versions():
    moved = []
    for name in os.listdir(VERSIONS_DIR):
        src = os.path.join(VERSIONS_DIR, name)
        dst = os.path.join(LEGACY_DIR, name)
        # skip our baseline if already present
        if name == BASELINE_NAME:
            continue
        if os.path.isfile(src):
            shutil.move(src, dst)
            moved.append(name)
    return moved


def create_legacy_readme():
    readme = os.path.join(LEGACY_DIR, 'README.md')
    if not os.path.exists(readme):
        with open(readme, 'w', encoding='utf-8') as f:
            f.write('# legacy_versions\n\n')
            f.write('This folder contains migrated Alembic revision files moved from `versions/`\n')
            f.write('during a rebaseline operation.\n')
            f.write('\nKeep this directory for historical purposes. Do not re-add these files to `versions/` unless you know what you are doing.\n')
    print('Legacy README ensured at', readme)


def create_baseline_if_missing():
    baseline_path = os.path.join(VERSIONS_DIR, BASELINE_NAME)
    if os.path.exists(baseline_path):
        print('Baseline already exists:', baseline_path)
        return baseline_path
    # Minimal alembic migration file
    body = '''"""empty migration - baseline for HSOMarine"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_baseline_hsomarine'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Baseline migration - no operations."""
    pass


def downgrade() -> None:
    """Baseline downgrade - no operations."""
    pass

'''
    with open(baseline_path, 'w', encoding='utf-8') as f:
        f.write(body)
    print('Created baseline migration at', baseline_path)
    return baseline_path


def main():
    print('Rebaseline Alembic: starting')
    ensure_dirs()
    backup = backup_versions()
    moved = move_old_versions()
    create_legacy_readme()
    baseline = create_baseline_if_missing()
    print('\nSummary:')
    print(' backup:', backup)
    print(' moved files count:', len(moved))
    if moved:
        for m in moved:
            print('  -', m)
    print(' baseline:', baseline)
    print('\nNext steps:')
    print(' - Review files in', LEGACY_DIR)
    print(' - If using an existing DB, run: alembic stamp head')
    print(' - Otherwise, run: alembic upgrade head')


if __name__ == '__main__':
    main()
