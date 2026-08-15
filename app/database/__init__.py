import sqlite3
from pathlib import Path
from flask import g
import os

# Use environment variable for database path with fallback
DATABASE_PATH = Path(os.environ.get('DATABASE_PATH', Path(__file__).parent.parent.parent / 'database' / 'iptv.db'))

def get_db():
    """Get database connection for current request."""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE_PATH, timeout=120.0)
        g.db.row_factory = sqlite3.Row
        # Enable WAL mode for better concurrency
        g.db.execute('PRAGMA journal_mode=WAL')
        g.db.execute('PRAGMA busy_timeout=120000')  # 120 seconds
        g.db.execute('PRAGMA synchronous=NORMAL')  # Better performance with good safety
        g.db.execute('PRAGMA cache_size=-10000')  # 10MB cache for better performance
        g.db.execute('PRAGMA temp_store=MEMORY')  # Store temp tables in memory
        g.db.execute('PRAGMA mmap_size=268435456')  # 256MB memory-mapped I/O for better performance
    return g.db

def close_db(e=None):
    """Close database connection."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Initialize database with schema."""
    # FIXED: Create database directory if it doesn't exist
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    db = sqlite3.connect(DATABASE_PATH)
    
    # Check if database exists and has tables
    cursor = db.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    if not tables:
        # Run migration
        migration_path = Path(__file__).parent / 'migrations' / '0001_init.sql'
        with open(migration_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        cursor.executescript(sql_script)
        db.commit()
        print("Database initialized successfully.")
    else:
        print("Database already exists.")
    
    db.close()

def get_schema_version():
    """Get current schema version."""
    db = sqlite3.connect(DATABASE_PATH)
    cursor = db.cursor()
    cursor.execute("PRAGMA user_version")
    version = cursor.fetchone()[0]
    db.close()
    return version
