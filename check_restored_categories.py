from app.app import create_app

# Create app context
app = create_app()
with app.app_context():
    from app.database import get_db
    db = get_db()
    
    print("VERIFICANDO CATEGORIAS APÓS RESTAURAÇÃO:")
    print("=" * 60)
    
    # Check current categories
    categories = db.execute('''
        SELECT categoria, COUNT(*) as count
        FROM midias
        WHERE status = 1
        GROUP BY categoria
        ORDER BY count DESC
    ''').fetchall()
    
    print("CATEGORIAS ATUAIS:")
    for cat in categories:
        print(f"  {cat['categoria']}: {cat['count']}")
    
    print()
    print(f"Total de mídias: {sum(cat['count'] for cat in categories)}")
