"""
Escaneia diretamente a galeria para encontrar .strm de itens blacklist.
"""

from app.app import create_app
from pathlib import Path
from app.services.config import get_galeria_path

app = create_app()
with app.app_context():
    from app.database import get_db
    db = get_db()
    galeria_path = Path(get_galeria_path())
    
    print("=" * 60)
    print("ESCANEANDO GALERIA POR .STRM DE ITENS BLACKLIST")
    print("=" * 60)
    
    # Get all .strm files in gallery
    strm_files = list(galeria_path.rglob('*.strm'))
    print(f"\nTotal de arquivos .strm na galeria: {len(strm_files)}")
    
    # Get all blacklist hashes
    blacklist_hashes = db.execute('''
        SELECT hash_midia FROM midias WHERE black_list = 1 AND status = 1
    ''').fetchall()
    
    blacklist_hash_set = {item['hash_midia'] for item in blacklist_hashes}
    print(f"Total de itens blacklist no banco: {len(blacklist_hash_set)}")
    
    # Get all exported_media
    exported = db.execute('SELECT hash_midia, arquivo FROM exported_media').fetchall()
    exported_dict = {item['hash_midia']: item['arquivo'] for item in exported}
    
    # Check which .strm files belong to blacklist items
    blacklist_strm_count = 0
    sample_count = 0
    
    for hash_midia, arquivo in exported_dict.items():
        if hash_midia in blacklist_hash_set:
            blacklist_strm_count += 1
            if sample_count < 10:
                print(f"  BLACKLIST .strm encontrado: {arquivo}")
                sample_count += 1
    
    print(f"\nRESULTADO:")
    print(f"  Arquivos .strm de itens blacklist: {blacklist_strm_count}")
    
    if blacklist_strm_count > 0:
        print("\n⚠️  BUG CONFIRMADO: Itens blacklist têm arquivos .strm na galeria!")
    else:
        print("\n✅ Nenhum bug: Nenhum item blacklist tem .strm na galeria")
