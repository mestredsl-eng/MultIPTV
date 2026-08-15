from app.app import create_app

# Create app context
app = create_app()
with app.app_context():
    from app.database import get_db
    db = get_db()
    
    print("MARCANDO TV RELIGIOSO COMO BLACKLIST:")
    print("=" * 60)
    
    # Check for religious TV channels
    religious_tv = db.execute('''
        SELECT COUNT(*) as count
        FROM midias
        WHERE status = 1
        AND categoria = 'TV'
        AND (nome_da_midia LIKE '%religioso%' OR nome_da_midia LIKE '%religiosa%'
             OR nome_da_midia LIKE '%igreja%' OR nome_da_midia LIKE '%igrejas%'
             OR nome_da_midia LIKE '%católica%' OR nome_da_midia LIKE '%catolica%'
             OR nome_da_midia LIKE '%cristão%' OR nome_da_midia LIKE '%cristao%'
             OR nome_da_midia LIKE '%cristã%' OR nome_da_midia LIKE '%crista%'
             OR nome_da_midia LIKE '%evangelico%' OR nome_da_midia LIKE '%evangélico%'
             OR nome_da_midia LIKE '%deus%' OR nome_da_midia LIKE '%jesus%'
             OR nome_da_midia LIKE '%bíblia%' OR nome_da_midia LIKE '%biblia%'
             OR nome_da_midia LIKE '%missa%' OR nome_da_midia LIKE '%oração%' OR nome_da_midia LIKE '%oracao%'
             OR nome_da_midia LIKE '%padre%' OR nome_da_midia LIKE '%pastor%'
             OR nome_da_midia LIKE '%bispo%' OR nome_da_midia LIKE '%papa%'
             OR nome_da_midia LIKE '%vaticano%')
    ''').fetchone()
    
    print(f"Total de canais TV com termos religiosos: {religious_tv['count']}")
    
    # Mark as blacklist
    result = db.execute('''
        UPDATE midias
        SET black_list = 1
        WHERE status = 1
        AND categoria = 'TV'
        AND (nome_da_midia LIKE '%religioso%' OR nome_da_midia LIKE '%religiosa%'
             OR nome_da_midia LIKE '%igreja%' OR nome_da_midia LIKE '%igrejas%'
             OR nome_da_midia LIKE '%católica%' OR nome_da_midia LIKE '%catolica%'
             OR nome_da_midia LIKE '%cristão%' OR nome_da_midia LIKE '%cristao%'
             OR nome_da_midia LIKE '%cristã%' OR nome_da_midia LIKE '%crista%'
             OR nome_da_midia LIKE '%evangelico%' OR nome_da_midia LIKE '%evangélico%'
             OR nome_da_midia LIKE '%deus%' OR nome_da_midia LIKE '%jesus%'
             OR nome_da_midia LIKE '%bíblia%' OR nome_da_midia LIKE '%biblia%'
             OR nome_da_midia LIKE '%missa%' OR nome_da_midia LIKE '%oração%' OR nome_da_midia LIKE '%oracao%'
             OR nome_da_midia LIKE '%padre%' OR nome_da_midia LIKE '%pastor%'
             OR nome_da_midia LIKE '%bispo%' OR nome_da_midia LIKE '%papa%'
             OR nome_da_midia LIKE '%vaticano%')
    ''')
    db.commit()
    
    print(f"Marcados como blacklist: {result.rowcount}")
    
    # Show some examples
    examples = db.execute('''
        SELECT nome_da_midia
        FROM midias
        WHERE status = 1
        AND black_list = 1
        AND categoria = 'TV'
        AND (nome_da_midia LIKE '%religioso%' OR nome_da_midia LIKE '%religiosa%'
             OR nome_da_midia LIKE '%igreja%' OR nome_da_midia LIKE '%igrejas%'
             OR nome_da_midia LIKE '%católica%' OR nome_da_midia LIKE '%catolica%'
             OR nome_da_midia LIKE '%cristão%' OR nome_da_midia LIKE '%cristao%'
             OR nome_da_midia LIKE '%cristã%' OR nome_da_midia LIKE '%crista%'
             OR nome_da_midia LIKE '%evangelico%' OR nome_da_midia LIKE '%evangélico%'
             OR nome_da_midia LIKE '%deus%' OR nome_da_midia LIKE '%jesus%'
             OR nome_da_midia LIKE '%bíblia%' OR nome_da_midia LIKE '%biblia%'
             OR nome_da_midia LIKE '%missa%' OR nome_da_midia LIKE '%oração%' OR nome_da_midia LIKE '%oracao%'
             OR nome_da_midia LIKE '%padre%' OR nome_da_midia LIKE '%pastor%'
             OR nome_da_midia LIKE '%bispo%' OR nome_da_midia LIKE '%papa%'
             OR nome_da_midia LIKE '%vaticano%')
        LIMIT 20
    ''').fetchall()
    
    print("\nEXEMPLOS DE CANAIS MARCADOS:")
    for ex in examples:
        print(f"  {ex['nome_da_midia']}")
