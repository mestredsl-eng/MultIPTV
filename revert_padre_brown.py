from app.app import create_app

# Create app context
app = create_app()
with app.app_context():
    from app.database import get_db
    db = get_db()
    
    print("REVERTENDO MARCAÇÕES INCORRETAS DE PADRE BROWN:")
    print("=" * 60)
    
    # Revert Padre Brown markings
    result = db.execute('''
        UPDATE midias
        SET black_list = 0
        WHERE status = 1
        AND black_list = 1
        AND nome_da_midia LIKE '%Padre Brown%'
    ''')
    db.commit()
    
    print(f"Revertidos itens Padre Brown: {result.rowcount}")
