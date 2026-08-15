#!/usr/bin/env python3
import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / 'database' / 'iptv.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT id, nome_da_midia, black_list FROM midias WHERE nome_normalizado LIKE '%comvoce%' OR nome_normalizado LIKE '%comvoc%' ORDER BY nome_da_midia")
results = cursor.fetchall()

for row in results:
    print(f"{row[0]} | {row[1]} | blacklist={row[2]}")

conn.close()
