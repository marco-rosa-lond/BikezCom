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

    driver = "{ODBC Driver 18 for SQL Server}"  # Adjust if you use 18+

    # Optional port handling
    server_with_port = f"{DB_SERVER},{DB_PORT}" if DB_PORT else DB_SERVER

    # 🔹 Connection string
    if use_windows_auth:
        conn_str = (
            f"DRIVER={driver};"
            f"SERVER={server_with_port};"
            f"DATABASE={DB_NAME};"
            f"Trusted_Connection=yes;"
            "Encrypt=no;TrustServerCertificate=yes;"

        )
    else:
        if not DB_USER or not DB_PASS:
            raise ValueError("❌ SQL authentication requires DB_USER and DB_PASS environment variables.")
        conn_str = (
            f"DRIVER={driver};"
            f"SERVER={server_with_port};"
            f"DATABASE={DB_NAME};"
            f"UID={DB_USER};PWD={DB_PASS};"
            "Encrypt=no;TrustServerCertificate=yes;"
        )

    print(conn_str)
    # 🔹 Attempt to connect
    try:
        conn = pyodbc.connect(conn_str)
        print("✅ Database connection established successfully.")
        return conn
    except pyodbc.Error as e:
        print(f"❌ Database connection failed: {e}")
        return None



def insert_new_model(conn, model_url, year, model_name, rating_url):
    cursor = conn.cursor()
    cursor.execute("""
        MERGE dbo.Models AS target
        USING (SELECT ? AS Url, ? AS Year, ? AS ModelName, ? AS RatingUrl) AS source
        ON target.Url = source.Url
        WHEN NOT MATCHED THEN
            INSERT (Url, Year, ModelName, RatingUrl)
            VALUES (source.Url, source.Year, source.ModelName, source.RatingUrl)
        OUTPUT $action;
    """, (model_url, year, model_name, rating_url))

    result = cursor.fetchone()
    conn.commit()

    if result and result[0] == "INSERT":
        print(f"✅ Inserted new model: {model_name} ({year})")
        return True
    else:
        print(f"⚠️ Already exists: {model_name} ({year})")
        return False




def insert_new_brand(conn, name, url):
    cursor = conn.cursor()
    cursor.execute("""
        MERGE dbo.Brands AS target
        USING (SELECT ? AS Name, ? AS Href) AS source
        ON target.Href = source.Href
        WHEN MATCHED THEN
            UPDATE SET LastUpdated = SYSUTCDATETIME()
        WHEN NOT MATCHED THEN
            INSERT (Name, Href)
            VALUES (source.Name, source.Href)
        OUTPUT $action;
    """, (name, url))

    result = cursor.fetchone()
    conn.commit()

    if result and result[0] == "INSERT":
        print(f"✅ Inserted new brand: {name} ({url})")
        return True
    else:
        print(f"⚠️ Already exists: {name} ({url})")
        return False

