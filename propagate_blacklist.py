"""Script para propagar blacklist automaticamente para itens com nomes similares."""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def propagate_blacklist():
    """
    Propaga blacklist para todos os itens com nomes similares.
    Para cada item já na blacklist, encontra itens com nomes similares e também os coloca na blacklist.
    """
    from app.app import create_app
    app = create_app()
    
    with app.app_context():
        from app.database import get_db
        from app.services.duplicate_manager import DuplicateManager
        
        db = get_db()
        duplicate_manager = DuplicateManager(db)
        
        # Buscar todos os itens que estão na blacklist
        blacklisted_items = db.execute('''
            SELECT id, nome_da_midia, nome_normalizado FROM midias 
            WHERE black_list = 1 AND status = 1
        ''').fetchall()
        
        total_blacklisted = len(blacklisted_items)
        logger.info(f"Encontrados {total_blacklisted} itens na blacklist para processamento")
        
        total_newly_blacklisted = 0
        processed_count = 0
        
        for item in blacklisted_items:
            processed_count += 1
            media_id = item['id']
            nome_da_midia = item['nome_da_midia']
            
            # Usar o método de auto-propagação do DuplicateManager
            newly_blacklisted = duplicate_manager.auto_propagate_blacklist(media_id)
            total_newly_blacklisted += newly_blacklisted
            
            if processed_count % 100 == 0:
                logger.info(f"Progresso: {processed_count}/{total_blacklisted} itens processados, {total_newly_blacklisted} novos itens blacklistados")
        
        logger.info(f"Processamento concluído: {total_newly_blacklisted} novos itens foram colocados na blacklist automaticamente")
        logger.info(f"Total de itens na blacklist antes: {total_blacklisted}")
        
        # Contar total após a propagação
        total_after = db.execute('SELECT COUNT(*) FROM midias WHERE black_list = 1 AND status = 1').fetchone()[0]
        logger.info(f"Total de itens na blacklist após: {total_after}")
        
        return total_newly_blacklisted


if __name__ == '__main__':
    try:
        logger.info("Iniciando propagação automática de blacklist...")
        newly_blacklisted = propagate_blacklist()
        logger.info(f"Script concluído com sucesso! {newly_blacklisted} novos itens foram blacklistados.")
    except Exception as e:
        logger.error(f"Erro durante a execução do script: {str(e)}")
        sys.exit(1)