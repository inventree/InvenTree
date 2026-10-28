#!/bin/sh
set -eu

PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
export PATH

ROOT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd)
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
    printf 'Backend virtualenv not found: %s\n' "$VENV_PYTHON" >&2
    exit 1
fi

export PATH="$ROOT_DIR/.venv/bin:$PATH"
export INVENTREE_DB_ENGINE=sqlite3
export INVENTREE_DB_NAME="$ROOT_DIR/.local/inventree-tests.sqlite3"
export INVENTREE_MEDIA_ROOT="$ROOT_DIR/.local/test-media"
export INVENTREE_STATIC_ROOT="$ROOT_DIR/.local/test-static"
export INVENTREE_BACKUP_DIR="$ROOT_DIR/.local/test-backup"
export INVENTREE_SITE_URL=http://localhost:8000
export INVENTREE_DEBUG=True
export INVENTREE_PLUGINS_ENABLED=True
export INVENTREE_CONSOLE_LOG=False
export INVENTREE_ALLOWED_HOSTS='*'
export INVENTREE_TRUSTED_ORIGINS=http://testserver

mkdir -p "$ROOT_DIR/.local/test-media" \
    "$ROOT_DIR/.local/test-static" \
    "$ROOT_DIR/.local/test-backup"

cd "$ROOT_DIR/src/backend/InvenTree"

"$VENV_PYTHON" manage.py collectstatic --noinput --verbosity 0

if [ "$#" -eq 0 ]; then
    set -- build common company importer machine order part pricing report stock users plugin InvenTree generic machine web scim
fi

exec "$VENV_PYTHON" manage.py test "$@" \
    --keepdb \
    --exclude-tag migration_test \
    --exclude-tag performance_test \
    --verbosity 1