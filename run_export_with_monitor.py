#!/usr/bin/env python
"""Script para executar exportação e monitorar progresso em tempo real."""

import time
import re
from pathlib import Path
from app.app import create_app
from app.database import get_db
from app.services.exporter import export_all_media

def monitor_log(log_path):
    """Monitor log file for errors and progress."""
    last_size = 0
    error_count = 0
    success_count = 0
    
    while True:
        if log_path.exists():
            current_size = log_path.stat().st_size
            
            if current_size > last_size:
                # Read new lines
                with open(log_path, 'r', encoding='utf-8') as f:
                    f.seek(last_size)
                    new_lines = f.readlines()
                
                for line in new_lines:
                    if 'ERROR' in line:
                        error_count += 1
                        print(f"❌ ERRO {error_count}: {line.strip()}")
                    elif 'Exportação concluída' in line:
                        print(f"\n✅ {line.strip()}")
                        return True
                    elif 'TV M3U e EPG gerados' in line:
                        print(f"📺 {line.strip()}")
                
                last_size = current_size
        
        time.sleep(2)

def main():
    """Execute export and monitor."""
    app = create_app()
    
    with app.app_context():
        log_path = Path(__file__).parent / 'app' / 'logs' / 'process.log'
        
        print("🚀 Iniciando exportação de 277138 mídias...")
        print("📊 Monitorando log em tempo real...\n")
        
        db = get_db()
        
        # Get all media to export
        media_items = db.execute('''
            SELECT * FROM midias WHERE status = 1 AND black_list = 0
        ''').fetchall()
        
        if not media_items:
            print("❌ Nenhuma mídia para exportar")
            return
        
        print(f"📦 Total de mídias: {len(media_items)}")
        print("⏳ Iniciando exportação...\n")
        
        try:
            # Start export
            export_all_media([dict(item) for item in media_items], db)
            print("\n✅ Exportação concluída com sucesso!")
        except Exception as e:
            print(f"\n❌ Erro na exportação: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    main()
