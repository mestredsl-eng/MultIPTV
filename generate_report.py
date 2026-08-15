from app.app import create_app
from pathlib import Path

# Create app context
app = create_app()
with app.app_context():
    from app.database import get_db
    db = get_db()
    
    # Get statistics
    stats = {
        'iptvs': db.execute('SELECT COUNT(*) FROM iptvs WHERE ativo = 1').fetchone()[0],
        'midias': db.execute('SELECT COUNT(*) FROM midias WHERE status = 1').fetchone()[0],
        'filmes': db.execute("SELECT COUNT(*) FROM midias WHERE categoria = 'Movie' AND status = 1").fetchone()[0],
        'series': db.execute("SELECT COUNT(*) FROM midias WHERE categoria = 'Series' AND status = 1").fetchone()[0],
        'tv': db.execute('SELECT COUNT(*) FROM tv_channels WHERE status = 1').fetchone()[0],
        'duplicados': db.execute('SELECT COUNT(*) FROM midias WHERE black_list = 1').fetchone()[0],
        'exportados': db.execute('SELECT COUNT(*) FROM exported_media').fetchone()[0],
        'tmdb_cache': db.execute('SELECT COUNT(*) FROM tmdb_cache').fetchone()[0],
    }
    
    # Get categories breakdown
    categories = db.execute('''
        SELECT categoria, COUNT(*) as count
        FROM midias
        WHERE status = 1
        GROUP BY categoria
        ORDER BY count DESC
    ''').fetchall()
    
    # Get execution stats
    execution_stats = db.execute('''
        SELECT tipo_execucao, inicio, fim, duracao_segundos, itens_novos, itens_ignorados, itens_exportados, status
        FROM execution_stats
        ORDER BY inicio DESC
        LIMIT 10
    ''').fetchall()
    
    # Get database size
    db_path = Path(__file__).parent.parent / 'database' / 'iptv.db'
    db_size_mb = db_path.stat().st_size / (1024 * 1024) if db_path.exists() else 0
    
    print("=" * 60)
    print("RELATÓRIO FINAL - MESTRE IPTV MANAGER")
    print("=" * 60)
    print()
    print("ESTATÍSTICAS GERAIS:")
    print(f"  Fontes IPTV: {stats['iptvs']}")
    print(f"  Total de Mídias: {stats['midias']}")
    print(f"  Filmes: {stats['filmes']}")
    print(f"  Séries: {stats['series']}")
    print(f"  Canais TV: {stats['tv']}")
    print(f"  Duplicados/Blacklist: {stats['duplicados']}")
    print(f"  Exportados (STRM): {stats['exportados']}")
    print(f"  Cache TMDB: {stats['tmdb_cache']}")
    print()
    print("BREAKDOWN POR CATEGORIA:")
    for cat in categories:
        print(f"  {cat['categoria']}: {cat['count']}")
    print()
    print("TAMANHO DO BANCO DE DADOS:")
    print(f"  {db_size_mb:.2f} MB")
    print()
    print("ÚLTIMAS EXECUÇÕES:")
    for exec_stat in execution_stats:
        print(f"  {exec_stat['tipo_execucao']}: {exec_stat['status']} ({exec_stat['duracao_segundos']}s)")
        print(f"    Itens novos: {exec_stat['itens_novos']}, Ignorados: {exec_stat['itens_ignorados']}, Exportados: {exec_stat['itens_exportados']}")
    print()
    print("=" * 60)
