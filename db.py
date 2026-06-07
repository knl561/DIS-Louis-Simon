"""
This handles our connection to the Postgres database.

It looks for the DATABASE_URL environment variable (with passwords, etc.).
If it can't find it, it just defaults to a local connection without a password.
"""
import os
import psycopg2
import psycopg2.extras

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres@localhost:5432/movie_explorer",
)


def get_connection():
    """Opens the connection and returns rows as dicts instead of tuples so it's easier to use"""
    return psycopg2.connect(
        DATABASE_URL,
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


def query(sql, params=None):
    """For SELECT queries where we want to grab all matching rows"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()


def query_one(sql, params=None):
    """For SELECT queries where we only need the very first row (or None)"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchone()


def execute(sql, params=None):
    """For INSERT, UPDATE, and DELETE. It runs the query and commits the changes"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
        conn.commit()
