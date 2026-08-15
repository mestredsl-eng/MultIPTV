from app.app import create_app

# Create app context
app = create_app()
with app.app_context():
    from app.database import get_db
    db = get_db()
    
    print("VERIFICANDO TMDB CACHE:")
    print("=" * 60)
    
    # Check tmdb_cache table
    tmdb_cache_count = db.execute('SELECT COUNT(*) as count FROM tmdb_cache').fetchone()
    print(f"Total de registros em tmdb_cache: {tmdb_cache_count['count']}")
    
    # Check midias with tmdb_id
    midias_with_tmdb = db.execute('SELECT COUNT(*) as count FROM midias WHERE tmdb_id IS NOT NULL AND status = 1').fetchone()
    print(f"Total de midias com tmdb_id preenchido: {midias_with_tmdb['count']}")
    
    # Check midias without tmdb_id (Movie and Series)
    midias_movie = db.execute('SELECT COUNT(*) as count FROM midias WHERE categoria = "Movie" AND tmdb_id IS NULL AND status = 1').fetchone()
    midias_series = db.execute('SELECT COUNT(*) as count FROM midias WHERE categoria = "Series" AND tmdb_id IS NULL AND status = 1').fetchone()
    
    print(f"Total de Movies sem tmdb_id: {midias_movie['count']}")
    print(f"Total de Series sem tmdb_id: {midias_series['count']}")
    
    print()
    print(f"Total de Movies e Series que poderiam ter tmdb_id: {midias_movie['count'] + midias_series['count']}")
    
    print()
    
    # Check some examples from tmdb_cache
    if tmdb_cache_count['count'] > 0:
        cache_examples = db.execute('SELECT * FROM tmdb_cache LIMIT 5').fetchall()
        print("EXEMPLOS DE TMDB CACHE:")
        for ex in cache_examples:
            query = ex['query'][:50] if 'query' in ex else 'N/A'
            tmdb_id = ex['tmdb_id'] if 'tmdb_id' in ex else 'N/A'
            print(f"  Query: {query}... | TMDB ID: {tmdb_id}")
