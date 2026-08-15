from app.app import create_app

# Create app context
app = create_app()
with app.app_context():
    from app.database import get_db
    db = get_db()
    
    # Get sample data from each category
    categories = db.execute('''
        SELECT categoria, COUNT(*) as count
        FROM midias
        WHERE status = 1
        GROUP BY categoria
        ORDER BY count DESC
    ''').fetchall()
    
    print("CATEGORIAS EXISTENTES NO BANCO:")
    print("=" * 60)
    for cat in categories:
        print(f"{cat['categoria']}: {cat['count']}")
    print()
    
    # Get sample data from each category
    print("AMOSTRA DE DADOS POR CATEGORIA:")
    print("=" * 60)
    
    for cat in categories:
        categoria = cat['categoria']
        samples = db.execute('''
            SELECT nome_da_midia, nome_normalizado, url, origem_iptv, ano, season, episode
            FROM midias
            WHERE categoria = ? AND status = 1
            LIMIT 5
        ''', (categoria,)).fetchall()
        
        print(f"\nCategoria: {categoria} (Total: {cat['count']})")
        print("-" * 60)
        for sample in samples:
            print(f"  Nome: {sample['nome_da_midia'][:80]}")
            print(f"  Normalizado: {sample['nome_normalizado'][:80]}")
            print(f"  URL: {sample['url'][:80]}")
            print(f"  Origem: {sample['origem_iptv']}")
            print(f"  Ano: {sample['ano']}, Season: {sample['season']}, Episode: {sample['episode']}")
            print()
    
    # Analyze patterns in group_title, tvg_name, tvg_id if available
    print("ANÁLISE DE PADRÕES:")
    print("=" * 60)
    
    # Check if we have group_title, tvg_name, tvg_id columns
    columns = db.execute("PRAGMA table_info(midias)").fetchall()
    column_names = [col['name'] for col in columns]
    print(f"Colunas disponíveis: {column_names}")
    print()
    
    # Get sample of URLs to analyze patterns
    url_samples = db.execute('''
        SELECT categoria, url
        FROM midias
        WHERE status = 1
        LIMIT 20
    ''').fetchall()
    
    print("AMOSTRA DE URLs:")
    print("-" * 60)
    for sample in url_samples:
        print(f"{sample['categoria']}: {sample['url'][:100]}")
