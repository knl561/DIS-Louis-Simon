#!/usr/bin/env bash

# This script sets up our database by creating it and loading the tables and sample data.
# You can run it on Mac/Linux with: ./scripts/init_db.sh

set -e

# Default database name, unless we pass another one
DB_NAME="${DB_NAME:-movie_explorer}"
# Finds the root folder of our project
HERE="$(cd "$(dirname "$0")/.." && pwd)"

# Tries to create the database. If it's already there, it just skips without crashing
echo "Creating database '$DB_NAME' (ignore error if it already exists)…"
createdb "$DB_NAME" 2>/dev/null || true

# Runs our schema file to build all the tables, views, and triggers
echo "Loading schema…"
psql -d "$DB_NAME" -v ON_ERROR_STOP=1 -f "$HERE/db/schema.sql"

# Fills up the tables with our test movies and users
echo "Loading seed data…"
psql -d "$DB_NAME" -v ON_ERROR_STOP=1 -f "$HERE/db/seed.sql"

echo "Done. Database '$DB_NAME' is ready."
