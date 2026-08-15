from app.app import create_app

# Create app context
app = create_app()
with app.app_context():
    from app.database import get_db
    from app.services.tmdb import get_movie_info
    import time

    db = get_db()

    print("ENRIQUECENDO TMDB PARA TODOS OS MOVIES (FILMES):")
    print("=" * 60)

    # Get all Movies without tmdb_id
    movies = db.execute('''
        SELECT id, nome_da_midia
        FROM midias
        WHERE status = 1 AND black_list = 0 AND categoria = 'Movie' AND tmdb_id IS NULL
    ''').fetchall()

    print(f"Total de Movies para enriquecer: {len(movies)}")

    enriched_count = 0
    for i, item in enumerate(movies):
        try:
            tmdb_info = get_movie_info(item['nome_da_midia'])
            if tmdb_info and tmdb_info.get('tmdb_id'):
                db.execute('''
                    UPDATE midias SET tmdb_id = ?, imagem_url = ?, ultima_atualizacao = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (tmdb_info['tmdb_id'], tmdb_info.get('poster'), item['id']))
                enriched_count += 1

            if i % 10 == 0:
                db.commit()
                print(f"Progresso Movies: {i+1}/{len(movies)} ({enriched_count} enriquecidos)")
                time.sleep(0.5)  # Rate limiting

        except Exception as e:
            print(f"Erro ao enriquecer Movie {item['nome_da_midia']}: {e}")

    db.commit()
    print(f"Movies enriquecidos: {enriched_count}")

    print("\nTOTAL ENRIQUECIDO:")
    print(f"Movies: {enriched_count}")
