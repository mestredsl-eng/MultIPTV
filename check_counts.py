"""Check current counts in database."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'database' / 'iptv.db'
print(f"Database path: {DB_PATH}")
print(f"Database exists: {DB_PATH.exists()}")

db = sqlite3.connect(DB_PATH, timeout=30.0)
db.row_factory = sqlite3.Row

adult_count = db.execute('SELECT COUNT(*) FROM midias WHERE categoria="Adult" AND status=1 AND black_list=0').fetchone()[0]
movie_count = db.execute('SELECT COUNT(*) FROM midias WHERE categoria="Movie" AND status=1 AND black_list=0').fetchone()[0]

print(f'Adult (no blacklist): {adult_count}')
print(f'Movie (no blacklist): {movie_count}')

adult_count_all = db.execute('SELECT COUNT(*) FROM midias WHERE categoria="Adult" AND status=1').fetchone()[0]
movie_count_all = db.execute('SELECT COUNT(*) FROM midias WHERE categoria="Movie" AND status=1').fetchone()[0]

print(f'Adult (all): {adult_count_all}')
print(f'Movie (all): {movie_count_all}')

db.close()
