import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'database', 'iptv.db')

conn = sqlite3.connect(db_path)
db = conn.cursor()

# Encontrar URLs duplicadas
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

# Para cada URL duplicada, manter apenas uma entrada (preferir a categoria mais específica)
removed_count = 0
for url, cnt in url_duplicates:
    # Buscar todas as entradas com esta URL
    db.execute('''
        SELECT id, categoria, nome_da_midia, hash_midia
        FROM midias
        WHERE url = ? AND status = 1 AND black_list = 0
        ORDER BY id
    ''', (url,))
    items = db.fetchall()
    
    if len(items) <= 1:
        continue
    
    # Manter a primeira entrada, remover as outras
    keep_id = items[0][0]
    print(f"\nURL: {url[:60]}...")
    print(f"  Mantendo: ID {keep_id} ({items[0][1]}): {items[0][2][:50]}...")
    
    for item in items[1:]:
        remove_id = item[0]
        print(f"  Removendo: ID {remove_id} ({item[1]}): {item[2][:50]}...")
        
        # Marcar como status = 0 (inativo) em vez de deletar
        db.execute('''
            UPDATE midias
            SET status = 0
            WHERE id = ?
        ''', (remove_id,))
        removed_count += 1

conn.commit()

print(f"\nTotal de entradas marcadas como inativas: {removed_count}")

# Verificar o status final
db.execute('''
    SELECT COUNT(*)
    FROM midias
    WHERE status = 1 AND black_list = 0
''')
final_count = db.fetchone()[0]
print(f"Total de mídias ativas após limpeza: {final_count}")

# Verificar se ainda há duplicados por URL
db.execute('''
    SELECT COUNT(*)
    FROM (
        SELECT url, COUNT(*) as cnt
        FROM midias
        WHERE status = 1 AND black_list = 0 AND url IS NOT NULL
        GROUP BY url
        HAVING cnt > 1
    )
''')
remaining_duplicates = db.fetchone()[0]
if remaining_duplicates > 0:
    print(f"⚠️  Ainda há {remaining_duplicates} URLs duplicadas")
else:
    print(f"✓ Não há mais URLs duplicadas")

conn.close()
