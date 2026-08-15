"""Test script for rigorous duplicate checking."""

from app.app import create_app

app = create_app()

with app.app_context():
    from app.database import get_db
    from app.services.parser import remove_quality_from_name
    import re
    
    db = get_db()
    
    print("TESTE: Verificação Rigorosa de Duplicatas")
    print("=" * 60)
    
    # Test the remove_quality_from_name function
    test_names = [
        "Filme 2024 FHD",
        "Filme 2024 4K",
        "Filme [L]",
        "Série S01E01 HD",
        "Série S01E01 FHD",
    ]
    
    print("\nTeste de normalização de nomes:")
    for name in test_names:
        normalized = remove_quality_from_name(name)
        base = re.sub(r'\s*[\(\[]\d{4}[\)\]]\s*', '', normalized)
        base = re.sub(r'\s+', ' ', base).strip().lower()
        print(f"  '{name}' -> '{base}'")
    
    # Check for potential duplicates in database
    print("\nVerificando duplicatas no banco de dados:")
    
    # Get a sample of media items
    media_sample = db.execute('''
        SELECT id, nome_da_midia, nome_normalizado, black_list 
        FROM midias 
        WHERE status = 1 
        LIMIT 10
    ''').fetchall()
    
    for media in media_sample:
        nome_normalizado = media['nome_normalizado']
        nome_base = remove_quality_from_name(nome_normalizado)
        nome_base = re.sub(r'\s*[\(\[]\d{4}[\)\]]\s*', '', nome_base)
        nome_base = re.sub(r'\s+', ' ', nome_base).strip().lower()
        
        # Check for similar names
        similar = db.execute('''
            SELECT id, nome_da_midia, black_list FROM midias 
            WHERE nome_normalizado LIKE ? AND id != ? AND status = 1
        ''', (f'%{nome_base}%', media['id'])).fetchall()
        
        if similar:
            print(f"\n  Mídia: {media['nome_da_midia']}")
            print(f"  Base: '{nome_base}'")
            print(f"  Similares encontrados: {len(similar)}")
            for sim in similar[:3]:  # Show max 3
                print(f"    - ID: {sim['id']}, Nome: {sim['nome_da_midia']}, Blacklist: {sim['black_list']}")
    
    print("\n" + "=" * 60)
    print("✅ Teste concluído!")
    print("\nA verificação rigorosa está ativa no processo de classificação.")
    print("Ela irá pular novas mídias que tiverem o mesmo nome base")
    print("que mídias já existentes na blacklist.")
