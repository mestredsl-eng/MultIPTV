import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'database', 'iptv.db')

conn = sqlite3.connect(db_path)
db = conn.cursor()

print("Verificando estatísticas do dashboard...")
print("=" * 60)

# Verificar cada métrica individualmente

# Total de mídias
db.execute('SELECT COUNT(*) FROM midias WHERE status = 1')
midias = db.fetchone()[0]
print(f"midias: {midias}")

# Filmes
db.execute('SELECT COUNT(*) FROM midias WHERE categoria = "Movie" AND status = 1')
filmes = db.fetchone()[0]
print(f"filmes (Movie): {filmes}")

# Series
db.execute('SELECT COUNT(*) FROM midias WHERE categoria = "Series" AND status = 1')
series = db.fetchone()[0]
print(f"series (Series): {series}")

# TV
db.execute('SELECT COUNT(*) FROM midias WHERE categoria = "TV" AND status = 1')
tv = db.fetchone()[0]
print(f"tv (TV): {tv}")

# tv_channels
db.execute('SELECT COUNT(*) FROM tv_channels WHERE status = 1')
tv_channels = db.fetchone()[0]
print(f"tv_channels (tabela tv_channels): {tv_channels}")

# Duplicados
db.execute('''
    SELECT COUNT(*) FROM (
        SELECT hash_midia, COUNT(*) as cnt
        FROM midias
        WHERE status = 1
        GROUP BY hash_midia
        HAVING cnt > 1
    )
''')
duplicados = db.fetchone()[0]
print(f"duplicados (por hash_midia): {duplicados}")

# Blacklist
db.execute('SELECT COUNT(*) FROM midias WHERE black_list = 1')
blacklist = db.fetchone()[0]
print(f"blacklist: {blacklist}")

# Exportados
db.execute('SELECT COUNT(*) FROM exported_media')
exportados = db.fetchone()[0]
print(f"exportados (tabela exported_media): {exportados}")

# TMDB cache
db.execute('SELECT COUNT(*) FROM tmdb_cache')
tmdb_cache = db.fetchone()[0]
print(f"tmdb_cache: {tmdb_cache}")

# Outras categorias
categorias = ['Adult', 'Educational', 'Documentary', 'Cartoon', 'Novela', 'Sports']
for cat in categorias:
    db.execute(f'SELECT COUNT(*) FROM midias WHERE categoria = "{cat}" AND status = 1')
    count = db.fetchone()[0]
    print(f"{cat.lower()}: {count}")

# Verificar IPTVs
db.execute('SELECT COUNT(*) FROM iptvs WHERE ativo = 1')
iptvs = db.fetchone()[0]
print(f"iptvs: {iptvs}")

print("\n" + "=" * 60)
print("Problemas identificados:")
print("1. exportados mostra apenas entradas na tabela exported_media (não mídias exportadas)")
print("2. tv_channels mostra 0 porque a tabela tv_channels está vazia")
print("   - Deveria mostrar o número de mídias na categoria TV?")

conn.close()
