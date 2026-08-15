"""Test script for category learning system."""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.app import create_app
from app.database import get_db
from app.services.category_learner import CategoryLearner, get_learned_category, record_category_correction

def test_category_learning():
    """Test the category learning system."""
    print("=== Testando Sistema de Aprendizado de Categoria ===\n")
    
    # Create app context
    app = create_app()
    with app.app_context():
        db = get_db()
        learner = CategoryLearner()
        
        # Test 1: Create a test media item
        print("Test 1: Criando mídia de teste...")
        db.execute('''
            INSERT INTO midias (iptv_id, nome_da_midia, nome_normalizado, url, categoria, hash_midia, black_list, status, categoria_manual)
            VALUES (1, 'Breaking Bad S01E01', 'breaking bad s01e01', 'http://test.com/video.mp4', 'Series', 'test_hash_1', 0, 1, 0)
        ''')
        db.commit()
        media_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        print(f"✓ Mídia criada com ID: {media_id}\n")
        
        # Test 2: Record a manual correction
        print("Test 2: Registrando correção manual (Series -> TV)...")
        success = learner.record_correction(media_id, 'Series', 'TV')
        print(f"✓ Correção registrada: {success}\n")
        
        # Test 3: Check if learned category is retrieved
        print("Test 3: Verificando se categoria aprendida é recuperada...")
        learned_category = learner.get_learned_category('test_hash_1', 'breaking bad s01e01')
        print(f"✓ Categoria aprendida: {learned_category}")
        assert learned_category == 'TV', "Categoria aprendida deveria ser 'TV'"
        print("✓ Teste passou!\n")
        
        # Test 4: Test with normalized name match
        print("Test 4: Testando correspondência por nome normalizado...")
        learned_category = learner.get_learned_category('different_hash', 'breaking bad s01e01')
        print(f"✓ Categoria por nome: {learned_category}")
        assert learned_category == 'TV', "Categoria por nome deveria ser 'TV'"
        print("✓ Teste passou!\n")
        
        # Test 5: Get learning stats
        print("Test 5: Obtendo estatísticas de aprendizado...")
        stats = learner.get_learning_stats()
        print(f"✓ Total de correções: {stats['total_corrections']}")
        print(f"✓ Total de aplicações: {stats['total_applications']}")
        print("✓ Teste passou!\n")
        
        # Test 6: Get recent corrections
        print("Test 6: Obtendo correções recentes...")
        recent = learner.get_recent_corrections(5)
        print(f"✓ Correções recentes: {len(recent)}")
        if recent:
            print(f"  Última correção: {recent[0]['categoria_anterior']} -> {recent[0]['categoria_nova']}")
        print("✓ Teste passou!\n")
        
        # Test 7: Test convenience functions
        print("Test 7: Testando funções de conveniência...")
        learned_cat = get_learned_category('test_hash_1', 'breaking bad s01e01')
        print(f"✓ Função get_learned_category: {learned_cat}")
        
        record_success = record_category_correction(media_id, 'TV', 'Series')
        print(f"✓ Função record_category_correction: {record_success}")
        print("✓ Teste passou!\n")
        
        # Cleanup
        print("Test 8: Limpando dados de teste...")
        db.execute('DELETE FROM midias WHERE id = ?', (media_id,))
        db.execute('DELETE FROM category_corrections WHERE hash_midia = ?', ('test_hash_1',))
        db.commit()
        print("✓ Limpeza concluída\n")
        
        print("=== Todos os testes passaram! ===")
        return True

if __name__ == '__main__':
    try:
        test_category_learning()
    except Exception as e:
        print(f"✗ Teste falhou: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
