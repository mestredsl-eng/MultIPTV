"""
Analisar blacklist para identificar itens banidos manualmente vs automaticamente.
"""

from app.app import create_app

app = create_app()
with app.app_context():
    from app.database import get_db
    db = get_db()
    
    print("=" * 60)
    print("ANÁLISE DA BLACKLIST")
    print("=" * 60)
    
    # Estatísticas gerais
    total = db.execute('SELECT COUNT(*) FROM midias WHERE status = 1').fetchone()[0]
    blacklist = db.execute('SELECT COUNT(*) FROM midias WHERE status = 1 AND black_list = 1').fetchone()[0]
    active = db.execute('SELECT COUNT(*) FROM midias WHERE status = 1 AND black_list = 0').fetchone()[0]
    
    print(f"\nESTATÍSTICAS GERAIS:")
    print(f"  Total: {total}")
    print(f"  Blacklist: {blacklist} ({blacklist/total*100:.1f}%)")
    print(f"  Active: {active}")
    
    # Blacklist por categoria
    print(f"\nBLACKLIST POR CATEGORIA:")
    blacklist_by_category = db.execute('''
        SELECT categoria, COUNT(*) as count
        FROM midias
        WHERE status = 1 AND black_list = 1
        GROUP BY categoria
        ORDER BY count DESC
    ''').fetchall()
    
    for row in blacklist_by_category:
        print(f"  {row['categoria']}: {row['count']}")
    
    # Verificar itens com marcações manuais conhecidas
    print(f"\nITENS COM MARCAÇÕES MANUAIS CONHECIDAS:")
    
    # Adulto
    adult_count = db.execute('''
        SELECT COUNT(*) FROM midias
        WHERE status = 1 AND black_list = 1 AND categoria = 'Adult'
    ''').fetchone()[0]
    print(f"  Adult (filmes adultos): {adult_count}")
    
    # Religioso (se houver padrão)
    religious_count = db.execute('''
        SELECT COUNT(*) FROM midias
        WHERE status = 1 AND black_list = 1 AND 
        (nome_da_midia LIKE '%religioso%' OR nome_da_midia LIKE '%igreja%' OR nome_da_midia LIKE '%deus%')
    ''').fetchone()[0]
    print(f"  Palavras religiosas no nome: {religious_count}")
    
    # Gay (se houver padrão)
    gay_count = db.execute('''
        SELECT COUNT(*) FROM midias
        WHERE status = 1 AND black_list = 1 AND 
        (nome_da_midia LIKE '%gay%' OR nome_da_midia LIKE '%lgbt%')
    ''').fetchone()[0]
    print(f"  Palavras gay/lgbt no nome: {gay_count}")
    
    # 24h (canais 24h)
    tv_24h_count = db.execute('''
        SELECT COUNT(*) FROM midias
        WHERE status = 1 AND black_list = 1 AND categoria = 'TV' AND 
        (nome_da_midia LIKE '%24h%' OR nome_da_midia LIKE '%24 h%')
    ''').fetchone()[0]
    print(f"  TV 24h: {tv_24h_count}")
    
    print(f"\n" + "=" * 60)
    print("SUGESTÃO: Manter apenas itens de categorias específicas")
    print("=" * 60)
