import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'database', 'iptv.db')

conn = sqlite3.connect(db_path)
db = conn.cursor()

# Verificar quantas mídias têm .ts no nome ou URL
db.execute('''
    SELECT COUNT(*)
    FROM midias
    WHERE (nome_da_midia LIKE '%.ts%' OR url LIKE '%.ts%')
''')
count = db.fetchone()[0]
print(f"Total de mídias com .ts no nome ou URL: {count}")

# Verificar por categoria
db.execute('''
    SELECT categoria, COUNT(*)
    FROM midias
    WHERE (nome_da_midia LIKE '%.ts%' OR url LIKE '%.ts%')
    GROUP BY categoria
''')
categories = db.fetchall()
print("\nPor categoria:")
for cat, cnt in categories:
    print(f"  {cat}: {cnt}")

# Mostrar alguns exemplos de não-TV com .ts
db.execute('''
    SELECT id, nome_da_midia, categoria, url
    FROM midias
    WHERE (nome_da_midia LIKE '%.ts%' OR url LIKE '%.ts%')
    AND categoria != 'TV'
    LIMIT 20
''')
examples = db.fetchall()
print("\nExemplos de não-TV com .ts:")
for ex in examples:
    url_preview = ex[3][:50] if ex[3] else 'N/A'
    print(f"  ID: {ex[0]} | Nome: {ex[1]} | Categoria: {ex[2]} | URL: {url_preview}...")

# Verificar se existe VOID.ts na galeria
galeria_path = os.path.join(os.path.dirname(__file__), 'galeria')
void_ts_path = os.path.join(galeria_path, 'VOID.ts')
if os.path.exists(void_ts_path):
    print(f"\n⚠️  ARQUIVO VOID.ts ENCONTRADO EM: {void_ts_path}")
else:
    print(f"\n✓ Arquivo VOID.ts não encontrado")

# Buscar por arquivos .ts na galeria
print("\nBuscando arquivos .ts na galeria...")
for root, dirs, files in os.walk(galeria_path):
    for file in files:
        if file.endswith('.ts'):
            full_path = os.path.join(root, file)
            print(f"  Encontrado: {full_path}")

conn.close()
