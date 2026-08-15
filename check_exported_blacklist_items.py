"""
Verificar quais itens na blacklist têm arquivos .strm na galeria.
"""

from app.app import create_app
from pathlib import Path
from app.services.exporter import generate_file_path
from app.services.config import get_galeria_path

app = create_app()
with app.app_context():
    from app.database import get_db
    db = get_db()
    galeria_path = Path(get_galeria_path())
    
    print("=" * 60)
    print("VERIFICANDO ITENS BLACKLIST COM ARQUIVOS .STRM")
    print("=" * 60)
    
    # Get blacklist items
    blacklist_items = db.execute('''
        SELECT id, hash_midia, nome_da_midia, categoria, ultima_atualizacao
        FROM midias
        WHERE status = 1 AND black_list = 1
        LIMIT 100
    ''').fetchall()
    
    print(f"\nAmostra de 100 itens da blacklist:")
    
    with_strm = 0
    without_strm = 0
    
    for item in blacklist_items:
        media_dict = {
            'hash_midia': item['hash_midia'],
            'nome_da_midia': item['nome_da_midia'],
            'categoria': item['categoria'],
            'url': '',  # Não importa para o caminho
            'ano': None,
            'season': None,
            'episode': None
        }
        
        arquivo_path = Path(generate_file_path(media_dict))
        
        if arquivo_path.exists():
            with_strm += 1
            print(f"  ✅ TEM .strm: {item['nome_da_midia'][:50]}... ({item['categoria']})")
        else:
            without_strm += 1
            print(f"  ❌ SEM .strm: {item['nome_da_midia'][:50]}... ({item['categoria']})")
    
    print(f"\nRESUMO DA AMOSTRA:")
    print(f"  Com .strm: {with_strm}")
    print(f"  Sem .strm: {without_strm}")
    
    # Verificar tabela exported_media
    print(f"\nVERIFICANDO TABELA exported_media:")
    exported_blacklist = db.execute('''
        SELECT COUNT(*) FROM exported_media
        WHERE hash_midia IN (
            SELECT hash_midia FROM midias WHERE black_list = 1 AND status = 1
        )
    ''').fetchone()[0]
    
    print(f"  Itens blacklist na tabela exported_media: {exported_blacklist}")
    
    print(f"\n" + "=" * 60)
    print("CONCLUSÃO:")
    print("=" * 60)
    if with_strm > 0:
        print("⚠️  ITENS BLACKLIST ESTÃO SENDO EXPORTADOS!")
        print("O problema está na exportação, não na importação.")
    else:
        print("✅ Nenhum item blacklist tem .strm")
        print("A filtragem de blacklist na exportação está funcionando.")
