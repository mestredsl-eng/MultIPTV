"""Executa script SQL de limpeza."""

import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).parent / 'database' / 'iptv.db'
SQL_FILE = Path(__file__).parent / 'cleanup_simple.sql'

conn = sqlite3.connect(DATABASE_PATH)

# Ler arquivo SQL
with open(SQL_FILE, 'r', encoding='utf-8') as f:
    sql_script = f.read()

# Executar script
try:
    conn.executescript(sql_script)
    conn.commit()
    print("✅ Script SQL executado com sucesso!")
except Exception as e:
    print(f"❌ Erro ao executar SQL: {e}")
    conn.rollback()

conn.close()
