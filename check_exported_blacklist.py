from app.app import create_app

# Create app context
app = create_app()
with app.app_context():
    from app.database import get_db
    from pathlib import Path
    from app.services.config import get_galeria_path
    
    db = get_db()
    
    print("VERIFICANDO ITENS EXPORTADOS COM BLACKLIST=1")
    print("=" * 60)
    
    # Check if there are exported items that are now blacklisted
    blacklist_exported = db.execute('''
        SELECT e.hash_midia, e.arquivo, m.nome_da_midia, m.categoria, m.black_list
        FROM exported_media e
        JOIN midias m ON e.hash_midia = m.hash_midia
        WHERE m.black_list = 1 AND m.status = 1
    ''').fetchall()
    
    print(f"Total de itens na galeria que estão na blacklist: {len(blacklist_exported)}")
    
    if blacklist_exported:
        print("\nITENS ENCONTRADOS:")
        galeria_path = Path(get_galeria_path())
        files_to_delete = []
        
        for item in blacklist_exported:  # Process ALL items
            arquivo_path = Path(item['arquivo'])
            exists = arquivo_path.exists()
            if exists:
                files_to_delete.append(arquivo_path)
        
        print(f"  Total de arquivos encontrados: {len(files_to_delete)}")
        
        print(f"\nTotal de arquivos para deletar: {len(files_to_delete)}")
        print("\nIniciando limpeza automaticamente...")
        
        # Delete files
        deleted_count = 0
        for file_path in files_to_delete:
            try:
                if file_path.exists():
                    file_path.unlink()
                    # Try to remove empty parent directories
                    try:
                        file_path.parent.rmdir()
                    except:
                        pass
                    deleted_count += 1
            except Exception as e:
                print(f"Erro ao deletar {file_path}: {e}")
        
        print(f"Arquivos deletados: {deleted_count}")
        
        # Remove from exported_media table
        db.execute('''
            DELETE FROM exported_media
            WHERE hash_midia IN (
                SELECT hash_midia FROM midias WHERE black_list = 1 AND status = 1
            )
        ''')
        db.commit()
        
        print("Tabela exported_media limpa (itens blacklist removidos)")
        print("Galeria agora está fiel ao banco de dados!")
    else:
        print("✅ Nenhum item blacklist encontrado na tabela exported_media")
        print("A galeria já está fiel ao banco de dados")
