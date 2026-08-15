import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'database', 'iptv.db')

conn = sqlite3.connect(db_path)
db = conn.cursor()

# Verificar o total de entradas na tabela exported_media
db.execute('SELECT COUNT(*) FROM exported_media')
total_exported = db.fetchone()[0]
print(f"Total de entradas em exported_media: {total_exported}")

# Limpar a tabela exported_media para forçar reexportação
db.execute('DELETE FROM exported_media')
conn.commit()
print("Tabela exported_media limpa")

# Verificar o total de mídias ativas
db.execute('''
    SELECT COUNT(*)
    FROM midias
    WHERE status = 1 AND black_list = 0
''')
total_active = db.fetchone()[0]
print(f"Total de mídias ativas: {total_active}")

conn.close()
