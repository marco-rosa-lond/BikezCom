import pyodbc
import os
from dotenv import load_dotenv
from pathlib import Path

# Automatically load .env if it exists
env_path = Path(__file__).resolve().parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)


DB_AUTH   = os.getenv("DB_AUTH")     # e.g. "SQL SERVER" or "WINDOWS"
DB_SERVER = os.getenv("DB_SERVER")   # e.g. "localhost\\SQLEXPRESS"
DB_NAME   = os.getenv("DB_NAME")
DB_USER   = os.getenv("DB_USER")
DB_PASS   = os.getenv("DB_PASS")
DB_PORT   = os.getenv("DB_PORT")

def get_connection(use_windows_auth=True):
    """
    Returns a pyodbc connection to SQL Server.
    Automatically detects whether to use SQL or Windows authentication
    based on environment variables.
    """

    # ✅ Automatically override auth mode if explicitly set to SQL Server
    if DB_AUTH and DB_AUTH.upper() == "SQL SERVER":
        use_windows_auth = False

    if not DB_SERVER or not DB_NAME:
        raise ValueError("❌ Missing required environment variables: DB_SERVER or DB_NAME")

    driver = "{ODBC Driver 18 for SQL Server}"

    # Optional port handling
    server_with_port = f"{DB_SERVER},{DB_PORT}" if DB_PORT else DB_SERVER

    # 🔹 Connection string
    if use_windows_auth:
        conn_str = (
            f"DRIVER={driver};"
            f"SERVER={server_with_port};"
            f"DATABASE={DB_NAME};"
            f"Trusted_Connection=yes;"
        )
    else:
        if not DB_USER or not DB_PASS:
            raise ValueError("❌ SQL authentication requires DB_USER and DB_PASS environment variables.")
        conn_str = (
            f"DRIVER={driver};"
            f"SERVER={server_with_port};"
            f"DATABASE={DB_NAME};"
            f"UID={DB_USER};"
            f"PWD={DB_PASS};"
            "Encrypt=no;TrustServerCertificate=yes;"
        )

    # 🔹 Attempt to connect
    try:
        conn = pyodbc.connect(conn_str)
        print("✅ Database connection established successfully.")
        return conn
    except pyodbc.Error as e:
        print(f"❌ Database connection failed: {e}")
        return None




def claim_next_model(conn):
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE TOP (1) dbo.Models WITH (ROWLOCK, UPDLOCK, READPAST)
    SET ScrapeStatus = 'in_progress', LastUpdated = SYSUTCDATETIME()
    OUTPUT inserted.Id, inserted.Url 
    WHERE ScrapeStatus = 'pending';
    """)
    row = cursor.fetchone()
    conn.commit()  # Commit via Python

    return row if row else None

 # [ScrapeStatus]='failed' OR [ScrapeStatus]='completed' OR [ScrapeStatus]='in_progress' OR [ScrapeStatus]='pending'

def mark_model_done(conn, model_id):
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE dbo.Models
    SET ScrapeStatus = 'completed', LastUpdated = GETDATE()
    WHERE ID = ?
    """, (model_id,))
    conn.commit()

def mark_model_failed(conn, model_id, error_msg):
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE dbo.Models
    SET ScrapeStatus = 'failed', LastUpdated = GETDATE()
    WHERE ID = ?
    """, (model_id,))
    conn.commit()
    cursor.execute("""
    INSERT INTO dbo.Failed (modelId, Url, Reason)
    VALUES (?, (SELECT Url FROM dbo.Models WHERE ID = ?), ?)
    """, (model_id, model_id, str(error_msg)[:900]))
    conn.commit()


def insert_specs(conn, model_id, specs):
    cursor = conn.cursor()
    for s in specs:
        cursor.execute("""
        IF NOT EXISTS (
            SELECT 1 FROM dbo.Details
            WHERE ModelId = ? AND Label = ? AND Text = ?
        )
        INSERT INTO dbo.Details (ModelId, Brand, SectionID, SectionDesc, Label, Text)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (model_id, s['label'], s['text'], model_id, s["brand"], s['section_id'], s['section_desc'], s['label'], s['text']))
    conn.commit()

def insert_model_html(conn, model_id, html):

    cursor = conn.cursor()
    cursor.execute("""
    MERGE dbo.Html AS target
    USING (SELECT ? AS modelId, ? AS HtmlContent) AS src
    ON target.modelId = src.modelId
    WHEN MATCHED THEN
        UPDATE SET HtmlContent = src.HtmlContent, RetrievedAt = GETDATE()
    WHEN NOT MATCHED THEN
        INSERT (modelId, HtmlContent) VALUES (src.modelId, src.HtmlContent);
    """, (model_id, html))
    conn.commit()
