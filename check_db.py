import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).parent / 'database' / 'iptv.db'
db = sqlite3.connect(DATABASE_PATH)
tables = db.execute('SELECT name FROM sqlite_master WHERE type="table"').fetchall()
print("Tables in database:")
for table in tables:
    print(f"  - {table[0]}")

version = db.execute('PRAGMA user_version').fetchone()[0]
print(f"\nSchema version: {version}")
db.close()
