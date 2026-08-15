from app.app import create_app

# Create app context
app = create_app()
with app.app_context():
    from app.database import get_db
    db = get_db()
    
    print("REVERTENDO MARCAÇÕES INCORRETAS DE BLACKLIST:")
    print("=" * 60)
    
    # Revert incorrect gay movie markings (those with "trans" in name but not actually gay)
    result1 = db.execute('''
        UPDATE midias
        SET black_list = 0
        WHERE status = 1
        AND black_list = 1
        AND categoria = 'Movie'
        AND (nome_da_midia LIKE '%transformers%' OR nome_da_midia LIKE '%transcendence%'
             OR nome_da_midia LIKE '%transa%' OR nome_da_midia LIKE '%trans %')
    ''')
    db.commit()
    
    print(f"Revertidos filmes incorretamente marcados: {result1.rowcount}")
    
    # Revert incorrect religious TV markings (those with "Santa" in name but not actually religious)
    result2 = db.execute('''
        UPDATE midias
        SET black_list = 0
        WHERE status = 1
        AND black_list = 1
        AND categoria = 'TV'
        AND (nome_da_midia LIKE '%Santa Maria%' OR nome_da_midia LIKE '%Santa Cruz%'
             OR nome_da_midia LIKE '%Santa Rosa%' OR nome_da_midia LIKE '%Santos%'
             OR nome_da_midia LIKE '%Live is Life%')
    ''')
    db.commit()
    
    print(f"Revertidos canais TV incorretamente marcados: {result2.rowcount}")
    
    print()
    print("Marcações incorretas revertidas!")
