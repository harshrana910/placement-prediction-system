import os

# ── MySQL Database Configuration ─────────────────────────────────────────────
# All values are read from environment variables first.
# If no environment variable is set, the local defaults below are used.
#
# To override (Windows PowerShell):
#   $env:MYSQL_PASSWORD = "your_password"
#   python app.py
#
# To override (Command Prompt):
#   set MYSQL_PASSWORD=your_password
#   python app.py
# ─────────────────────────────────────────────────────────────────────────────

DB_CONFIG = {
    "host":               os.environ.get("MYSQL_HOST",     "localhost"),
    "port":               int(os.environ.get("MYSQL_PORT", 3306)),
    "user":               os.environ.get("MYSQL_USER",     "root"),
    "password":           os.environ.get("MYSQL_PASSWORD", ""),
    "database":           os.environ.get("MYSQL_DATABASE", "placement"),
    "connection_timeout": 5,   # fail fast if MySQL is unreachable
}
