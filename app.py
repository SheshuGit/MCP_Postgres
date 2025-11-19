# This file serves as the main entry point for the Render web service, 
# integrating FastMCP with an ASGI server (Uvicorn) and adding a security layer.

import os
import uvicorn
import asyncio
# Import mcp and initialization function from your logic file
from mcp_server import mcp, initialize_db_pool 
from mcp.server.http import StreamableHttpTransport
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# --- Security Dependency ---
# Sets up the Bearer Token authentication schema
security = HTTPBearer()

def check_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Checks the Authorization: Bearer <TOKEN> header against the secret key (MCP_API_KEY)
    stored in the Render environment variables.
    """
    expected_key = os.getenv("MCP_API_KEY")
    
    # Critical Check: Ensure the secret key is configured on the server
    if not expected_key:
        print("SECURITY ERROR: MCP_API_KEY is not set in environment variables!")
        raise HTTPException(
            status_code=500, 
            detail="Server Misconfiguration: Authentication key missing.",
        )

    # Validate the token sent by the client
    if credentials.credentials != expected_key:
        raise HTTPException(
            status_code=401, 
            detail="Unauthorized access. Invalid MCP_API_KEY.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True

# --- Setup and Run ---

async def start_server():
    """Initializes the database pool and starts the Streamable HTTP Transport."""
    
    # 1. Initialize the Database (connection pool)
    # This must be done before the server starts accepting connections
    await initialize_db_pool() 
    
    # Render sets the PORT environment variable automatically.
    port = int(os.getenv("PORT", 8080))
    
    # 2. Configure the Streamable HTTP Transport
    # This handles the MCP JSON-RPC protocol messages over HTTP.
    transport = StreamableHttpTransport(
        server=mcp,
        host="0.0.0.0", 
        port=port,
        # Allow connections from any origin (required for a public web client like yours)
        cors_allow_origins=['*'], 
        cors_allow_headers=['*', 'Authorization', 'Mcp-Session-Id']
    )

    # 3. Get the core ASGI application object
    app = transport.get_app() 

    # 4. Add the security layer to the main MCP endpoints
    # All requests to /mcp MUST now include the correct Authorization header.
    @app.post("/mcp", dependencies=[Depends(check_auth)])
    @app.get("/mcp", dependencies=[Depends(check_auth)])
    async def protected_mcp_endpoint(request: Request):
        # Once authenticated, pass the request to the core MCP logic
        return await transport.handle_request(request)

    print(f"INFO: Starting secured Render-Postgres-Assistant on port {port}...")
    
    # 5. Start the Uvicorn server
    config = uvicorn.Config(app, host="0.0.0.0", port=port)
    server = uvicorn.Server(config)
    await server.serve()
    
if __name__ == '__main__':
    # Start the async runtime and the server
    asyncio.run(start_server())