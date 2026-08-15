from app.app import create_app

# Create app context
app = create_app()
with app.app_context():
    from app.database import get_db
    db = get_db()
    
    print("VERIFICANDO PADRE BROWN:")
    print("=" * 60)
    
    # Check Padre Brown items
    padre_brown = db.execute('''
        SELECT nome_da_midia, categoria, black_list
        FROM midias
        WHERE nome_da_midia LIKE '%Padre Brown%'
        LIMIT 10
    ''').fetchall()
    
    print("ITENS PADRE BROWN:")
    for item in padre_brown:
        print(f"  {item['nome_da_midia'][:60]}... | Categoria: {item['categoria']} | Blacklist: {item['black_list']}")
