#!/usr/bin/env bash
# ------------------------------------------------------------
#  Initialise the Movie Explorer database.
#  Creates the database (if missing) and runs schema.sql + seed.sql.
#
#  Usage:
#     ./scripts/init_db.sh
#
#  Override connection details with environment variables, e.g.:
#     PGUSER=postgres PGHOST=localhost DB_NAME=movie_explorer ./scripts/init_db.sh
# ------------------------------------------------------------
set -e

DB_NAME="${DB_NAME:-movie_explorer}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"

echo "Creating database '$DB_NAME' (ignore error if it already exists)…"
createdb "$DB_NAME" 2>/dev/null || true

echo "Loading schema…"
psql -d "$DB_NAME" -v ON_ERROR_STOP=1 -f "$HERE/db/schema.sql"

echo "Loading seed data…"
psql -d "$DB_NAME" -v ON_ERROR_STOP=1 -f "$HERE/db/seed.sql"

echo "Done. Database '$DB_NAME' is ready."
