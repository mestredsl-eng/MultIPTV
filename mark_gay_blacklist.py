from app.app import create_app

# Create app context
app = create_app()
with app.app_context():
    from app.database import get_db
    db = get_db()
    
    print("MARCANDO FILMES GAY COMO BLACKLIST:")
    print("=" * 60)
    
    # Check for gay movies
    gay_movies = db.execute('''
        SELECT COUNT(*) as count
        FROM midias
        WHERE status = 1
        AND categoria = 'Movie'
        AND (nome_da_midia LIKE '% gay %' OR nome_da_midia LIKE '%gay%' OR nome_da_midia LIKE '%homosexual%'
             OR nome_da_midia LIKE '%lgbt%' OR nome_da_midia LIKE '%queer%')
    ''').fetchone()
    
    print(f"Total de filmes com termos gay/lgbt: {gay_movies['count']}")
    
    # Mark as blacklist
    result = db.execute('''
        UPDATE midias
        SET black_list = 1
        WHERE status = 1
        AND categoria = 'Movie'
        AND (nome_da_midia LIKE '% gay %' OR nome_da_midia LIKE '%gay%' OR nome_da_midia LIKE '%homosexual%'
             OR nome_da_midia LIKE '%lgbt%' OR nome_da_midia LIKE '%queer%')
    ''')
    db.commit()
    
    print(f"Marcados como blacklist: {result.rowcount}")
    
    # Show some examples
    examples = db.execute('''
        SELECT nome_da_midia
        FROM midias
        WHERE status = 1
        AND black_list = 1
        AND categoria = 'Movie'
        AND (nome_da_midia LIKE '% gay %' OR nome_da_midia LIKE '%gay%' OR nome_da_midia LIKE '%homosexual%'
             OR nome_da_midia LIKE '%lgbt%' OR nome_da_midia LIKE '%queer%')
        LIMIT 10
    ''').fetchall()
    
    print("\nEXEMPLOS DE FILMES MARCADOS:")
    for ex in examples:
        print(f"  {ex['nome_da_midia']}")
