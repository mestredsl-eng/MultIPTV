"""Script simples para testar a funcionalidade de auto-blacklist."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.app import create_app

def test_auto_blacklist():
    """Testa a funcionalidade de auto-blacklist com exemplos específicos."""
    app = create_app()
    
    with app.app_context():
        from app.database import get_db
        from app.services.duplicate_manager import DuplicateManager
        
        db = get_db()
        duplicate_manager = DuplicateManager(db)
        
        print("=== TESTE DE AUTO-BLACKLIST ===\n")
        
        # Teste 1: Verificar se "meus filmes picles" está na blacklist
        print("Teste 1: Procurando por 'meus filmes picles' na blacklist...")
        picles_items = db.execute('''
            SELECT id, nome_da_midia, black_list FROM midias 
            WHERE nome_normalizado LIKE '%picles%' AND status = 1
            LIMIT 5
        ''').fetchall()
        
        if picles_items:
            print(f"Encontrados {len(picles_items)} itens com 'picles':")
            for item in picles_items:
                print(f"  - ID: {item['id']}, Nome: {item['nome_da_midia']}, Blacklist: {item['black_list']}")
        else:
            print("  Nenhum item com 'picles' encontrado.")
        
        print()
        
        # Teste 2: Verificar quantos itens estão na blacklist atualmente
        print("Teste 2: Contagem de itens na blacklist...")
        blacklist_count = db.execute('SELECT COUNT(*) FROM midias WHERE black_list = 1 AND status = 1').fetchone()[0]
        total_count = db.execute('SELECT COUNT(*) FROM midias WHERE status = 1').fetchone()[0]
        print(f"  Total de itens: {total_count}")
        print(f"  Itens na blacklist: {blacklist_count}")
        print(f"  Itens ativos (não blacklist): {total_count - blacklist_count}")
        
        print()
        
        # Teste 3: Testar verificação de auto-blacklist para um novo item
        print("Teste 3: Simulando adição de novo item...")
        test_nome = "meus filmes picles 2024"
        test_normalizado = test_nome.lower()
        
        should_blacklist, reason = duplicate_manager.check_and_apply_auto_blacklist(
            test_normalizado, test_nome
        )
        
        if should_blacklist:
            print(f"  ✅ O item '{test_nome}' seria AUTO-BLACKLISTADO")
            print(f"  Motivo: {reason}")
        else:
            print(f"  ❌ O item '{test_nome}' NÃO seria blacklistado automaticamente")
        
        print()
        
        # Teste 4: Mostrar alguns exemplos de itens que poderiam ser auto-blacklistados
        print("Teste 4: Verificando itens que poderiam ser auto-blacklistados...")
        non_blacklisted = db.execute('''
            SELECT id, nome_da_midia, nome_normalizado FROM midias 
            WHERE black_list = 0 AND status = 1
            LIMIT 10
        ''').fetchall()
        
        print(f"  Verificando {len(non_blacklisted)} itens aleatórios não-blacklistados:")
        for item in non_blacklisted:
            should_blacklist, reason = duplicate_manager.check_and_apply_auto_blacklist(
                item['nome_normalizado'], item['nome_da_midia']
            )
            status = "⚠️  SERIA BLACKLISTADO" if should_blacklist else "✅ OK"
            print(f"    - {item['nome_da_midia']}: {status}")
            if should_blacklist:
                print(f"      Motivo: {reason}")
        
        print()
        print("=== TESTE CONCLUÍDO ===")

if __name__ == '__main__':
    test_auto_blacklist()