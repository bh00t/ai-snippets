"""
MCP SERVER: Persistent SQLite School Database
----------------------------------------------
ROLE: This script provides the data. It sits and waits for the Client to 
request specific tools. It uses SQLite for "Thread-Safe" persistence on Windows.
"""

from mcp.server.fastmcp import FastMCP
import sqlite3
import json
import logging

# 1. LOGGING SETUP:
# In MCP, the server speaks to the client via 'stdout'. If we used print(),
# we would corrupt the data stream. We use a file log to see what's happening.
logging.basicConfig(
    filename='server.log', 
    level=logging.INFO, 
    format='%(asctime)s - [SERVER] %(levelname)s - %(message)s'
)

# 2. INITIALIZE FASTMCP:
# FastMCP is the framework that handles the 'Handshake' with the AI Client.
mcp = FastMCP("School Database Server")
DB_FILE = 'school.db'

def initialize_database():
    """
    Sets up the physical database file. 
    'check_same_thread=False' is the MAGIC FIX for Windows. It allows
    the Async loop to talk to the SQLite file without deadlocking.
    """
    logging.info(f"Connecting to persistent database: {DB_FILE}")
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    
    # Ensure our table exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            name TEXT,
            attendance_pct REAL,
            fees_paid INTEGER, 
            fees_due INTEGER
        )
    """)
    
    # Seed data if the file is new/empty
    cursor = conn.execute("SELECT COUNT(*) FROM students")
    if cursor.fetchone()[0] == 0:
        logging.info("Seeding initial student data...")
        students = [
            ('S001', 'Aarav Sharma', 91.5, 1, 0),
            ('S002', 'Priya Mehta', 63.2, 0, 18500),
            ('S003', 'Rohan Verma', 78.0, 1, 0),
            ('S004', 'Sneha Iyer', 54.1, 0, 22000)
        ]
        conn.executemany("INSERT INTO students VALUES (?, ?, ?, ?, ?)", students)
        conn.commit()
    
    return conn

# Establish the global database connection
db_conn = initialize_database()

# 3. TOOL DEFINITIONS:
# We use @mcp.tool() to tell the AI: "This Python function is a capability you can use."

@mcp.tool()
def get_attendance(student_id: str) -> str:
    """Queries the SQLite file for a student's attendance percentage."""
    logging.info(f"AI requested attendance for: {student_id}")
    try:
        cursor = db_conn.cursor()
        # .upper() handles 's004' vs 'S004'
        cursor.execute("SELECT name, attendance_pct FROM students WHERE student_id = ?", (student_id.upper(),))
        row = cursor.fetchone()
        
        if not row:
            return json.dumps({"error": "Student not found"})
        
        return json.dumps({"student_id": student_id.upper(), "name": row[0], "attendance_pct": row[1]})
    except Exception as e:
        logging.error(f"Database Error: {e}")
        return json.dumps({"error": str(e)})

@mcp.tool()
def get_fee_status(student_id: str) -> str:
    """Queries the SQLite file for a student's fee payment records."""
    logging.info(f"AI requested fees for: {student_id}")
    try:
        cursor = db_conn.cursor()
        cursor.execute("SELECT name, fees_paid, fees_due FROM students WHERE student_id = ?", (student_id.upper(),))
        row = cursor.fetchone()
        
        if not row:
            return json.dumps({"error": "Student not found"})
            
        return json.dumps({
            "student_id": student_id.upper(), 
            "name": row[0], 
            "fees_paid": bool(row[1]), 
            "fees_due": row[2]
        })
    except Exception as e:
        logging.error(f"Database Error: {e}")
        return json.dumps({"error": str(e)})

if __name__ == "__main__":
    # mcp.run() starts the 'stdio' loop, waiting for the Client to send JSON-RPC commands.
    mcp.run()