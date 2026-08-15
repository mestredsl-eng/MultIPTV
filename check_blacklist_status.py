from app.app import create_app

# Create app context
app = create_app()
with app.app_context():
    from app.database import get_db
    db = get_db()
    
    print("STATUS ATUAL DA BLACKLIST:")
    print("=" * 60)
    
    # Check total blacklist count
    blacklist_count = db.execute('SELECT COUNT(*) as count FROM midias WHERE black_list = 1 AND status = 1').fetchone()
    print(f"Total de itens na blacklist: {blacklist_count['count']}")
    
    # Check by category
    blacklist_by_category = db.execute('''
        SELECT categoria, COUNT(*) as count
        FROM midias
        WHERE black_list = 1 AND status = 1
        GROUP BY categoria
        ORDER BY count DESC
    ''').fetchall()
    
    print("\nBLACKLIST POR CATEGORIA:")
    for cat in blacklist_by_category:
        print(f"  {cat['categoria']}: {cat['count']}")
