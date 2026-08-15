"""Script para preencher campos qualidade, tem_legendado e hash_base em dados existentes."""

import sys
import shutil
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from app.app import create_app
from app.services.parser import extract_quality_features, map_quality_level_to_string, calculate_hash_with_year, calculate_hash_base

def migrate_existing_data():
    """Migração otimizada com backup e rollback."""
    app = create_app()
    
    with app.app_context():
        from app.database import get_db
        db = get_db()
        
        # 1. Backup obrigatório
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = Path('database') / f'iptv_backup_{timestamp}.db'
        db_file = Path('database') / 'iptv.db'
        
        print(f"Criando backup: {backup_file}")
        shutil.copy(db_file, backup_file)
        print(f"Backup criado com sucesso")
        
        # 2. Adicionar hash_base (se não existir)
        try:
            db.execute('ALTER TABLE midias ADD COLUMN hash_base TEXT')
            db.commit()
            print("Campo hash_base adicionado")
        except Exception as e:
            if "duplicate column" not in str(e).lower():
                raise
            print("Campo hash_base já existe")
        
        # 3. Adicionar tem_legendado (se não existir)
        try:
            db.execute('ALTER TABLE midias ADD COLUMN tem_legendado BOOLEAN DEFAULT 0')
            db.commit()
            print("Campo tem_legendado adicionado")
        except Exception as e:
            if "duplicate column" not in str(e).lower():
                raise
            print("Campo tem_legendado já existe")
        
        # 4. Buscar total
        total = db.execute('SELECT COUNT(*) FROM midias').fetchone()[0]
        print(f"Total de registros: {total}")
        
        if total == 0:
            print("Nenhum registro para migrar")
            return
        
        # 5. Processar em lotes de 10.000
        offset = 0
        batch_size = 10000
        total_atualizados = 0
        
        try:
            while True:
                midias = db.execute('''
                    SELECT id, nome_da_midia, nome_normalizado, categoria, ano, hash_midia
                    FROM midias 
                    LIMIT ? OFFSET ?
                ''', (batch_size, offset)).fetchall()
                
                if not midias:
                    break
                
                batch_data = []
                for midia in midias:
                    features = extract_quality_features(midia['nome_da_midia'])
                    qualidade = map_quality_level_to_string(features['quality_level'])
                    tem_legendado = features['is_legendado']
                    
                    # Recalcular hashes
                    hash_midia_novo = calculate_hash_with_year(
                        midia['categoria'], midia['nome_normalizado'], midia['ano']
                    )
                    hash_base = calculate_hash_base(
                        midia['categoria'], midia['nome_normalizado']
                    )
                    
                    batch_data.append((
                        qualidade, tem_legendado, hash_midia_novo, hash_base, midia['id']
                    ))
                
                # Executar batch
                db.executemany('''
                    UPDATE midias 
                    SET qualidade = ?, tem_legendado = ?, hash_midia = ?, hash_base = ?
                    WHERE id = ?
                ''', batch_data)
                db.commit()
                
                total_atualizados += len(batch_data)
                offset += batch_size
                
                progresso = (total_atualizados / total) * 100
                print(f"Progresso: {total_atualizados}/{total} ({progresso:.1f}%)")
        
        except Exception as e:
            print(f"ERRO: {e}")
            print("Restaurando backup...")
            shutil.copy(backup_file, db_file)
            print("Backup restaurado")
            raise
        
        print(f"Migração concluída com sucesso: {total_atualizados} registros atualizados")
        print(f"Backup mantido em: {backup_file}")

if __name__ == '__main__':
    migrate_existing_data()
