"""
Verificar quando itens foram exportados vs quando foram marcados como blacklist.
"""

from app.app import create_app

app = create_app()
with app.app_context():
    from app.database import get_db
    db = get_db()
    
    print("=" * 60)
    print("VERIFICANDO EXPORTED_MEDIA VS BLACKLIST")
    print("=" * 60)
    
    # Verificar itens blacklist que estão em exported_media
    blacklist_exported = db.execute('''
        SELECT m.id, m.nome_da_midia, m.categoria, m.ultima_atualizacao, e.ultima_exportacao
        FROM midias m
        INNER JOIN exported_media e ON m.hash_midia = e.hash_midia
        WHERE m.black_list = 1 AND m.status = 1
        LIMIT 10
    ''').fetchall()
    
    print(f"\nITENS BLACKLIST QUE ESTÃO EM exported_media:")
    print(f"(Foram exportados ANTES de serem marcados como blacklist)")
    
    if blacklist_exported:
        for item in blacklist_exported:
            print(f"  {item['nome_da_midia'][:50]}...")
            print(f"    Categoria: {item['categoria']}")
            print(f"    Última atualização: {item['ultima_atualizacao']}")
            print(f"    Última exportação: {item['ultima_exportacao']}")
            print()
    else:
        print("  Nenhum item blacklist em exported_media")
    
    # Contar total
    total_blacklist_exported = db.execute('''
        SELECT COUNT(*) FROM exported_media
        WHERE hash_midia IN (
            SELECT hash_midia FROM midias WHERE black_list = 1 AND status = 1
        )
    ''').fetchone()[0]
    
    print(f"\nTOTAL DE ITENS BLACKLIST EM exported_media: {total_blacklist_exported}")
    
    if total_blacklist_exported > 0:
        print("\n⚠️  ESTES ARQUIVOS .STRM EXISTEM NA GALERIA")
        print("   Foram exportados antes dos itens serem marcados como blacklist")
        print("   Use check_gallery_orphans.py para removê-los")
