"""Demonstração da funcionalidade de auto-blacklist."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.app import create_app

def demo_auto_blacklist():
    """Demonstra como funciona a auto-blacklist na prática."""
    app = create_app()
    
    with app.app_context():
        from app.database import get_db
        from app.services.duplicate_manager import DuplicateManager
        
        db = get_db()
        duplicate_manager = DuplicateManager(db)
        
        print("=== DEMONSTRAÇÃO DE AUTO-BLACKLIST ===\n")
        
        # Escolhemos um exemplo comum - canais de TV que costumam ter duplicatas
        test_nome = "Globo HD"
        
        print(f"Passo 1: Procurando por itens similares a '{test_nome}'...")
        
        # Primeiro, verificar o estado atual
        similares = db.execute('''
            SELECT id, nome_da_midia, black_list FROM midias 
            WHERE nome_normalizado LIKE '%globo%' AND status = 1
            LIMIT 10
        ''').fetchall()
        
        print(f"Encontrados {len(similares)} itens similares:")
        for item in similares:
            status = "🚫 BLACKLIST" if item['black_list'] == 1 else "✅ ATIVO"
            print(f"  - ID: {item['id']}, Nome: {item['nome_da_midia']}, Status: {status}")
        
        print()
        
        # Agora vamos simular colocando um item na blacklist
        print(f"Passo 2: Simulando blacklist de '{test_nome}'...")
        
        # Encontrar um item específico para testar
        item_teste = db.execute('''
            SELECT id, nome_da_midia, black_list FROM midias 
            WHERE nome_normalizado LIKE '%globo%' AND black_list = 0 AND status = 1
            LIMIT 1
        ''').fetchone()
        
        if item_teste:
            print(f"Item escolhido para teste: ID {item_teste['id']} - {item_teste['nome_da_midia']}")
            
            # Colocar na blacklist
            db.execute('UPDATE midias SET black_list = 1 WHERE id = ?', (item_teste['id'],))
            db.commit()
            print(f"✅ Item {item_teste['id']} colocado na blacklist manualmente")
            
            print()
            print("Passo 3: Executando auto-propagação de blacklist...")
            
            # Executar auto-propagação
            newly_blacklisted = duplicate_manager.auto_propagate_blacklist(item_teste['id'])
            
            print(f"✅ Auto-propagação concluída! {newly_blacklisted} novos itens blacklistados automaticamente")
            
            print()
            print("Passo 4: Verificando resultado...")
            
            # Verificar quais itens foram blacklistados
            result_after = db.execute('''
                SELECT id, nome_da_midia, black_list FROM midias 
                WHERE nome_normalizado LIKE '%globo%' AND status = 1
                LIMIT 10
            ''').fetchall()
            
            print(f"Estado após auto-propagação:")
            for item in result_after:
                status = "🚫 BLACKLIST" if item['black_list'] == 1 else "✅ ATIVO"
                print(f"  - ID: {item['id']}, Nome: {item['nome_da_midia']}, Status: {status}")
            
            # Reverter o teste (desfazer blacklist)
            print()
            print("Passo 5: Revertendo teste (limpando blacklist)...")
            
            # Desfazer blacklist dos itens que modificamos
            all_globo = db.execute('''
                SELECT id FROM midias 
                WHERE nome_normalizado LIKE '%globo%' AND status = 1
            ''').fetchall()
            
            for item in all_globo:
                db.execute('UPDATE midias SET black_list = 0 WHERE id = ?', (item['id'],))
            
            db.commit()
            print(f"✅ Teste revertido! {len(all_globo)} itens restaurados")
            
        else:
            print("Nenhum item encontrado para teste")
        
        print()
        print("=== COMO FUNCIONA O SISTEMA ===")
        print()
        print("1. Quando um item é colocado na blacklist (black_list = 1):")
        print("   - O sistema busca automaticamente por itens com nomes similares")
        print("   - Itens similares são automaticamente colocados na blacklist também")
        print()
        print("2. Durante a inserção de novos itens:")
        print("   - O sistema verifica se o nome é similar a itens já banidos")
        print("   - Se similar, o novo item é inserido diretamente na blacklist")
        print()
        print("3. Isso evita duplicação de conteúdo banido no sistema")
        print("   - Exemplo: 'meus filmes picles' banido -> qualquer variação auto-banida")
        print()
        print("=== DEMONSTRAÇÃO CONCLUÍDA ===")

if __name__ == '__main__':
    demo_auto_blacklist()