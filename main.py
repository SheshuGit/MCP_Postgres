from mcp.server.fastmcp import FastMCP
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}

mcp = FastMCP("PostgresMCP")

def get_conn():
    return psycopg2.connect(**DB_CONFIG)

@mcp.tool()
def list_tables() -> list[str]:
    query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema='public'
        ORDER BY table_name;
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            return [row[0] for row in cur.fetchall()]

@mcp.tool()
def describe_table(table_name: str) -> list[dict]:
    query = """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name=%s
        ORDER BY ordinal_position;
    """
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (table_name,))
            return cur.fetchall()

@mcp.tool()
def run_select(query: str) -> list[dict]:
    if "select" not in query.lower():
        raise ValueError("Only SELECT queries allowed.")
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            return cur.fetchall()

@mcp.tool()
def run_sql(query: str) -> str:
    blocked = ["drop", "alter", "truncate", "create"]
    if any(x in query.lower() for x in blocked):
        raise ValueError("DDL commands not allowed.")
    if query.lower().strip().startswith("select"):
        raise ValueError("Use run_select() for SELECT.")

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            conn.commit()
            return f"Executed successfully. Rows affected: {cur.rowcount}"

@mcp.resource("pg://preview/{table}")
def preview_table(table: str) -> list[dict]:
    query = f"SELECT * FROM {table} LIMIT 10"
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            return cur.fetchall()

@mcp.prompt()
def sql_prompt(nl: str) -> str:
    return (
        "Convert the following natural language request into an SQL query. "
        "Return only SQL.\n\nRequest:\n" + nl
    )

def main():
    # Initialize and run the server
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()