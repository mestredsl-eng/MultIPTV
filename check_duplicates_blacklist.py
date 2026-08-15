from app.app import create_app

# Create app context
app = create_app()
with app.app_context():
    from app.database import get_db
    db = get_db()
    
    print("VERIFICANDO DUPLICADOS E BLACKLIST:")
    print("=" * 60)
    
    # Check black_list
    blacklist_count = db.execute('SELECT COUNT(*) as count FROM midias WHERE black_list = 1').fetchone()
    print(f"Total de midias com black_list = 1: {blacklist_count['count']}")
    
    # Check black_list = 0
    blacklist_0_count = db.execute('SELECT COUNT(*) as count FROM midias WHERE black_list = 0').fetchone()
    print(f"Total de midias com black_list = 0: {blacklist_0_count['count']}")
    
    # Check NULL black_list
    blacklist_null_count = db.execute('SELECT COUNT(*) as count FROM midias WHERE black_list IS NULL').fetchone()
    print(f"Total de midias com black_list IS NULL: {blacklist_null_count['count']}")
    
    print()
    
    # Check duplicates by hash_midia
    duplicate_count = db.execute('''
        SELECT COUNT(*) as count FROM (
            SELECT hash_midia, COUNT(*) as cnt 
            FROM midias 
            WHERE status = 1 
            GROUP BY hash_midia 
            HAVING cnt > 1
        )
    ''').fetchone()
    print(f"Total de hash_midia duplicados: {duplicate_count['count']}")
    
    # Show some duplicate examples
    if duplicate_count['count'] > 0:
        duplicates = db.execute('''
            SELECT hash_midia, COUNT(*) as cnt, GROUP_CONCAT(nome_da_midia, ', ') as nomes
            FROM midias 
            WHERE status = 1 
            GROUP BY hash_midia 
            HAVING cnt > 1
            LIMIT 5
        ''').fetchall()
        print("\nExemplos de duplicados:")
        for dup in duplicates:
            print(f"  Hash: {dup['hash_midia'][:20]}... | Count: {dup['cnt']} | Nomes: {dup['nomes'][:100]}...")
    
    print()
    
    # Check total midias
    total_count = db.execute('SELECT COUNT(*) as count FROM midias WHERE status = 1').fetchone()
    print(f"Total de midias ativas: {total_count['count']}")
