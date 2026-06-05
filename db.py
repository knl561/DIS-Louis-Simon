"""
Database access layer for Movie Explorer.

Connection settings come from the DATABASE_URL environment variable, e.g.:
    postgresql://USER:PASSWORD@localhost:5432/movie_explorer

If DATABASE_URL is not set, it falls back to a sensible local default.
"""
import os
import psycopg2
import psycopg2.extras

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres@localhost:5432/movie_explorer",
)


def get_connection():
    """Open a new connection. Rows come back as dict-like objects."""
    return psycopg2.connect(
        DATABASE_URL,
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


def query(sql, params=None):
    """Run a SELECT and return all rows as a list of dicts."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()


def query_one(sql, params=None):
    """Run a SELECT and return the first row (or None)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchone()


def execute(sql, params=None):
    """Run an INSERT/UPDATE/DELETE inside a transaction."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
        conn.commit()
