import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'database', 'iptv.db')

conn = sqlite3.connect(db_path)
db = conn.cursor()

print("Verificando classificação de TV...")
print("=" * 60)

# Verificar total de mídias classificadas como TV
db.execute('SELECT COUNT(*) FROM midias WHERE categoria = "TV" AND status = 1')
tv_count = db.fetchone()[0]
print(f"Total de mídias classificadas como TV: {tv_count}")

# Verificar quantas têm .TS no nome
db.execute('SELECT COUNT(*) FROM midias WHERE categoria = "TV" AND status = 1 AND nome_da_midia LIKE "%.ts%"')
ts_count = db.fetchone()[0]
print(f"Mídias TV com .TS no nome: {ts_count}")

# Verificar quantas têm VOID no nome
db.execute('SELECT COUNT(*) FROM midias WHERE categoria = "TV" AND status = 1 AND nome_da_midia LIKE "%VOID%"')
void_count = db.fetchone()[0]
print(f"Mídias TV com VOID no nome: {void_count}")

# Mostrar exemplos de mídias TV sem .TS
db.execute('''
    SELECT nome_da_midia, url 
    FROM midias 
    WHERE categoria = "TV" AND status = 1 
    AND nome_da_midia NOT LIKE "%.ts%"
    LIMIT 10
''')
print("\nExemplos de mídias TV sem .TS (primeiros 10):")
for row in db.fetchall():
    print(f"  - {row[0][:80]}...")
    print(f"    URL: {row[1][:80] if row[1] else 'N/A'}...")

# Mostrar exemplos de mídias TV com VOID
db.execute('''
    SELECT nome_da_midia, url 
    FROM midias 
    WHERE categoria = "TV" AND status = 1 
    AND nome_da_midia LIKE "%VOID%"
    LIMIT 10
''')
print("\nExemplos de mídias TV com VOID (primeiros 10):")
for row in db.fetchall():
    print(f"  - {row[0][:80]}...")
    print(f"    URL: {row[1][:80] if row[1] else 'N/A'}...")

print("\n" + "=" * 60)
print("Problema identificado:")
print(f"- {tv_count - ts_count} mídias classificadas como TV NÃO têm .TS no nome")
print(f"- {void_count} mídias classificadas como TV têm VOID no nome")
print("\nSolução:")
print("- Reclassificar mídias TV sem .TS para outras categorias")
print("- Reclassificar mídias com VOID para outras categorias (não TV)")

conn.close()
