
# 🏥 Hospital MCP Server  
Secure PostgreSQL Access via Model Context Protocol (MCP)  
**Claude Desktop acts as the MCP client**

This project implements a secure **Model Context Protocol (MCP)** server that connects to a PostgreSQL-based Hospital Management System.  
Claude Desktop communicates with this server and can safely query hospital data through defined, read-only MCP tools.

---

# 📁 Project Structure

```

MY-FIRST-MCP-SERVER/
│
├── .venv/                # Virtual environment
├── .env                  # Environment variables (DB credentials)
├── .gitignore
├── .python-version
├── main.py               # MCP server implementation
├── pyproject.toml        # Project dependencies (uv/poetry/pdm)
├── README.md             # This documentation
└── uv.lock               # Dependency lockfile

````

---

# 🗄️ 1. PostgreSQL Setup

You must create **secure read-only views** before exposing data to Claude.

### Create Views (Safe, non-sensitive)

```sql
CREATE VIEW doctors_view AS
SELECT doctor_id, department_id, specialization
FROM Doctors;

CREATE VIEW departments_view AS
SELECT department_id, name, head_doctor_id
FROM Departments;

CREATE VIEW public_appointments_view AS
SELECT appointment_id, patient_id, doctor_id, appointment_date
FROM Appointments;

CREATE VIEW rooms_view AS
SELECT room_id, room_number, current_status
FROM Rooms;

CREATE VIEW billing_summary_view AS
SELECT bill_id, patient_id, appointment_id, admission_id, total_amount
FROM Billing;
````

---

# 🔐 2. Create Restricted DB Role

```sql
CREATE ROLE mcp_readonly LOGIN PASSWORD 'your_password';

GRANT SELECT ON doctors_view TO mcp_readonly;
GRANT SELECT ON departments_view TO mcp_readonly;
GRANT SELECT ON public_appointments_view TO mcp_readonly;
GRANT SELECT ON rooms_view TO mcp_readonly;
GRANT SELECT ON billing_summary_view TO mcp_readonly;

REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM mcp_readonly;

ALTER ROLE mcp_readonly SET statement_timeout = '3s';
ALTER ROLE mcp_readonly SET idle_in_transaction_session_timeout = '2s';
```

Only the views are exposed — raw PHI tables are protected.

---

# ⚙️ 3. Environment Variables (`.env`)

Your MCP server reads DB credentials from here:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=hospital_db
DB_USER=mcp_readonly
DB_PASSWORD=your_password
```

---

# 🧠 4. MCP Server (`main.py`)

`main.py` runs your MCP server and exposes tools such as:

* `get_doctor_by_id`
* `list_doctors_by_department`
* `get_appointments_for_doctor`
* `check_room_status`
* `get_patient_billing_summary`

All SQL queries are:

✔ parameterized
✔ read-only
✔ safely constrained

---

# 🔌 5. Installing Dependencies

Inside your project folder:

```bash
uv sync
```

Or if using pip manually:

```bash
pip install -r requirements.txt
```

(Dependencies are defined in `pyproject.toml`)

---

# 🤝 6. Connecting MCP Server to Claude Desktop

Claude Desktop automatically detects MCP servers placed in its extensions directory.


### `In your local file system  "C:\Users\shesh\AppData\Roaming\Claude\claude_desktop_config.json" edit this file with your configurations`

```json
{
  "mcpServers": {
    "postgres": {
      "command": "C:\\Users\\shesh\\my-first-mcp-server\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\shesh\\my-first-mcp-server\\main.py",
        "stdio"
      ],
      "cwd": "C:\\Users\\shesh\\my-first-mcp-server",
      "env": {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_NAME": "db_name",
        "DB_USER": "postgres",
        "DB_PASSWORD": "your_password"
      }
    }
  }
}
```

---

### 📍 **Step 3 — Restart Claude Desktop**

Go to:

**Claude Desktop → Settings → Developer**
You should see:

```
hospital-mcp (running)
```


Claude will now:

1. Launch your `main.py` MCP server
2. Discover available tools
3. Call them automatically during conversation

---

# 🧪 7. Testing Inside Claude

In Claude Desktop you can ask:

```
Get the list of doctors in the cardiology department.
```

Claude will call:

```
list_doctors_by_department(department_id=1)
```

Or:

```
Show me appointments for doctor 3.
```

Claude → calls your MCP tool → your DB → safe output returned.

---

# 🎯 Summary

You now have:

✔ A working **Python MCP server**
✔ Secure **PostgreSQL integration**
✔ Fully wired **Claude Desktop tool access**
✔ Safe read-only hospital data views
✔ Clean project structure

Claude Desktop communicates with your DB **only through your safe MCP tools**, never accessing raw tables directly.



