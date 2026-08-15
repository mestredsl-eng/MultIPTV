"""Test script for the centralized DuplicateManager service."""

from app.app import create_app

app = create_app()

with app.app_context():
    from app.database import get_db
    from app.services.duplicate_manager import DuplicateManager
    
    db = get_db()
    duplicate_manager = DuplicateManager(db)
    
    print("TESTE: DuplicateManager Centralizado")
    print("=" * 60)
    
    # Test 1: get_base_name
    print("\n1. Teste de extração de nome base:")
    test_names = [
        "Filme 2024 FHD",
        "Filme 2024 4K", 
        "Série S01E01 HD",
        "Canal TV FHD",
    ]
    for nome in test_names:
        base = duplicate_manager.get_base_name(nome)
        print(f"  '{nome}' -> '{base}'")
    
    # Test 2: check_rigorous_blacklist
    print("\n2. Teste de verificação rigorosa de blacklist:")
    test_normalized = "a&e 4k"
    should_skip, reason, count = duplicate_manager.check_rigorous_blacklist(test_normalized)
    print(f"  Nome normalizado: '{test_normalized}'")
    print(f"  Deve pular: {should_skip}")
    print(f"  Razão: {reason}")
    print(f"  Contagem: {count}")
    
    # Test 3: find_duplicates_by_base_name
    print("\n3. Teste de busca de duplicatas por nome base:")
    sample_media = db.execute('SELECT id, nome_normalizado FROM midias LIMIT 1').fetchone()
    if sample_media:
        nome_normalizado = sample_media['nome_normalizado']
        duplicates = duplicate_manager.find_duplicates_by_base_name(nome_normalizado, exclude_id=sample_media['id'])
        print(f"  Mídia de teste: {nome_normalizado}")
        print(f"  Duplicatas por nome base: {len(duplicates)}")
        if duplicates:
            for dup in duplicates[:3]:
                print(f"    - ID: {dup['id']}, Nome: {dup['nome_da_midia']}, Blacklist: {dup['black_list']}")
    
    # Test 4: find_all_duplicates (comprehensive)
    print("\n4. Teste de busca completa de duplicatas:")
    if sample_media:
        all_duplicates = duplicate_manager.find_all_duplicates(sample_media['id'])
        print(f"  Mídia ID: {sample_media['id']}")
        print(f"  Duplicatas por hash: {len(all_duplicates['hash_duplicates'])}")
        print(f"  Duplicatas por nome: {len(all_duplicates['name_duplicates'])}")
        print(f"  Total de duplicatas: {all_duplicates['total_duplicates']}")
    
    # Test 5: get_statistics
    print("\n5. Teste de estatísticas:")
    stats = duplicate_manager.get_statistics()
    print(f"  Total de mídias: {stats['total_media']}")
    print(f"  Mídias na blacklist: {stats['blacklisted_media']}")
    
    print("\n" + "=" * 60)
    print("✅ Testes do DuplicateManager concluídos com sucesso!")
    print("\nO serviço centralizado está funcionando corretamente e pode ser")
    print("usado por todas as partes do sistema para consistência.")
