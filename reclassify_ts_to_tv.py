import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'database', 'iptv.db')

conn = sqlite3.connect(db_path)
db = conn.cursor()

# Verificar quantas mídias têm .ts no nome ou URL e NÃO estão na categoria TV
db.execute('''
    SELECT COUNT(*)
    FROM midias
    WHERE (nome_da_midia LIKE '%.ts%' OR url LIKE '%.ts%')
    AND categoria != 'TV'
''')
count = db.fetchone()[0]
print(f"Total de mídias com .ts que NÃO estão na categoria TV: {count}")

# Verificar por categoria antes da reclassificação
db.execute('''
    SELECT categoria, COUNT(*)
    FROM midias
    WHERE (nome_da_midia LIKE '%.ts%' OR url LIKE '%.ts%')
    AND categoria != 'TV'
    GROUP BY categoria
''')
categories = db.fetchall()
print("\nDistribuição por categoria (antes da reclassificação):")
for cat, cnt in categories:
    print(f"  {cat}: {cnt}")

# Reclassificar todas as mídias com .ts para TV
db.execute('''
    UPDATE midias
    SET categoria = 'TV'
    WHERE (nome_da_midia LIKE '%.ts%' OR url LIKE '%.ts%')
    AND categoria != 'TV'
''')
updated = db.rowcount
conn.commit()
print(f"\nMídias reclassificadas para TV: {updated}")

# Verificar o status final
db.execute('''
    SELECT COUNT(*)
    FROM midias
    WHERE (nome_da_midia LIKE '%.ts%' OR url LIKE '%.ts%')
    AND categoria = 'TV'
''')
final_count = db.fetchone()[0]
print(f"Total de mídias com .ts agora na categoria TV: {final_count}")

# Verificar se ainda há alguma mídia com .ts fora de TV
db.execute('''
    SELECT COUNT(*)
    FROM midias
    WHERE (nome_da_midia LIKE '%.ts%' OR url LIKE '%.ts%')
    AND categoria != 'TV'
''')
remaining = db.fetchone()[0]
if remaining > 0:
    print(f"\n⚠️  Ainda há {remaining} mídias com .ts fora de TV")
else:
    print(f"\n✓ Todas as mídias com .ts agora estão na categoria TV")

conn.close()
