import pyodbc
from contextlib import contextmanager
import os

# optional: load from env vars or config.py

def get_connection():
    conn_str = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=localhost;"
        "Database=BikezCom;"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)

@contextmanager
def get_cursor(commit=False):
    """Context manager to get a cursor and ensure cleanup."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        if commit:
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def execute_query(query, params=None, commit=False):
    """Quick helper for SELECT or DML operations."""
    with get_cursor(commit=commit) as cursor:
        cursor.execute(query, params or ())
        # if not commit:
        #     return cursor.fetchall()
        return cursor