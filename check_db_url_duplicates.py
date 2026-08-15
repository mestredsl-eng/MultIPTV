import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'database', 'iptv.db')

conn = sqlite3.connect(db_path)
db = conn.cursor()

# Verificar duplicados por URL
db.execute('''
    SELECT url, COUNT(*) as cnt
    FROM midias
    WHERE status = 1 AND black_list = 0 AND url IS NOT NULL
    GROUP BY url
    HAVING cnt > 1
    ORDER BY cnt DESC
''')
url_duplicates = db.fetchall()

print(f"Total de URLs duplicadas no banco: {len(url_duplicates)}")
print(f"Total de ocorrências duplicadas: {sum(row[1] for row in url_duplicates)}")

# Mostrar exemplos
print("\nExemplos de URLs duplicadas (primeiros 10):")
for url, cnt in url_duplicates[:10]:
    print(f"\nURL: {url[:80]}...")
    print(f"  Ocorrências: {cnt}")
    
    # Verificar categorias
    db.execute('''
        SELECT categoria, COUNT(*) as cnt
        FROM midias
        WHERE url = ?
        GROUP BY categoria
    ''', (url,))
    categories = db.fetchall()
    print(f"  Categorias: {', '.join(f'{cat} ({cnt})' for cat, cnt in categories)}")

# Verificar duplicados por hash_midia
db.execute('''
    SELECT hash_midia, COUNT(*) as cnt
    FROM midias
    WHERE status = 1 AND black_list = 0 AND hash_midia IS NOT NULL
    GROUP BY hash_midia
    HAVING cnt > 1
    ORDER BY cnt DESC
''')
hash_duplicates = db.fetchall()

print(f"\nTotal de hash_midia duplicados no banco: {len(hash_duplicates)}")
print(f"Total de ocorrências duplicadas: {sum(row[1] for row in hash_duplicates)}")

# Verificar se há mídias com mesma URL mas hash_midia diferentes
db.execute('''
    SELECT url, COUNT(DISTINCT hash_midia) as distinct_hashes
    FROM midias
    WHERE status = 1 AND black_list = 0 AND url IS NOT NULL
    GROUP BY url
    HAVING distinct_hashes > 1
    ORDER BY distinct_hashes DESC
''')
url_multiple_hashes = db.fetchall()

print(f"\nTotal de URLs com múltiplos hash_midia: {len(url_multiple_hashes)}")

print("\nExemplos de URLs com múltiplos hash_midia (primeiros 10):")
for url, distinct_hashes in url_multiple_hashes[:10]:
    print(f"\nURL: {url[:80]}...")
    print(f"  Hash_midia diferentes: {distinct_hashes}")
    
    db.execute('''
        SELECT hash_midia, categoria, nome_da_midia
        FROM midias
        WHERE url = ?
        LIMIT 5
    ''', (url,))
    items = db.fetchall()
    for item in items:
        print(f"    Hash: {item[0]} | Categoria: {item[1]} | Nome: {item[2][:50]}...")

conn.close()
