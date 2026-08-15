from app.app import create_app
from pathlib import Path
from app.services.exporter import generate_file_path

# Create app context
app = create_app()
with app.app_context():
    from app.database import get_db
    from app.services.config import get_galeria_path
    
    db = get_db()
    galeria_path = Path(get_galeria_path())
    
    print("LIMPANDO ARQUIVOS .STRM DE ITENS NA BLACKLIST")
    print("=" * 60)
    
    # Get all blacklist items from database
    blacklist_items = db.execute('''
        SELECT id, hash_midia, nome_da_midia, categoria, url, ano, season, episode
        FROM midias 
        WHERE status = 1 AND black_list = 1
    ''').fetchall()
    
    print(f"Total de itens na blacklist no banco: {len(blacklist_items)}")
    
    deleted_count = 0
    error_count = 0
    
    for item in blacklist_items:
        try:
            # Generate the expected file path for this item
            media_dict = {
                'hash_midia': item['hash_midia'],
                'nome_da_midia': item['nome_da_midia'],
                'categoria': item['categoria'],
                'url': item['url'],
                'ano': item['ano'],
                'season': item['season'],
                'episode': item['episode']
            }
            
            arquivo_path = Path(generate_file_path(media_dict))
            
            if arquivo_path.exists():
                arquivo_path.unlink()
                deleted_count += 1
                
                # Try to remove empty parent directories
                try:
                    arquivo_path.parent.rmdir()
                except:
                    pass
                
                if deleted_count % 100 == 0:
                    print(f"Progresso: {deleted_count} arquivos deletados...")
        except Exception as e:
            error_count += 1
            if error_count <= 10:  # Show first 10 errors
                print(f"Erro ao deletar {item['nome_da_midia'][:50]}: {e}")
    
    print(f"\nTotal de arquivos .strm deletados: {deleted_count}")
    print(f"Total de erros: {error_count}")
    
    # Also clean exported_media table for blacklist items
    db.execute('''
        DELETE FROM exported_media
        WHERE hash_midia IN (
            SELECT hash_midia FROM midias WHERE black_list = 1 AND status = 1
        )
    ''')
    db.commit()
    
    print("Tabela exported_media limpa (itens blacklist removidos)")
    print("Galeria agora está fiel ao banco de dados!")
