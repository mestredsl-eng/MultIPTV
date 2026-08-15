from app.app import create_app

# Create app context
app = create_app()
with app.app_context():
    from app.database import get_db
    db = get_db()
    
    print("CATEGORIAS NO BANCO DE DADOS:")
    print("=" * 60)
    
    # Get all categories
    categories = db.execute('''
        SELECT categoria, COUNT(*) as count
        FROM midias
        WHERE status = 1
        GROUP BY categoria
        ORDER BY count DESC
    ''').fetchall()
    
    for cat in categories:
        print(f"{cat['categoria']}: {cat['count']}")
    
    print()
    print("BLACKLIST:")
    print("=" * 60)
    blacklist_count = db.execute('SELECT COUNT(*) as count FROM midias WHERE black_list = 1').fetchone()
    print(f"Total black_list = 1: {blacklist_count['count']}")
    
    print()
    print("DUPLICADOS (hash_midia duplicado):")
    print("=" * 60)
    duplicate_count = db.execute('''
        SELECT COUNT(*) as count FROM (
            SELECT hash_midia, COUNT(*) as cnt 
            FROM midias 
            WHERE status = 1 
            GROUP BY hash_midia 
            HAVING cnt > 1
        )
    ''').fetchone()
    print(f"Total hash_midia duplicados: {duplicate_count['count']}")
