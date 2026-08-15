import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'database', 'iptv.db')

conn = sqlite3.connect(db_path)
db = conn.cursor()

# Verificar quantas mídias têm "24H" no nome
db.execute('''
    SELECT COUNT(*)
    FROM midias
    WHERE nome_da_midia LIKE '%24H%'
''')
count = db.fetchone()[0]
print(f"Total de mídias com '24H' no nome: {count}")

# Verificar por categoria
db.execute('''
    SELECT categoria, COUNT(*)
    FROM midias
    WHERE nome_da_midia LIKE '%24H%'
    GROUP BY categoria
''')
categories = db.fetchall()
print("\nPor categoria:")
for cat, cnt in categories:
    print(f"  {cat}: {cnt}")

# Mostrar alguns exemplos
db.execute('''
    SELECT id, nome_da_midia, categoria
    FROM midias
    WHERE nome_da_midia LIKE '%24H%'
    LIMIT 10
''')
examples = db.fetchall()
print("\nExemplos:")
for ex in examples:
    print(f"  ID: {ex[0]} | Nome: {ex[1]} | Categoria: {ex[2]}")

# Marcar como blacklist
db.execute('''
    UPDATE midias
    SET black_list = 1
    WHERE nome_da_midia LIKE '%24H%' AND black_list = 0
''')
updated = db.rowcount
conn.commit()
print(f"\nMídias marcadas como blacklist: {updated}")

# Verificar o status final
db.execute('''
    SELECT COUNT(*)
    FROM midias
    WHERE nome_da_midia LIKE '%24H%' AND black_list = 1
''')
final_count = db.fetchone()[0]
print(f"Total de mídias com '24H' agora na blacklist: {final_count}")

conn.close()
