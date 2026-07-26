import os

# ──────────────────────────────────────────────────────────────
# MySQL Database Configuration
# Supports:
# 1. Railway (Production)
# 2. Local MySQL (Development)
# ──────────────────────────────────────────────────────────────

DB_CONFIG = {
    "host": os.getenv("MYSQLHOST", "localhost"),
    "port": int(os.getenv("MYSQLPORT", "3306")),
    "user": os.getenv("MYSQLUSER", "root"),
    "password": os.getenv("MYSQLPASSWORD", ""),
    "database": os.getenv("MYSQLDATABASE", "placement"),
    "connection_timeout": 5,
    "autocommit": False,
}