from app.app import create_app

# Create app context
app = create_app()
with app.app_context():
    from app.database import get_db
    db = get_db()
    
    print("VERIFICANDO DUPLICADOS EM TV:")
    print("=" * 60)
    
    # Check TV channels
    tv_count = db.execute('SELECT COUNT(*) as count FROM midias WHERE categoria = "TV" AND status = 1').fetchone()
    print(f"Total de canais TV: {tv_count['count']}")
    
    # Check duplicates by nome_da_midia
    duplicate_tv = db.execute('''
        SELECT nome_da_midia, COUNT(*) as cnt
        FROM midias
        WHERE categoria = "TV" AND status = 1
        GROUP BY nome_da_midia
        HAVING cnt > 1
        ORDER BY cnt DESC
        LIMIT 20
    ''').fetchall()
    
    print(f"\nTotal de canais TV duplicados por nome: {len(duplicate_tv)}")
    
    if duplicate_tv:
        print("\nEXEMPLOS DE DUPLICADOS:")
        for dup in duplicate_tv:
            print(f"  {dup['nome_da_midia'][:60]}... | Count: {dup['cnt']}")
    
    # Check duplicates by url (if available)
    duplicate_url = db.execute('''
        SELECT url, COUNT(*) as cnt
        FROM midias
        WHERE categoria = "TV" AND status = 1 AND url IS NOT NULL
        GROUP BY url
        HAVING cnt > 1
        ORDER BY cnt DESC
        LIMIT 20
    ''').fetchall()
    
    print(f"\nTotal de canais TV duplicados por URL: {len(duplicate_url)}")
    
    if duplicate_url:
        print("\nEXEMPLOS DE DUPLICADOS POR URL:")
        for dup in duplicate_url:
            print(f"  {dup['url'][:60]}... | Count: {dup['cnt']}")
