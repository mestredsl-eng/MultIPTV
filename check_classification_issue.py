from app.app import create_app

# Create app context
app = create_app()
with app.app_context():
    from app.database import get_db
    db = get_db()
    
    print("VERIFICANDO CLASSIFICAÇÃO:")
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
    
    # Check for items that might be novels but classified as Series
    potential_novelas = db.execute('''
        SELECT COUNT(*) as count
        FROM midias
        WHERE status = 1 
        AND categoria = 'Series'
        AND (nome_da_midia LIKE '%novela%' OR nome_da_midia LIKE '%telenovela%' OR nome_da_midia LIKE '%novelas%')
    ''').fetchone()
    print(f"Series com 'novela' no nome: {potential_novelas['count']}")
    
    # Check for items that might be cartoons but classified as Series
    potential_cartoons = db.execute('''
        SELECT COUNT(*) as count
        FROM midias
        WHERE status = 1 
        AND categoria = 'Series'
        AND (nome_da_midia LIKE '%cartoon%' OR nome_da_midia LIKE '%anime%' OR nome_da_midia LIKE '%desenho%' 
             OR nome_da_midia LIKE '%animation%' OR nome_da_midia LIKE '%disney%')
    ''').fetchone()
    print(f"Series com 'cartoon/anime/desenho' no nome: {potential_cartoons['count']}")
    
    # Check for items that might be adult but classified as Movie or Series
    potential_adult = db.execute('''
        SELECT COUNT(*) as count
        FROM midias
        WHERE status = 1 
        AND categoria IN ('Movie', 'Series')
        AND (nome_da_midia LIKE '%xxx%' OR nome_da_midia LIKE '%porn%' OR nome_da_midia LIKE '%adult%'
             OR nome_da_midia LIKE '%18+%' OR nome_da_midia LIKE '%erotic%')
    ''').fetchone()
    print(f"Movie/Series com termos adultos no nome: {potential_adult['count']}")
    
    print()
    
    # Show some examples
    print("EXEMPLOS DE POSSÍVEIS NOVELAS CLASSIFICADAS COMO SERIES:")
    examples = db.execute('''
        SELECT nome_da_midia, categoria
        FROM midias
        WHERE status = 1 
        AND categoria = 'Series'
        AND (nome_da_midia LIKE '%novela%' OR nome_da_midia LIKE '%telenovela%')
        LIMIT 10
    ''').fetchall()
    for ex in examples:
        print(f"  {ex['nome_da_midia'][:60]}... | {ex['categoria']}")
