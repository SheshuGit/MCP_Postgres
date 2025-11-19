
import os
import asyncpg
from mcp.server.fastmcp import FastMCP
from typing import List, Dict, Any

# --- Configuration & Global State ---

mcp = FastMCP("Render-Postgres-Assistant")

# Global variable to hold the async connection pool
db_pool = None

async def initialize_db_pool():
    """Initializes the global asynchronous connection pool using environment variables.
    
    This function reads DB credentials from environment variables set on the Render dashboard.
    """
    global db_pool
    if db_pool is not None:
        return

    # Connection parameters read from Render Environment Variables
    DB_CONFIG = {
        "host": os.getenv("DB_HOST"),
        "port": int(os.getenv("DB_PORT", 5432)),
        "database": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD")
    }

    try:
        # Create a connection pool for efficient, non-blocking connections
        db_pool = await asyncpg.create_pool(**DB_CONFIG)
        print("INFO: PostgreSQL Connection Pool initialized successfully.")
    except Exception as e:
        print(f"ERROR: Failed to connect to PostgreSQL: {e}")
        # Critical failure: Stop service startup if DB connection fails
        raise 


@mcp.tool()
async def list_tables() -> List[str]:
    """Returns a list of all table names in the public schema of the database."""
    await initialize_db_pool()
    query = "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name;"
    
    async with db_pool.acquire() as conn:
        records = await conn.fetch(query)
        return [row[0] for row in records]

@mcp.tool()
async def describe_table(table_name: str) -> List[Dict[str, Any]]:
    """Returns the schema (column names, types, and constraints) for a specified table."""
    await initialize_db_pool()
    query = """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name=$1
        ORDER BY ordinal_position;
    """
    async with db_pool.acquire() as conn:
        # asyncpg uses $1, $2, etc. for parameterized queries
        records = await conn.fetch(query, table_name) 
        return [dict(r) for r in records]

@mcp.tool()
async def run_select(query: str) -> List[Dict[str, Any]]:
    """
    Executes a read-only SQL SELECT query against the database and returns the results.
    """
    await initialize_db_pool()
    if "select" not in query.strip().lower():
        raise ValueError("Only SELECT queries allowed for data retrieval.")
    
    async with db_pool.acquire() as conn:
        records = await conn.fetch(query)
        return [dict(r) for r in records]

@mcp.tool()
async def run_sql(query: str) -> str:
    """
    Executes a non-SELECT SQL command (INSERT, UPDATE, DELETE) and returns the number of rows affected.
    DDL commands (DROP, ALTER, CREATE) are explicitly blocked for safety.
    """
    await initialize_db_pool()
    blocked = ["drop", "alter", "truncate", "create"]
    
    if any(x in query.lower() for x in blocked):
        raise ValueError("DDL commands not allowed.")
    if query.strip().lower().startswith("select"):
        raise ValueError("Use run_select() for SELECT queries.")

    async with db_pool.acquire() as conn:
        # execute() runs the command and returns a status string like "UPDATE 1"
        result = await conn.execute(query) 
        rows_affected = result.split()[-1] 
        return f"Executed successfully. Rows affected: {rows_affected}"

@mcp.resource("pg://preview/{table}")
async def preview_table(table: str) -> List[Dict[str, Any]]:
    """Returns the first 10 rows of data from the specified table for preview."""
    await initialize_db_pool()
    query = f"SELECT * FROM {table} LIMIT 10"
    async with db_pool.acquire() as conn:
        records = await conn.fetch(query)
        return [dict(r) for r in records]

@mcp.prompt()
def sql_prompt(nl: str) -> str:
    """A prompt template to guide the LLM to generate SQL from natural language."""
    return (
        "Convert the following natural language request into an SQL query. "
        "Return only SQL.\n\nRequest:\n" + nl
    )