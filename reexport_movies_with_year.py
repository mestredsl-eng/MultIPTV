"""Script para reexportar filmes com ano no nome do arquivo."""

import sqlite3
from pathlib import Path
from app.services.exporter import generate_file_path, export_media
from app.database import get_db

DATABASE_PATH = Path(__file__).parent / 'database' / 'iptv.db'

print("REEXPORTANDO FILMES COM ANO NO NOME:")
print("=" * 60)

try:
    db = sqlite3.connect(DATABASE_PATH, timeout=120.0)
    db.row_factory = sqlite3.Row

    # Buscar todos os filmes ativos
    print("\nBuscando filmes no banco de dados...")
    movies = db.execute('''
        SELECT * FROM midias
        WHERE categoria = 'Movie' AND status = 1 AND black_list = 0
    ''').fetchall()

    print(f"Encontrados {len(movies)} filmes para reexportar")

    # Confirmar
    response = input(f"Deseja reexportar {len(movies)} filmes? (s/n): ")
    if response.lower() != 's':
        print("Operação cancelada.")
        db.close()
        exit(0)

    updated_count = 0
    error_count = 0

    for i, movie in enumerate(movies, 1):
        try:
            # Gerar novo caminho com ano
            media_item = dict(movie)
            new_path = generate_file_path(media_item)

            # Verificar se o caminho novo é diferente do atual
            old_export = db.execute('''
                SELECT arquivo FROM exported_media WHERE hash_midia = ?
            ''', (movie['hash_midia'],)).fetchone()

            if old_export and old_export['arquivo'] != new_path:
                # Reexportar com novo nome
                export_media(media_item, db)
                updated_count += 1

                if i % 10 == 0:
                    print(f"Progresso: {i}/{len(movies)} filmes processados, {updated_count} atualizados")
            else:
                if i % 10 == 0:
                    print(f"Progresso: {i}/{len(movies)} filmes processados (já atualizados)")

        except Exception as e:
            error_count += 1
            print(f"Erro ao processar filme {movie['nome_da_midia']}: {e}")

    print("\n" + "=" * 60)
    print("Reexportação concluída!")
    print(f"Total processados: {len(movies)}")
    print(f"Atualizados: {updated_count}")
    print(f"Erros: {error_count}")

    db.close()

except Exception as e:
    print(f"\n❌ Erro: {e}")
    import traceback
    traceback.print_exc()
