"""API routes."""

from flask import Blueprint, jsonify, request
import logging
import hashlib
import requests

bp = Blueprint('api', __name__, url_prefix='/api')

logger = logging.getLogger('process')


@bp.route('/iptv/stats', methods=['GET'])
def get_stats():
    """Get IPTV statistics."""
    from app.database.queries import get_dashboard_stats
    stats = get_dashboard_stats()
    return jsonify(stats)


@bp.route('/iptv/check-duplicate', methods=['POST'])
def check_duplicate():
    """Check if IPTV source name already exists."""
    from app.database import get_db
    data = request.get_json()
    nome = data.get('nome', '')
    
    db = get_db()
    existing = db.execute('SELECT id FROM iptvs WHERE nome = ?', (nome,)).fetchone()
    
    return jsonify({'exists': existing is not None})


@bp.route('/iptv/sources', methods=['POST'])
def create_iptv_source():
    """Create new IPTV source."""
    from app.database import get_db
    from app.database.queries import create_iptv
    data = request.get_json()
    
    nome = data.get('nome', '').strip()
    url_m3u = data.get('url_m3u', '').strip()
    url_epg = data.get('url_epg', '').strip()
    
    # Validate inputs
    if not nome:
        return jsonify({'success': False, 'error': 'Nome é obrigatório'})
    if len(nome) < 3:
        return jsonify({'success': False, 'error': 'Nome deve ter pelo menos 3 caracteres'})
    if not url_m3u:
        return jsonify({'success': False, 'error': 'URL M3U é obrigatória'})
    if not url_m3u.startswith(('http://', 'https://')):
        return jsonify({'success': False, 'error': 'URL M3U deve começar com http:// ou https://'})
    if not url_epg:
        return jsonify({'success': False, 'error': 'URL EPG é obrigatória'})
    if not url_epg.startswith(('http://', 'https://')):
        return jsonify({'success': False, 'error': 'URL EPG deve começar com http:// ou https://'})
    
    try:
        iptv_id = create_iptv(nome, url_m3u, url_epg)
        return jsonify({'success': True, 'id': iptv_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/iptv/sources', methods=['GET'])
def get_iptv_sources():
    """Get all IPTV sources."""
    from app.database.queries import get_all_iptvs
    sources = get_all_iptvs()
    return jsonify([dict(source) for source in sources])


@bp.route('/iptv/sources/<int:iptv_id>', methods=['DELETE'])
def delete_iptv_source(iptv_id):
    """Delete IPTV source (hard delete - removes from database and gallery)."""
    from app.database.queries import delete_iptv
    try:
        result = delete_iptv(iptv_id)
        return jsonify({
            'success': True,
            'affected_media': result.get('media_count', 0),
            'files_removed': result.get('files_removed', 0)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/iptv/sources/<int:iptv_id>/toggle-status', methods=['POST'])
def toggle_iptv_status(iptv_id):
    """Toggle IPTV source active status."""
    from app.database import get_db
    try:
        db = get_db()
        
        # Get current status
        result = db.execute('SELECT ativo FROM iptvs WHERE id = ?', (iptv_id,)).fetchone()
        if not result:
            return jsonify({'success': False, 'error': 'Fonte IPTV não encontrada'})
        
        current_status = result['ativo']
        new_status = 0 if current_status == 1 else 1
        
        # Toggle status
        db.execute('UPDATE iptvs SET ativo = ? WHERE id = ?', (new_status, iptv_id))
        db.commit()
        
        return jsonify({
            'success': True,
            'new_status': new_status
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/iptv/sources/<int:iptv_id>/test-connection', methods=['POST'])
def test_iptv_connection(iptv_id):
    """Test IPTV connection by checking if media streams are accessible."""
    from app.database import get_db
    from datetime import datetime
    
    try:
        db = get_db()
        
        # Get IPTV source info
        iptv = db.execute('SELECT * FROM iptvs WHERE id = ?', (iptv_id,)).fetchone()
        if not iptv:
            return jsonify({'success': False, 'error': 'Fonte IPTV não encontrada'})
        
        # Get a sample of active media from this IPTV
        media_samples = db.execute(
            'SELECT url FROM midias WHERE iptv_id = ? AND status = 1 AND black_list = 0 LIMIT 5',
            (iptv_id,)
        ).fetchall()
        
        if not media_samples:
            return jsonify({
                'success': False,
                'error': 'Nenhuma mídia ativa encontrada para teste',
                'status': 'no_media'
            })
        
        # Test each media URL
        tested_count = 0
        success_count = 0
        errors = []
        
        for media in media_samples:
            try:
                url = media['url']
                if not url:
                    continue
                
                # Try to get the stream with timeout
                response = requests.head(url, timeout=10, allow_redirects=True)
                
                tested_count += 1
                
                if response.status_code in [200, 206, 302, 301]:
                    success_count += 1
                else:
                    errors.append(f"Status {response.status_code} para {url[:50]}...")
                    
            except requests.exceptions.Timeout:
                errors.append(f"Timeout ao acessar {media['url'][:50]}...")
                tested_count += 1
            except requests.exceptions.RequestException as e:
                errors.append(f"Erro: {str(e)[:50]}...")
                tested_count += 1
        
        if tested_count == 0:
            return jsonify({
                'success': False,
                'error': 'Não foi possível testar nenhuma mídia',
                'status': 'no_test'
            })
        
        # Update last test timestamp
        db.execute(
            'UPDATE iptvs SET ultima_atualizacao = ? WHERE id = ?',
            (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), iptv_id)
        )
        db.commit()
        
        # Determine overall status
        success_rate = (success_count / tested_count) * 100 if tested_count > 0 else 0
        
        return jsonify({
            'success': True,
            'status': 'online' if success_rate > 50 else 'offline',
            'tested_count': tested_count,
            'success_count': success_count,
            'success_rate': success_rate,
            'errors': errors[:3],  # Return first 3 errors
            'message': f'{success_count}/{tested_count} mídias acessíveis ({success_rate:.1f}%)'
        })
        
    except Exception as e:
        logger.error(f"Erro ao testar conexão IPTV: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/process/status', methods=['GET'])
def get_process_status():
    """Get current process status."""
    from app.database.queries import get_process_status
    status = get_process_status()
    return jsonify(status)


@bp.route('/process/download', methods=['POST'])
def start_download():
    """Start download process."""
    try:
        from app.database import get_db
        from app.database.queries import get_all_iptvs
        from app.services.downloader import download_all_m3u
        from app.services.config import get_galeria_path
        from app.services.backup import create_backup
        from pathlib import Path
        from datetime import datetime
        
        # Create automatic backup before critical operation
        db = get_db()
        db_path = Path(__file__).parent.parent.parent / 'database' / 'iptv.db'
        backup_dir = Path(__file__).parent.parent.parent / 'backup'
        try:
            backup_file = create_backup(db_path, backup_dir)
            logger.info(f"Backup criado: {backup_file}")
        except Exception as backup_error:
            logger.warning(f"Backup falhou, continuando: {backup_error}")
        
        # Start execution stats tracking
        start_time = datetime.now()
        db.execute('''
            INSERT INTO execution_stats (tipo_execucao, inicio, status)
            VALUES ('processar', CURRENT_TIMESTAMP, 'running')
        ''')
        db.commit()
        stats_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        
        # Get all IPTV sources
        iptv_sources = get_all_iptvs()
        
        if not iptv_sources:
            return jsonify({'success': False, 'error': 'Nenhuma fonte IPTV cadastrada'})
        
        # Update process status
        db.execute('''
            INSERT INTO process_status (etapa, progresso, mensagem, status)
            VALUES ('Download', 0, 'Iniciando download de M3U...', 'running')
        ''')
        db.commit()
        
        logger.info(f"Iniciando download de {len(iptv_sources)} fontes IPTV")
        
        # Download M3U files
        cache_dir = Path(__file__).parent.parent.parent / 'cache'
        downloaded_files = download_all_m3u([dict(source) for source in iptv_sources], cache_dir)
        
        # Update progress
        db.execute('''
            UPDATE process_status 
            SET progresso = 100, mensagem = 'Download concluído com sucesso', status = 'completed'
            WHERE id = (SELECT id FROM process_status WHERE status = 'running' ORDER BY id DESC LIMIT 1)
        ''')
        db.commit()
        
        # Update execution stats
        end_time = datetime.now()
        duration = int((end_time - start_time).total_seconds())
        db.execute('''
            UPDATE execution_stats 
            SET fim = CURRENT_TIMESTAMP, duracao_segundos = ?, itens_novos = ?, status = 'completed'
            WHERE id = ?
        ''', (duration, len(downloaded_files), stats_id))
        db.commit()
        
        logger.info(f"Download concluído: {len(downloaded_files)} arquivos baixados")
        
        return jsonify({'success': True, 'message': f'Download concluído: {len(downloaded_files)} arquivos'})
    except Exception as e:
        logger.error(f"Erro no download: {str(e)}")
        # Update execution stats on error
        try:
            db.execute('''
                UPDATE execution_stats 
                SET fim = CURRENT_TIMESTAMP, status = 'failed'
                WHERE id = ?
            ''', (stats_id,))
            db.commit()
        except:
            pass
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/process/classify', methods=['POST'])
def start_classify():
    """Start classification process."""
    try:
        from app.database import get_db
        from app.database.queries import get_all_iptvs
        from app.services.parser import parse_m3u, normalize_name, calculate_hash_base, extract_quality_features, map_quality_level_to_string, calcular_score_qualidade
        from app.services.classifier import classify_media, extract_season_episode, extract_year
        from app.services.config import get_galeria_path
        from app.services.backup import create_backup
        from pathlib import Path
        from datetime import datetime
        
        # Create automatic backup before critical operation
        db = get_db()
        db_path = Path(__file__).parent.parent.parent / 'database' / 'iptv.db'
        backup_dir = Path(__file__).parent.parent.parent / 'backup'
        try:
            backup_file = create_backup(db_path, backup_dir)
            logger.info(f"Backup criado: {backup_file}")
        except Exception as backup_error:
            logger.warning(f"Backup falhou, continuando: {backup_error}")
        
        # Start execution stats tracking
        start_time = datetime.now()
        db.execute('''
            INSERT INTO execution_stats (tipo_execucao, inicio, status)
            VALUES ('processar', CURRENT_TIMESTAMP, 'running')
        ''')
        db.commit()
        stats_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        
        # Get all IPTV sources
        iptv_sources = get_all_iptvs()
        
        if not iptv_sources:
            return jsonify({'success': False, 'error': 'Nenhuma fonte IPTV cadastrada'})
        
        # Update process status
        db = get_db()
        db.execute('''
            INSERT INTO process_status (etapa, progresso, mensagem, status)
            VALUES ('Classificação', 0, 'Iniciando classificação...', 'running')
        ''')
        db.commit()
        status_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        
        logger.info("Iniciando classificação de mídias")

        # Load category corrections cache to avoid repeated DB queries
        category_corrections_cache = {}
        try:
            corrections = db.execute('SELECT hash_midia, nome_normalizado, categoria_nova FROM category_corrections').fetchall()
            for correction in corrections:
                # Cache by hash and by normalized name for fast lookup
                category_corrections_cache[correction['hash_midia']] = correction['categoria_nova']
                category_corrections_cache[correction['nome_normalizado']] = correction['categoria_nova']
            logger.info(f"Cache de categorias carregado: {len(corrections)} correções")
        except Exception as e:
            logger.warning(f"Erro ao carregar cache de categorias: {e}")
            category_corrections_cache = {}

        cache_dir = Path(__file__).parent.parent.parent / 'cache'
        total_processed = 0
        total_skipped = 0
        total_updated = 0
        total_skipped_rigorous = 0  # Counter for rigorous duplicate skips
        total_auto_blacklisted = 0  # Counter for auto-blacklisted items

        # Track timing for progress calculation
        last_progress_update = datetime.now()
        entries_since_last_update = 0

        # Batch insert buffer for performance
        insert_batch = []
        BATCH_SIZE = 1000
        
        for iptv in iptv_sources:
            # Find cached M3U file
            url_hash = hashlib.md5(iptv['url_m3u'].encode()).hexdigest()
            cache_file = cache_dir / f"{url_hash}.m3u"
            
            if not cache_file.exists():
                logger.warning(f"Arquivo cache não encontrado para {iptv['nome']}")
                continue

            # Parse M3U
            logger.info(f"Iniciando parse do arquivo: {cache_file}")
            entries = parse_m3u(str(cache_file))
            logger.info(f"Parse concluído: {len(entries)} entradas de {iptv['nome']}")

            for i, entry in enumerate(entries):
                # Log progress every 100 entries to identify freeze point
                if i % 100 == 0:
                    logger.info(f"Processando entrada {i}/{len(entries)} de {iptv['nome']}")

                try:
                    # Normalize name
                    nome_normalizado = normalize_name(entry['name'])

                    # Classify
                    categoria = classify_media(entry)

                    # Extract metadata
                    season, episode = extract_season_episode(entry['name'])
                    ano = extract_year(entry['name'])

                    # Extract quality features
                    features = extract_quality_features(entry['name'])
                    qualidade = map_quality_level_to_string(features['quality_level'])
                    tem_legendado = features['is_legendado']
                    has_hdr = features['has_hdr']
                    codec = features['codec']
                    audio = features['audio']

                    # Calculate hash without year to prevent duplicates by name
                    hash_midia = calculate_hash_base(categoria, nome_normalizado)
                    hash_base = hash_midia  # Same as hash_midia now

                    # Check if there's a learned category for this media (using cache for performance)
                    learned_category = category_corrections_cache.get(hash_midia) or category_corrections_cache.get(nome_normalizado)
                    categoria_manual = 0  # Default: not manual
                    if learned_category:
                        categoria = learned_category
                        categoria_manual = 0  # Learned category is not manual correction
                        # Don't recalculate hash - use nome_normalizado for matching to avoid hash conflicts
                except Exception as e:
                    logger.error(f"Erro ao processar entrada {i}: {entry['name']} - {str(e)}")
                    continue

                # Check if already exists by hash_midia (same name, any year)
                db_check_start = datetime.now()
                try:
                    existing = db.execute('''
                        SELECT id, black_list, categoria, categoria_manual, qualidade, tem_legendado FROM midias WHERE hash_midia = ?
                    ''', (hash_midia,)).fetchone()
                except Exception as e:
                    logger.error(f"Erro ao consultar banco para hash {hash_midia}: {str(e)}")
                    continue
                db_check_time = (datetime.now() - db_check_start).total_seconds()

                if db_check_time > 0.01:  # Log if query takes more than 10ms
                    logger.warning(f"Query lenta detectada: {db_check_time*1000:.2f}ms para hash {hash_midia}")

                # REMOVED: Redundant blacklist check - already handled in existing check above
                # This was causing 2x database queries per entry, severely impacting performance

                if existing:
                    # If exists and is blacklisted, skip
                    if existing['black_list'] == 1:
                        total_skipped += 1
                        continue

                    # If exists and has manual category, respect it (don't change)
                    if existing['categoria_manual'] == 1:
                        total_skipped += 1
                        continue

                    # Calculate quality scores
                    try:
                        score_atual = calcular_score_qualidade(existing['qualidade'], existing['tem_legendado'])
                        score_novo = calcular_score_qualidade(qualidade, tem_legendado)

                        if score_novo > score_atual:
                            try:
                                db.execute('''
                                    UPDATE midias
                                    SET qualidade = ?, tem_legendado = ?, url = ?, ultima_atualizacao = CURRENT_TIMESTAMP
                                    WHERE id = ?
                                ''', (qualidade, tem_legendado, entry['url'], existing['id']))
                                total_updated += 1
                                logger.info(f"Qualidade atualizada: {existing['qualidade']} → {qualidade} (score: {score_atual} → {score_novo})")
                            except Exception as e:
                                logger.error(f"Erro ao atualizar qualidade para id {existing['id']}: {str(e)}")
                            continue
                        else:
                            total_skipped += 1
                            continue
                    except Exception as e:
                        logger.error(f"Erro ao calcular scores de qualidade: {str(e)}")
                        total_skipped += 1
                        continue

                # AUTO-BLACKLIST CHECK: DISABLED - BUG CAUSING 52% OF ITEMS TO BE BLACKLISTED
                # The LIKE '%nome_base%' pattern is too permissive and causes cascading blacklist
                # TODO: Improve similarity matching before re-enabling
                # should_auto_blacklist, auto_blacklist_reason = duplicate_manager.check_and_apply_auto_blacklist(
                #     nome_normalizado, entry['name']
                # )
                #
                # black_list_value = 1 if should_auto_blacklist else 0
                #
                # if should_auto_blacklist:
                #     total_auto_blacklisted += 1
                #     logger.info(f"AUTO-BLACKLIST: '{entry['name']}' auto-blacklisted - {auto_blacklist_reason}")
                
                # Always set to 0 (not blacklisted) until auto-blacklist is fixed
                black_list_value = 0

                # Add to batch insert buffer
                insert_batch.append((
                    iptv['id'], entry['name'], nome_normalizado, entry['url'], categoria,
                    hash_midia, hash_base, iptv['nome'], ano, season, episode,
                    black_list_value, categoria_manual, qualidade, tem_legendado
                ))

                # Execute batch insert when buffer is full
                if len(insert_batch) >= BATCH_SIZE:
                    try:
                        db.executemany('''
                            INSERT INTO midias (iptv_id, nome_da_midia, nome_normalizado, url, categoria,
                                              hash_midia, hash_base, origem_iptv, ano, season, episode,
                                              black_list, categoria_manual, qualidade, tem_legendado, data_coleta)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        ''', insert_batch)
                        total_processed += len(insert_batch)
                        insert_batch = []
                    except Exception as e:
                        logger.error(f"Erro ao inserir batch: {str(e)}")
                        insert_batch = []

                entries_since_last_update += 1

                # Update progress every 100 entries for better visibility (no commit)
                # Also update on first entry (i == 0) to show immediate progress
                if i % 100 == 0 or i == 0:
                    progress = int((i / len(entries)) * 100)
                    current_time = datetime.now()
                    time_since_update = (current_time - last_progress_update).total_seconds()

                    # Calculate speed (entries per second)
                    if time_since_update > 0 and entries_since_last_update > 0:
                        speed = entries_since_last_update / time_since_update
                        # Estimate remaining time
                        remaining_entries = len(entries) - i
                        eta_seconds = remaining_entries / speed if speed > 0 else 0
                        eta_minutes = int(eta_seconds / 60)
                        eta_str = f"{eta_minutes}min" if eta_minutes > 0 else f"{int(eta_seconds)}s"

                        progress_message = f'Processando {iptv["nome"]}: {i}/{len(entries)} ({progress}%) - {speed:.0f} itens/s - ETA: {eta_str}'
                    else:
                        progress_message = f'Processando {iptv["nome"]}: {i}/{len(entries)} ({progress}%)'

                    db.execute('''
                        UPDATE process_status
                        SET progresso = ?, mensagem = ?
                        WHERE id = ?
                    ''', (progress, progress_message, status_id))

                    # Reset timing counters
                    last_progress_update = current_time
                    entries_since_last_update = 0

                # Commit data every 5000 entries to reduce I/O overhead
                if i % 5000 == 0:
                    db.commit()

        # Insert any remaining items in the batch buffer
        if insert_batch:
            try:
                db.executemany('''
                    INSERT INTO midias (iptv_id, nome_da_midia, nome_normalizado, url, categoria,
                                      hash_midia, hash_base, origem_iptv, ano, season, episode,
                                      black_list, categoria_manual, qualidade, tem_legendado, data_coleta)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', insert_batch)
                total_processed += len(insert_batch)
                insert_batch = []
            except Exception as e:
                logger.error(f"Erro ao inserir batch final: {str(e)}")

        # Final commit for any remaining uncommitted changes
        try:
            db.commit()
        except Exception as e:
            logger.error(f"Erro no commit final: {str(e)}")
        
        # Final update
        db.execute('''
            UPDATE process_status
            SET progresso = 100, mensagem = 'Classificação concluída', status = 'completed'
            WHERE id = ?
        ''', (status_id,))
        db.commit()
        
        # Update execution stats
        end_time = datetime.now()
        duration = int((end_time - start_time).total_seconds())
        db.execute('''
            UPDATE execution_stats 
            SET fim = CURRENT_TIMESTAMP, duracao_segundos = ?, itens_novos = ?, itens_ignorados = ?, status = 'completed'
            WHERE id = ?
        ''', (duration, total_processed, total_skipped, stats_id))
        db.commit()
        
        logger.info(f"Classificação concluída: {total_processed} novas mídias, {total_skipped} ignoradas ({total_skipped_rigorous} por verificação rigorosa), {total_auto_blacklisted} auto-blacklistadas)")
        
        return jsonify({'success': True, 'message': f'Classificação concluída: {total_processed} novas mídias, {total_skipped} ignoradas ({total_skipped_rigorous} por verificação rigorosa), {total_auto_blacklisted} auto-blacklistadas'})
    except Exception as e:
        logger.error(f"Erro na classificação: {str(e)}")
        # Update execution stats on error
        try:
            db.execute('''
                UPDATE execution_stats
                SET fim = CURRENT_TIMESTAMP, status = 'failed'
                WHERE id = ?
            ''', (stats_id,))
            db.commit()
        except Exception as db_error:
            logger.error(f"Erro ao atualizar execution_stats: {str(db_error)}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/process/export', methods=['POST'])
def start_export():
    """Start export process (export all items)."""
    try:
        from app.database import get_db
        from app.services.exporter import export_all_media
        from app.services.backup import create_backup
        from pathlib import Path
        from datetime import datetime
        
        # Create automatic backup before critical operation
        db = get_db()
        db_path = Path(__file__).parent.parent.parent / 'database' / 'iptv.db'
        backup_dir = Path(__file__).parent.parent.parent / 'backup'
        try:
            backup_file = create_backup(db_path, backup_dir)
            logger.info(f"Backup criado: {backup_file}")
        except Exception as backup_error:
            logger.warning(f"Backup falhou, continuando: {backup_error}")
        
        # Start execution stats tracking
        start_time = datetime.now()
        db.execute('''
            INSERT INTO execution_stats (tipo_execucao, inicio, status)
            VALUES ('exportar', CURRENT_TIMESTAMP, 'running')
        ''')
        db.commit()
        stats_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        
        # Get all media to export
        media_items = db.execute('''
            SELECT * FROM midias WHERE status = 1 AND black_list = 0
        ''').fetchall()
        
        if not media_items:
            return jsonify({'success': False, 'error': 'Nenhuma mídia para exportar'})
        
        # Update process status
        db.execute('''
            INSERT INTO process_status (etapa, progresso, mensagem, status)
            VALUES ('Exportação', 0, 'Iniciando exportação...', 'running')
        ''')
        db.commit()
        
        logger.info(f"Iniciando exportação de {len(media_items)} mídias")

        # Export media
        export_all_media([dict(item) for item in media_items], db)
        
        # Final update
        db.execute('''
            UPDATE process_status 
            SET progresso = 100, mensagem = 'Exportação concluída', status = 'completed'
            WHERE id = (SELECT id FROM process_status WHERE status = 'running' ORDER BY id DESC LIMIT 1)
        ''')
        db.commit()
        
        # Update execution stats
        end_time = datetime.now()
        duration = int((end_time - start_time).total_seconds())
        db.execute('''
            UPDATE execution_stats 
            SET fim = CURRENT_TIMESTAMP, duracao_segundos = ?, itens_exportados = ?, status = 'completed'
            WHERE id = ?
        ''', (duration, len(media_items), stats_id))
        db.commit()
        
        logger.info(f"Exportação concluída: {len(media_items)} mídias")

        return jsonify({'success': True, 'message': f'Exportação concluída: {len(media_items)} mídias'})
    except Exception as e:
        logger.error(f"Erro na exportação: {str(e)}")
        # Update execution stats on error
        try:
            db.execute('''
                UPDATE execution_stats 
                SET fim = CURRENT_TIMESTAMP, status = 'failed'
                WHERE id = ?
            ''', (stats_id,))
            db.commit()
        except:
            pass
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/process/logs', methods=['GET'])
def stream_logs():
    """Stream logs via SSE."""
    from flask import Response
    import time
    from pathlib import Path
    
    # Calculate log file path before generator
    log_file = Path(__file__).parent.parent.parent / 'app' / 'logs' / 'process.log'
    
    def generate():
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                f.seek(0, 2)
                while True:
                    line = f.readline()
                    if line:
                        yield f"data: {line}\n\n"
                    time.sleep(0.1)
        else:
            yield f"data: Log file not found\n\n"
    
    return Response(generate(), mimetype='text/event-stream')


@bp.route('/process/progress', methods=['GET'])
def get_progress():
    """Get current progress (simple endpoint without SSE)."""
    from app.database import get_db
    
    try:
        db = get_db()
        progress = db.execute('''
            SELECT etapa, progresso, mensagem, status FROM process_status 
            ORDER BY id DESC LIMIT 1
        ''').fetchone()
        
        if progress:
            return jsonify(dict(progress))
        else:
            # Return empty status when no process exists
            return jsonify({'etapa': None, 'progresso': 0, 'mensagem': 'Aguardando', 'status': 'idle'})
    except Exception as e:
        return jsonify({'error': str(e)})


@bp.route('/logs/content', methods=['GET'])
def get_log_content():
    """Get log file content."""
    from flask import Response
    from pathlib import Path
    
    filename = request.args.get('file', 'process.log')
    log_file = Path(__file__).parent.parent.parent / 'app' / 'logs' / filename
    
    if log_file.exists():
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return Response(content, mimetype='text/plain')
    else:
        return Response('Log file not found', status=404, mimetype='text/plain')


@bp.route('/logs/clear', methods=['POST'])
def clear_log():
    """Clear log file."""
    from pathlib import Path
    import json
    
    filename = request.args.get('file', 'process.log')
    log_file = Path(__file__).parent.parent.parent / 'app' / 'logs' / filename
    
    try:
        if log_file.exists():
            log_file.write_text('')
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Log file not found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})



@bp.route('/logs/filter-errors', methods=['GET'])
def filter_error_logs():
    """Filter error lines from process.log and export.log and create error.log."""
    from pathlib import Path
    from flask import Response
    
    logs_dir = Path(__file__).parent.parent.parent / 'app' / 'logs'
    error_log_file = logs_dir / 'error.log'
    
    # Log files to filter
    source_files = ['process.log', 'export.log']
    
    # Error keywords to filter
    error_keywords = ['ERROR', 'ERRO', 'Exception', 'Failed', 'FALHOU', 'Error', 'exception', 'failed', 'falhou', 'CRITICAL', 'Critical']
    
    try:
        error_lines = []
        
        for source_file in source_files:
            source_path = logs_dir / source_file
            if source_path.exists():
                with open(source_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        # Check if line contains any error keyword
                        if any(keyword in line for keyword in error_keywords):
                            # Add source file reference
                            error_lines.append(f"[{source_file}] {line}")
        
        # Write error.log with filtered lines
        error_log_file.write_text('\n'.join(error_lines))
        
        # Return the filtered content
        return Response('\n'.join(error_lines), mimetype='text/plain')
        
    except Exception as e:
        return Response(f'Erro ao filtrar logs: {str(e)}', status=500, mimetype='text/plain')


@bp.route('/media/items', methods=['GET'])
def get_media_items():
    """Get all media items with optional filtering."""
    from app.database import get_db
    
    category = request.args.get('category')
    status = request.args.get('status')
    blacklist = request.args.get('blacklist')
    search = request.args.get('search')
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    db = get_db()
    
    # Build query with filters
    query = 'SELECT * FROM midias WHERE 1=1'
    params = []
    
    if category:
        query += ' AND categoria = ?'
        params.append(category)
    
    if status is not None:
        query += ' AND status = ?'
        params.append(int(status))
    
    # Default to black_list = 0 unless explicitly requested
    if blacklist is not None:
        query += ' AND black_list = ?'
        params.append(int(blacklist))
    else:
        query += ' AND black_list = 0'
    
    if search:
        query += ' AND (nome_da_midia LIKE ? OR nome_normalizado LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%'])
    
    query += ' ORDER BY nome_da_midia ASC LIMIT ? OFFSET ?'
    params.extend([limit, offset])
    
    items = db.execute(query, params).fetchall()
    
    # Get total count
    count_query = 'SELECT COUNT(*) FROM midias WHERE 1=1'
    count_params = []
    
    if category:
        count_query += ' AND categoria = ?'
        count_params.append(category)
    
    if status is not None:
        count_query += ' AND status = ?'
        count_params.append(int(status))
    
    # Default to black_list = 0 unless explicitly requested
    if blacklist is not None:
        count_query += ' AND black_list = ?'
        count_params.append(int(blacklist))
    else:
        count_query += ' AND black_list = 0'
    
    if search:
        count_query += ' AND (nome_da_midia LIKE ? OR nome_normalizado LIKE ?)'
        count_params.extend([f'%{search}%', f'%{search}%'])
    
    total = db.execute(count_query, count_params).fetchone()[0]
    
    return jsonify({
        'items': [dict(item) for item in items],
        'total': total,
        'limit': limit,
        'offset': offset
    })


@bp.route('/media/items/<int:media_id>', methods=['DELETE'])
def delete_media_item(media_id):
    """Delete a media item (soft delete)."""
    from app.database import get_db
    
    db = get_db()
    
    try:
        db.execute('UPDATE midias SET status = 0 WHERE id = ?', (media_id,))
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/media/items/<int:media_id>/blacklist', methods=['POST'])
def toggle_blacklist(media_id):
    """Toggle blacklist status for a media item."""
    from app.database import get_db

    db = get_db()
    
    try:
        # Get current blacklist status
        result = db.execute('SELECT black_list FROM midias WHERE id = ?', (media_id,)).fetchone()
        if not result:
            return jsonify({'success': False, 'error': 'Media item not found'})
        
        current_blacklist = result['black_list']
        new_blacklist = 0 if current_blacklist == 1 else 1
        
        db.execute('UPDATE midias SET black_list = ? WHERE id = ?', (new_blacklist, media_id))
        db.commit()
        return jsonify({'success': True, 'blacklist': new_blacklist})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/media/items/blacklist-batch', methods=['POST'])
def blacklist_batch():
    """Toggle blacklist status for multiple media items at once."""
    from app.database import get_db

    db = get_db()
    data = request.get_json()
    ids = data.get('ids', [])

    if not ids:
        return jsonify({'success': False, 'error': 'No IDs provided'})

    try:
        # Get current blacklist status for each item
        current_status = {}
        for media_id in ids:
            result = db.execute('SELECT black_list FROM midias WHERE id = ?', (media_id,)).fetchone()
            if result:
                current_status[media_id] = result['black_list']

        # Toggle blacklist status
        count = 0
        for media_id, current_black_list in current_status.items():
            new_status = 0 if current_black_list == 1 else 1
            db.execute('UPDATE midias SET black_list = ? WHERE id = ?', (new_status, media_id))
            count += 1

        db.commit()
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/media/items/process-duplicates', methods=['POST'])
def process_duplicates():
    """Process selected duplicate items - keep first as original, blacklist others."""
    from app.database import get_db
    from app.services.parser import remove_quality_from_name

    db = get_db()
    data = request.get_json()
    ids = data.get('ids', [])

    if not ids:
        return jsonify({'success': False, 'error': 'No IDs provided'})

    try:
        # Get items with their names
        placeholders = ','.join(['?'] * len(ids))
        items = db.execute(f'''
            SELECT id, nome_normalizado, nome_da_midia
            FROM midias
            WHERE id IN ({placeholders})
        ''', ids).fetchall()

        # Group by normalized name without quality indicators
        name_groups = {}
        for item in items:
            name = item['nome_normalizado'] or item['nome_da_midia']
            # Remove quality indicators for grouping
            name_without_quality = remove_quality_from_name(name)
            if name_without_quality not in name_groups:
                name_groups[name_without_quality] = []
            name_groups[name_without_quality].append(item['id'])

        # Process each group - keep first, blacklist others
        blacklist_count = 0
        for name, item_ids in name_groups.items():
            if len(item_ids) > 1:
                # Keep first as original
                original_id = item_ids[0]
                # Blacklist the rest
                for duplicate_id in item_ids[1:]:
                    db.execute('UPDATE midias SET black_list = 1 WHERE id = ?', (duplicate_id,))
                    blacklist_count += 1

        db.commit()
        return jsonify({'success': True, 'count': blacklist_count})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/media/items/change-category-batch', methods=['POST'])
def change_category_batch():
    """Change category for multiple media items at once."""
    from app.database import get_db

    db = get_db()
    data = request.get_json()
    ids = data.get('ids', [])
    new_category = data.get('category')

    if not ids:
        return jsonify({'success': False, 'error': 'No IDs provided'})

    if not new_category:
        return jsonify({'success': False, 'error': 'No category provided'})

    try:
        from app.services.category_learner import record_category_correction
        count = 0
        for media_id in ids:
            # Get current category before update
            current = db.execute('SELECT categoria, hash_midia, nome_normalizado FROM midias WHERE id = ?', (media_id,)).fetchone()
            if current:
                old_category = current['categoria']
                # Update category
                db.execute('UPDATE midias SET categoria = ?, categoria_manual = 1 WHERE id = ?', (new_category, media_id))
                # Record correction for learning
                record_category_correction(media_id, old_category, new_category)
                count += 1

        db.commit()
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/media/items/<int:media_id>/category', methods=['POST'])
def change_category(media_id):
    """Change category for a media item."""
    from app.database import get_db
    
    db = get_db()
    data = request.get_json()
    new_category = data.get('category')
    
    if not new_category:
        return jsonify({'success': False, 'error': 'Category is required'})

    try:
        from app.services.category_learner import record_category_correction
        # Get current category before update
        current = db.execute('SELECT categoria, hash_midia, nome_normalizado FROM midias WHERE id = ?', (media_id,)).fetchone()
        if current:
            old_category = current['categoria']
            # Update category
            db.execute('UPDATE midias SET categoria = ?, categoria_manual = 1 WHERE id = ?', (new_category, media_id))
            # Record correction for learning
            record_category_correction(media_id, old_category, new_category)
            db.commit()
            return jsonify({'success': True, 'category': new_category})
        else:
            return jsonify({'success': False, 'error': 'Media not found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/media/items/<int:media_id>/duplicates', methods=['GET'])
def get_duplicates(media_id):
    """Get items with same hash_midia and base name (enhanced duplicate detection)."""
    from app.database import get_db
    from app.services.duplicate_manager import DuplicateManager
    
    db = get_db()
    
    try:
        duplicate_manager = DuplicateManager(db)
        
        # Use enhanced duplicate detection
        result = duplicate_manager.find_all_duplicates(media_id)
        
        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']})
        
        return jsonify({
            'success': True,
            'hash_duplicates': result['hash_duplicates'],
            'name_duplicates': result['name_duplicates'],
            'total_duplicates': result['total_duplicates']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/media/categories', methods=['GET'])
def get_media_categories():
    """Get all media categories with counts."""
    from app.database import get_db
    
    db = get_db()
    
    categories = db.execute('''
        SELECT categoria, COUNT(*) as count
        FROM midias
        WHERE status = 1
        GROUP BY categoria
        ORDER BY count DESC
    ''').fetchall()
    
    return jsonify([dict(cat) for cat in categories])


@bp.route('/process/tmdb', methods=['POST'])
def start_tmdb_enrichment():
    """Start TMDB enrichment process (limited to 10 items for demonstration)."""
    try:
        from app.database import get_db
        from app.services.tmdb import get_movie_info, get_tv_info
        from app.services.backup import create_backup
        from pathlib import Path
        from datetime import datetime

        # Create automatic backup before critical operation
        db = get_db()
        db_path = Path(__file__).parent.parent.parent / 'database' / 'iptv.db'
        backup_dir = Path(__file__).parent.parent.parent / 'backup'
        try:
            backup_file = create_backup(db_path, backup_dir)
            logger.info(f"Backup criado: {backup_file}")
        except Exception as backup_error:
            logger.warning(f"Backup falhou, continuando: {backup_error}")

        # Start execution stats tracking
        start_time = datetime.now()
        db.execute('''
            INSERT INTO execution_stats (tipo_execucao, inicio, status)
            VALUES ('tmdb', CURRENT_TIMESTAMP, 'running')
        ''')
        db.commit()
        stats_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

        # Get limited media to enrich (10 items for demonstration)
        media_items = db.execute('''
            SELECT * FROM midias WHERE status = 1 AND black_list = 0 AND tmdb_id IS NULL LIMIT 10
        ''').fetchall()

        if not media_items:
            return jsonify({'success': False, 'error': 'Nenhuma mídia para enriquecer'})

        # Update process status
        db.execute('''
            INSERT INTO process_status (etapa, progresso, mensagem, status)
            VALUES ('TMDB', 0, 'Iniciando enriquecimento TMDB...', 'running')
        ''')
        db.commit()

        logger.info(f"Iniciando enriquecimento TMDB de {len(media_items)} mídias (demonstração)")

        enriched_count = 0
        blacklist_count = 0
        category_change_count = 0
        for i, item in enumerate(media_items):
            item_dict = dict(item)
            categoria = item_dict.get('categoria')
            nome = item_dict.get('nome_da_midia')

            try:
                tmdb_info = get_movie_info(nome, categoria=categoria)

                if tmdb_info and tmdb_info.get('tmdb_id'):
                    # Update with TMDB info
                    db.execute('''
                        UPDATE midias SET tmdb_id = ?, imagem_url = ?, ultima_atualizacao = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (tmdb_info['tmdb_id'], tmdb_info.get('poster'), item_dict['id']))
                    enriched_count += 1

                    # Check if category needs to be changed based on TMDB
                    if categoria == 'Adult' and not tmdb_info.get('adult', False):
                        # TMDB says it's not adult, change to Movie
                        db.execute('UPDATE midias SET categoria = ? WHERE id = ?', ('Movie', item_dict['id']))
                        category_change_count += 1
                    elif categoria == 'Movie' and tmdb_info.get('adult', False):
                        # TMDB says it's adult, change to Adult
                        db.execute('UPDATE midias SET categoria = ? WHERE id = ?', ('Adult', item_dict['id']))
                        category_change_count += 1
                elif categoria == 'Adult':
                    # Adult film not recognized by TMDB - blacklist it
                    db.execute('UPDATE midias SET black_list = 1 WHERE id = ?', (item_dict['id'],))
                    blacklist_count += 1

                # Update progress
                progress = int((i + 1) / len(media_items) * 100)
                db.execute('''
                    UPDATE process_status
                    SET progresso = ?, mensagem = ?
                    WHERE id = (SELECT id FROM process_status WHERE status = 'running' ORDER BY id DESC LIMIT 1)
                ''', (progress, f'Enriquecendo {i + 1}/{len(media_items)}'))
                db.commit()

            except Exception as e:
                logger.error(f"Erro ao enriquecer {nome}: {e}")

        db.commit()

        # Final update
        db.execute('''
            UPDATE process_status
            SET progresso = 100, mensagem = 'Enriquecimento TMDB concluído', status = 'completed'
            WHERE id = (SELECT id FROM process_status WHERE status = 'running' ORDER BY id DESC LIMIT 1)
        ''')
        db.commit()

        # Update execution stats
        end_time = datetime.now()
        duration = int((end_time - start_time).total_seconds())
        db.execute('''
            UPDATE execution_stats
            SET fim = CURRENT_TIMESTAMP, duracao_segundos = ?, itens_novos = ?, status = 'completed'
            WHERE id = ?
        ''', (duration, enriched_count, stats_id))
        db.commit()
        
        logger.info(f"Enriquecimento TMDB concluído: {enriched_count} mídias")
        
        return jsonify({'success': True, 'message': f'Enriquecimento TMDB concluído: {enriched_count} mídias (demonstração)'})
    except Exception as e:
        logger.error(f"Erro no enriquecimento TMDB: {str(e)}")
        # Update execution stats on error
        try:
            db.execute('''
                UPDATE execution_stats 
                SET fim = CURRENT_TIMESTAMP, status = 'failed'
                WHERE id = ?
            ''', (stats_id,))
            db.commit()
        except:
            pass
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/process/epg', methods=['POST'])
def start_epg_fetch():
    """Start EPG fetch process (demonstration)."""
    try:
        from app.database import get_db
        from app.services.epg_fetcher import download_epg_file
        from app.services.backup import create_backup
        from pathlib import Path
        from datetime import datetime
        
        # Create automatic backup before critical operation
        db = get_db()
        db_path = Path(__file__).parent.parent.parent / 'database' / 'iptv.db'
        backup_dir = Path(__file__).parent.parent.parent / 'backup'
        try:
            backup_file = create_backup(db_path, backup_dir)
            logger.info(f"Backup criado: {backup_file}")
        except Exception as backup_error:
            logger.warning(f"Backup falhou, continuando: {backup_error}")
        
        # Start execution stats tracking
        start_time = datetime.now()
        db.execute('''
            INSERT INTO execution_stats (tipo_execucao, inicio, status)
            VALUES ('epg', CURRENT_TIMESTAMP, 'running')
        ''')
        db.commit()
        stats_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        
        # Get IPTV sources with EPG URLs
        iptv_sources = db.execute('SELECT * FROM iptvs WHERE url_epg IS NOT NULL AND url_epg != ""').fetchall()
        
        if not iptv_sources:
            return jsonify({'success': False, 'error': 'Nenhuma fonte EPG cadastrada'})
        
        # Update process status
        db.execute('''
            INSERT INTO process_status (etapa, progresso, mensagem, status)
            VALUES ('EPG', 0, 'Iniciando download de EPG...', 'running')
        ''')
        db.commit()
        
        logger.info(f"Iniciando download de EPG de {len(iptv_sources)} fontes (demonstração)")
        
        downloaded_count = 0
        galeria_path = Path(__file__).parent.parent.parent.parent / 'Galeria'
        
        for i, iptv in enumerate(iptv_sources):
            try:
                epg_url = iptv['url_epg']
                output_path = galeria_path / 'TV' / f"epg_{iptv['nome']}.xml"
                
                success = download_epg_file(epg_url, output_path)
                if success:
                    downloaded_count += 1
                
                # Update progress
                progress = int((i + 1) / len(iptv_sources) * 100)
                db.execute('''
                    UPDATE process_status 
                    SET progresso = ?, mensagem = ?
                    WHERE id = (SELECT id FROM process_status WHERE status = 'running' ORDER BY id DESC LIMIT 1)
                ''', (progress, f'Downloading EPG {i + 1}/{len(iptv_sources)}'))
                db.commit()
                
            except Exception as e:
                logger.error(f"Erro ao baixar EPG de {iptv['nome']}: {e}")
        
        # Final update
        db.execute('''
            UPDATE process_status 
            SET progresso = 100, mensagem = 'Download EPG concluído', status = 'completed'
            WHERE id = (SELECT id FROM process_status WHERE status = 'running' ORDER BY id DESC LIMIT 1)
        ''')
        db.commit()
        
        # Update execution stats
        end_time = datetime.now()
        duration = int((end_time - start_time).total_seconds())
        db.execute('''
            UPDATE execution_stats 
            SET fim = CURRENT_TIMESTAMP, duracao_segundos = ?, itens_novos = ?, status = 'completed'
            WHERE id = ?
        ''', (duration, downloaded_count, stats_id))
        db.commit()
        
        logger.info(f"Download EPG concluído: {downloaded_count} arquivos")
        
        return jsonify({'success': True, 'message': f'Download EPG concluído: {downloaded_count} arquivos (demonstração)'})
    except Exception as e:
        logger.error(f"Erro no download EPG: {str(e)}")
        # Update execution stats on error
        try:
            db.execute('''
                UPDATE execution_stats 
                SET fim = CURRENT_TIMESTAMP, status = 'failed'
                WHERE id = ?
            ''', (stats_id,))
            db.commit()
        except:
            pass
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/process/tv-m3u', methods=['POST'])
def start_tv_m3u_build():
    """Start TV M3U build process."""
    try:
        from app.database import get_db
        from app.services.tv_builder import build_tv_m3u
        from app.services.backup import create_backup
        from pathlib import Path
        from datetime import datetime
        
        # Create automatic backup before critical operation
        db = get_db()
        db_path = Path(__file__).parent.parent.parent / 'database' / 'iptv.db'
        backup_dir = Path(__file__).parent.parent.parent / 'backup'
        try:
            backup_file = create_backup(db_path, backup_dir)
            logger.info(f"Backup criado: {backup_file}")
        except Exception as backup_error:
            logger.warning(f"Backup falhou, continuando: {backup_error}")
        
        # Start execution stats tracking
        start_time = datetime.now()
        db.execute('''
            INSERT INTO execution_stats (tipo_execucao, inicio, status)
            VALUES ('tv_m3u', CURRENT_TIMESTAMP, 'running')
        ''')
        db.commit()
        stats_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        
        # Update process status
        db.execute('''
            INSERT INTO process_status (etapa, progresso, mensagem, status)
            VALUES ('TV M3U', 0, 'Iniciando geração de TV M3U...', 'running')
        ''')
        db.commit()
        
        logger.info("Iniciando geração de TV M3U")
        
        # Build TV M3U
        tv_m3u_path = build_tv_m3u()
        
        # Get TV channels count
        tv_channels_count = db.execute('SELECT COUNT(*) FROM tv_channels WHERE status = 1 AND black_list = 0').fetchone()[0]
        
        # Final update
        db.execute('''
            UPDATE process_status 
            SET progresso = 100, mensagem = 'Geração TV M3U concluída', status = 'completed'
            WHERE id = (SELECT id FROM process_status WHERE status = 'running' ORDER BY id DESC LIMIT 1)
        ''')
        db.commit()
        
        # Update execution stats
        end_time = datetime.now()
        duration = int((end_time - start_time).total_seconds())
        db.execute('''
            UPDATE execution_stats 
            SET fim = CURRENT_TIMESTAMP, duracao_segundos = ?, itens_novos = ?, status = 'completed'
            WHERE id = ?
        ''', (duration, tv_channels_count, stats_id))
        db.commit()
        
        logger.info(f"Geração TV M3U concluída: {tv_channels_count} canais")
        
        return jsonify({'success': True, 'message': f'Geração TV M3U concluída: {tv_channels_count} canais'})
    except Exception as e:
        logger.error(f"Erro na geração TV M3U: {str(e)}")
        # Update execution stats on error
        try:
            db.execute('''
                UPDATE execution_stats 
                SET fim = CURRENT_TIMESTAMP, status = 'failed'
                WHERE id = ?
            ''', (stats_id,))
            db.commit()
        except:
            pass
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/reclassify/start', methods=['POST'])
def start_reclassification():
    """Start intelligent reclassification process."""
    try:
        from app.database import get_db
        from app.services.reclassifier import MediaReclassifier
        from app.services.backup import create_backup
        from pathlib import Path
        from datetime import datetime
        import threading
        
        data = request.get_json()
        mode = data.get('mode', 'simulation')  # 'simulation' or 'execution'
        batch_size = data.get('batch_size', 1000)
        
        if mode not in ['simulation', 'execution']:
            return jsonify({'success': False, 'error': 'Modo inválido. Use "simulation" ou "execution"'})
        
        # Create automatic backup before critical operation (only in execution mode)
        if mode == 'execution':
            db = get_db()
            db_path = Path(__file__).parent.parent.parent / 'database' / 'iptv.db'
            backup_dir = Path(__file__).parent.parent.parent / 'backup'
            try:
                backup_file = create_backup(db_path, backup_dir)
                logger.info(f"Backup criado: {backup_file}")
            except Exception as backup_error:
                logger.warning(f"Backup falhou, continuando: {backup_error}")
        
        # Start execution stats tracking
        db = get_db()
        start_time = datetime.now()
        db.execute('''
            INSERT INTO execution_stats (tipo_execucao, inicio, status)
            VALUES ('reclassify', CURRENT_TIMESTAMP, 'running')
        ''')
        db.commit()
        stats_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        
        # Update process status
        db.execute('''
            INSERT INTO process_status (etapa, progresso, mensagem, status)
            VALUES ('Reclassificação', 0, ?, 'running')
        ''', (f'Iniciando reclassificação (modo: {mode})...',))
        db.commit()
        
        logger.info(f"Iniciando reclassificação (modo: {mode}, batch_size: {batch_size})")
        
        # Start reclassification in background thread
        def reclassify_thread():
            try:
                import json
                from app.app import create_app
                from app.database import get_db
                
                # Create app context for this thread
                app_context = create_app().app_context()
                app_context.push()
                
                # Create new database connection in this thread
                db_thread = get_db()
                
                reclassifier = MediaReclassifier()
                
                # Get total count
                total_count = db_thread.execute('SELECT COUNT(*) FROM midias WHERE status = 1 AND black_list = 0').fetchone()[0]
                processed_count = 0
                changed_count = 0
                
                # Process in batches
                offset = 0
                results_by_category = {cat: 0 for cat in reclassifier.categories}
                
                while offset < total_count:
                    # Get batch
                    media_items = db_thread.execute('''
                        SELECT * FROM midias WHERE status = 1 AND black_list = 0 LIMIT ? OFFSET ?
                    ''', (batch_size, offset)).fetchall()
                    
                    if not media_items:
                        break
                    
                    # Reclassify batch
                    results = reclassifier.reclassify_batch([dict(item) for item in media_items])
                    
                    # Process results
                    for result in results:
                        if result['changed']:
                            changed_count += 1
                            results_by_category[result['new_category']] += 1
                            
                            # In execution mode, update database
                            if mode == 'execution':
                                db_thread.execute('''
                                    UPDATE midias SET categoria = ?, ultima_atualizacao = CURRENT_TIMESTAMP
                                    WHERE id = ?
                                ''', (result['new_category'], result['media_id']))
                                
                                # Add to audit log
                                db_thread.execute('''
                                    INSERT INTO classification_audit 
                                    (media_id, categoria_antiga, categoria_nova, score_json, reason, confidence)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                ''', (result['media_id'], result['current_category'], result['new_category'],
                                      json.dumps(result['score_json']), result['reason'], result['confidence']))
                    
                    processed_count += len(media_items)
                    offset += batch_size
                    
                    # Update progress
                    progress = int((processed_count / total_count) * 100)
                    db_thread.execute('''
                        UPDATE process_status 
                        SET progresso = ?, mensagem = ?
                        WHERE id = (SELECT id FROM process_status WHERE status = 'running' ORDER BY id DESC LIMIT 1)
                    ''', (progress, f'Processando {processed_count}/{total_count} ({changed_count} alterados)'))
                    db_thread.commit()
                    
                    # Small delay to prevent overwhelming the database
                    import time
                    time.sleep(0.1)
                
                # Final update
                db_thread.execute('''
                    UPDATE process_status 
                    SET progresso = 100, mensagem = 'Reclassificação concluída', status = 'completed'
                    WHERE id = (SELECT id FROM process_status WHERE status = 'running' ORDER BY id DESC LIMIT 1)
                ''')
                db_thread.commit()
                
                # Update execution stats
                end_time = datetime.now()
                duration = int((end_time - start_time).total_seconds())
                db_thread.execute('''
                    UPDATE execution_stats 
                    SET fim = CURRENT_TIMESTAMP, duracao_segundos = ?, itens_novos = ?, itens_ignorados = ?, status = 'completed'
                    WHERE id = ?
                ''', (duration, changed_count, processed_count - changed_count, stats_id))
                db_thread.commit()
                
                logger.info(f"Reclassificação concluída: {processed_count} processados, {changed_count} alterados")
                
                # Pop app context
                app_context.pop()
                
            except Exception as e:
                logger.error(f"Erro na reclassificação: {str(e)}")
                # Update execution stats on error
                try:
                    from app.app import create_app
                    from app.database import get_db
                    app_context = create_app().app_context()
                    app_context.push()
                    db_thread = get_db()
                    db_thread.execute('''
                        UPDATE execution_stats 
                        SET fim = CURRENT_TIMESTAMP, status = 'failed'
                        WHERE id = ?
                    ''', (stats_id,))
                    db_thread.commit()
                    app_context.pop()
                except:
                    pass
        
        # Start thread
        thread = threading.Thread(target=reclassify_thread)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': f'Reclassificação iniciada em modo {mode}',
            'mode': mode,
            'batch_size': batch_size
        })
        
    except Exception as e:
        logger.error(f"Erro ao iniciar reclassificação: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/reclassify/status', methods=['GET'])
def get_reclassification_status():
    """Get current reclassification status."""
    try:
        from app.database import get_db
        
        db = get_db()
        
        # Get process status
        process_status = db.execute('''
            SELECT etapa, progresso, mensagem, status
            FROM process_status
            WHERE etapa = 'Reclassificação' AND status = 'running'
            ORDER BY id DESC LIMIT 1
        ''').fetchone()
        
        if not process_status:
            # Get last completed reclassification
            process_status = db.execute('''
                SELECT etapa, progresso, mensagem, status
                FROM process_status
                WHERE etapa = 'Reclassificação'
                ORDER BY id DESC LIMIT 1
            ''').fetchone()
        
        if process_status:
            return jsonify({
                'success': True,
                'status': dict(process_status)
            })
        else:
            return jsonify({
                'success': True,
                'status': None,
                'message': 'Nenhuma reclassificação encontrada'
            })
            
    except Exception as e:
        logger.error(f"Erro ao obter status da reclassificação: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/reclassify/report', methods=['GET'])
def get_reclassification_report():
    """Get reclassification report."""
    try:
        from app.database import get_db
        
        db = get_db()
        
        # Get audit statistics
        audit_stats = db.execute('''
            SELECT 
                COUNT(*) as total_changed,
                COUNT(DISTINCT media_id) as unique_media,
                AVG(confidence) as avg_confidence
            FROM classification_audit
        ''').fetchone()
        
        # Get changes by category
        changes_by_category = db.execute('''
            SELECT categoria_nova, COUNT(*) as count
            FROM classification_audit
            GROUP BY categoria_nova
            ORDER BY count DESC
        ''').fetchall()
        
        # Get recent changes
        recent_changes = db.execute('''
            SELECT 
                ca.media_id,
                m.nome_da_midia,
                ca.categoria_antiga,
                ca.categoria_nova,
                ca.confidence,
                ca.reason,
                ca.created_at
            FROM classification_audit ca
            JOIN midias m ON ca.media_id = m.id
            ORDER BY ca.created_at DESC
            LIMIT 20
        ''').fetchall()
        
        return jsonify({
            'success': True,
            'report': {
                'total_changed': audit_stats['total_changed'],
                'unique_media': audit_stats['unique_media'],
                'avg_confidence': round(audit_stats['avg_confidence'], 2) if audit_stats['avg_confidence'] else 0,
                'changes_by_category': [dict(cat) for cat in changes_by_category],
                'recent_changes': [dict(change) for change in recent_changes]
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter relatório de reclassificação: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/maintenance/enrich-tmdb', methods=['POST'])
def enrich_tmdb():
    """Enrich all Movies and Adult films with TMDB data (runs in background)."""
    try:
        import threading
        import time
        from app.app import create_app

        def enrich_thread():
            try:
                app_context = create_app().app_context()
                app_context.push()

                from app.database import DATABASE_PATH
                from app.services.tmdb import get_movie_info
                import sqlite3

                # Create separate connection with WAL mode for background thread
                db = sqlite3.connect(DATABASE_PATH, timeout=30.0)
                db.row_factory = sqlite3.Row
                db.execute('PRAGMA journal_mode=WAL')
                db.execute('PRAGMA busy_timeout=30000')

                # Get all Movies and Adult films without tmdb_id
                movies = db.execute('''
                    SELECT id, nome_da_midia, categoria
                    FROM midias
                    WHERE status = 1 AND black_list = 0 AND (categoria = 'Movie' OR categoria = 'Adult') AND tmdb_id IS NULL
                ''').fetchall()

                enriched_count = 0
                blacklist_count = 0
                category_change_count = 0
                total_movies = len(movies)

                for i, item in enumerate(movies):
                    try:
                        tmdb_info = get_movie_info(item['nome_da_midia'], categoria=item['categoria'])
                        categoria = item['categoria']

                        if tmdb_info and tmdb_info.get('tmdb_id'):
                            # Update with TMDB info
                            db.execute('''
                                UPDATE midias SET tmdb_id = ?, imagem_url = ?, ultima_atualizacao = CURRENT_TIMESTAMP
                                WHERE id = ?
                            ''', (tmdb_info['tmdb_id'], tmdb_info.get('poster'), item['id']))
                            enriched_count += 1

                            # Check if category needs to be changed based on TMDB
                            if categoria == 'Adult' and not tmdb_info.get('adult', False):
                                # TMDB says it's not adult, change to Movie
                                db.execute('UPDATE midias SET categoria = ? WHERE id = ?', ('Movie', item['id']))
                                category_change_count += 1
                            elif categoria == 'Movie' and tmdb_info.get('adult', False):
                                # TMDB says it's adult, change to Adult
                                db.execute('UPDATE midias SET categoria = ? WHERE id = ?', ('Adult', item['id']))
                                category_change_count += 1
                        elif categoria == 'Adult':
                            # Adult film not recognized by TMDB - blacklist it
                            db.execute('UPDATE midias SET black_list = 1 WHERE id = ?', (item['id'],))
                            blacklist_count += 1

                        # Commit after EACH item to avoid database lock
                        db.commit()

                        if i % 10 == 0:
                            logger.info(f"Progresso TMDB: {i+1}/{total_movies} ({enriched_count} enriquecidos, {blacklist_count} blacklistados, {category_change_count} categorias mudadas)")
                            time.sleep(0.5)  # Rate limiting

                    except Exception as e:
                        logger.error(f"Erro ao enriquecer {item['nome_da_midia']}: {e}")

                # Final commit and close
                db.commit()
                db.close()
                app_context.pop()

                logger.info(f"Enriquecimento TMDB concluído: {enriched_count} enriquecidos, {blacklist_count} blacklistados, {category_change_count} categorias mudadas")

            except Exception as e:
                logger.error(f"Erro no thread de enriquecimento TMDB: {str(e)}")

        # Start background thread
        thread = threading.Thread(target=enrich_thread)
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'message': 'Enriquecimento TMDB iniciado em background. Verifique os logs para progresso.'
        })
    except Exception as e:
        logger.error(f"Erro ao iniciar enriquecimento TMDB: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/maintenance/reset-exported', methods=['POST'])
def reset_exported():
    """Reset exported media table to force re-export."""
    try:
        from app.database import get_db

        db = get_db()

        # Clear exported_media table
        db.execute('DELETE FROM exported_media')
        db.commit()

        logger.info("Tabela exported_media limpa")
        return jsonify({
            'success': True,
            'message': 'Tabela de exportados limpa com sucesso. Pronto para reexportar.'
        })
    except Exception as e:
        logger.error(f"Erro ao limpar tabela exported_media: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/maintenance/fix-duplicates', methods=['POST'])
def fix_duplicates():
    """Fix duplicates by quality (blacklist lower quality versions)."""
    try:
        from app.database import get_db
        from app.services.parser import remove_quality_from_name
        import hashlib

        db = get_db()

        # Get all active media
        items = db.execute('''
            SELECT id, categoria, nome_normalizado, ano, hash_midia, nome_da_midia, qualidade
            FROM midias
            WHERE status = 1 AND black_list = 0
        ''').fetchall()

        def get_quality_score(qualidade, nome):
            """Retorna o score de qualidade."""
            quality_order = {
                '[L]': 10,
                '4K HDR': 9.5,
                '4K': 9,
                'FHD HDR': 8.5,
                'FHD': 8,
                'HD HDR': 7.5,
                'HD': 7,
                'SD': 6,
                '[DV]': 5.5,
                '[DVD]': 5.5,
                '': 5,
            }

            if qualidade:
                if '[L]' in qualidade:
                    return quality_order['[L]']
                for q, score in quality_order.items():
                    if q and q in qualidade.upper():
                        return score

            if nome:
                nome_upper = nome.upper()
                if '[L]' in nome_upper:
                    return quality_order['[L]']
                if '4K' in nome_upper and 'HDR' in nome_upper:
                    return quality_order['4K HDR']
                if '4K' in nome_upper:
                    return quality_order['4K']
                if 'FHD' in nome_upper and 'HDR' in nome_upper:
                    return quality_order['FHD HDR']
                if 'FHD' in nome_upper:
                    return quality_order['FHD']
                if 'HD' in nome_upper and 'HDR' in nome_upper:
                    return quality_order['HD HDR']
                if 'HD' in nome_upper:
                    return quality_order['HD']
                if 'SD' in nome_upper:
                    return quality_order['SD']
                if '[DV]' in nome_upper or '[DVD]' in nome_upper:
                    return quality_order['[DV]']

            return quality_order['']

        # Calculate new hash for each item
        hash_groups = {}
        for item in items:
            media_id, categoria, nome_normalizado, ano, old_hash, nome_da_midia, qualidade = item

            # Calculate new hash without quality
            nome_sem_qualidade = remove_quality_from_name(nome_normalizado)
            hash_input = f"{categoria}|{nome_sem_qualidade}|{ano or ''}"
            new_hash = hashlib.sha256(hash_input.encode()).hexdigest()

            quality_score = get_quality_score(qualidade, nome_da_midia)

            if new_hash not in hash_groups:
                hash_groups[new_hash] = []

            hash_groups[new_hash].append({
                'id': media_id,
                'quality_score': quality_score,
                'nome': nome_da_midia
            })

        # Process each group
        total_to_blacklist = 0
        total_kept = 0
        ids_to_blacklist = []

        for new_hash, group in hash_groups.items():
            if len(group) > 1:
                # Sort by quality score (descending)
                group.sort(key=lambda x: x['quality_score'], reverse=True)

                # Keep only the best
                best = group[0]
                others = group[1:]

                total_kept += 1

                for item in others:
                    ids_to_blacklist.append(item['id'])
                    total_to_blacklist += 1

        # Mark duplicates as blacklist
        for media_id in ids_to_blacklist:
            db.execute('UPDATE midias SET black_list = 1 WHERE id = ?', (media_id,))

        db.commit()

        logger.info(f"Duplicados corrigidos: {total_to_blacklist} marcados como blacklist, {total_kept} mantidos")
        return jsonify({
            'success': True,
            'message': f'Correção concluída: {total_to_blacklist} itens marcados como blacklist, {total_kept} mantidos'
        })
    except Exception as e:
        logger.error(f"Erro ao corrigir duplicados: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/maintenance/clean-gallery', methods=['POST'])
def clean_gallery():
    """Clean gallery by marking media for re-export."""
    try:
        from app.database import get_db

        db = get_db()

        # Clear exported_media table to force re-export of all media
        db.execute('DELETE FROM exported_media')
        
        # Count how many media items will be re-exported
        count = db.execute("SELECT COUNT(*) as count FROM midias WHERE status = 1 AND black_list = 0").fetchone()['count']

        db.commit()

        logger.info(f"Galeria limpa para re-exportação: {count} mídias marcadas")

        return jsonify({
            'success': True,
            'message': f'Galeria limpa: {count} mídias marcadas para re-exportação. Os arquivos .strm serão regerados na próxima exportação.'
        })
    except Exception as e:
        logger.error(f"Erro ao limpar galeria: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/maintenance/clean-gallery-duplicates', methods=['POST'])
def clean_gallery_duplicates():
    """Clean duplicate .strm files from gallery using database."""
    try:
        from app.database import get_db

        db = get_db()

        # Get all exported files from database
        exported = db.execute('SELECT arquivo, hash_arquivo FROM exported_media').fetchall()

        # Find duplicates by hash
        hash_groups = {}
        for item in exported:
            arquivo = item['arquivo']
            hash_arquivo = item['hash_arquivo']
            if hash_arquivo not in hash_groups:
                hash_groups[hash_arquivo] = []
            hash_groups[hash_arquivo].append(arquivo)

        # Remove duplicates (keep first occurrence)
        removed_count = 0
        for hash_arquivo, files in hash_groups.items():
            if len(files) > 1:
                # Keep first, remove rest
                for dup_file in files[1:]:
                    try:
                        from pathlib import Path
                        dup_path = Path(dup_file)
                        if dup_path.exists():
                            dup_path.unlink()
                            # Remove from database
                            db.execute('DELETE FROM exported_media WHERE arquivo = ?', (dup_file,))
                            removed_count += 1
                            logger.info(f"Removido duplicado: {dup_file}")
                    except Exception as e:
                        logger.error(f"Erro ao remover {dup_file}: {e}")

        db.commit()
        logger.info(f"Duplicados da galeria removidos: {removed_count} arquivos")
        return jsonify({
            'success': True,
            'message': f'Duplicados removidos: {removed_count} arquivos .strm'
        })
    except Exception as e:
        logger.error(f"Erro ao limpar duplicados da galeria: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/maintenance/clean-url-duplicates', methods=['POST'])
def clean_url_duplicates():
    """Clean media items with duplicate URLs from database."""
    try:
        from app.database import get_db

        db = get_db()

        # Find all URLs that appear more than once
        duplicate_urls = db.execute('''
            SELECT url, COUNT(*) as cnt
            FROM midias
            WHERE status = 1
            GROUP BY url
            HAVING cnt > 1
        ''').fetchall()

        total_removed = 0

        for url_info in duplicate_urls:
            url = url_info['url']
            # Get all items with this URL
            items = db.execute('''
                SELECT id FROM midias WHERE url = ? AND status = 1
            ''', (url,)).fetchall()

            # Keep the first one, remove the rest
            for item in items[1:]:
                db.execute('UPDATE midias SET status = 0 WHERE id = ?', (item['id'],))
                total_removed += 1

        db.commit()

        logger.info(f"Duplicados de URL removidos: {total_removed} itens")
        return jsonify({
            'success': True,
            'message': f'Duplicados removidos: {total_removed} itens'
        })
    except Exception as e:
        logger.error(f"Erro ao limpar duplicados de URL: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/maintenance/download-epg', methods=['POST'])
def download_epg():
    """Download and process EPG from IPTV sources."""
    try:
        from app.database import get_db
        from app.services.epg import download_epg, save_epg
        from app.services.config import get_galeria_path
        from pathlib import Path

        db = get_db()

        # Get all active IPTV sources with EPG URLs
        iptv_sources = db.execute('''
            SELECT nome, url_epg FROM iptvs WHERE ativo = 1 AND url_epg IS NOT NULL AND url_epg != ''
        ''').fetchall()

        if not iptv_sources:
            return jsonify({'success': False, 'error': 'Nenhuma fonte IPTV com URL EPG encontrada'})

        # Download EPG from first source (or merge all)
        epg_xml = None
        for iptv in iptv_sources:
            epg_xml = download_epg(iptv['url_epg'])
            if epg_xml:
                break

        if not epg_xml:
            return jsonify({'success': False, 'error': 'Falha ao baixar EPG de todas as fontes'})

        # Save EPG to gallery
        galeria_path = Path(get_galeria_path())
        epg_path = galeria_path / 'epg.xml'

        if save_epg(epg_xml, str(epg_path)):
            logger.info(f"EPG baixado e salvo em: {epg_path}")
            return jsonify({
                'success': True,
                'message': f'EPG baixado e salvo em: {epg_path}'
            })
        else:
            return jsonify({'success': False, 'error': 'Falha ao salvar EPG'})

    except Exception as e:
        logger.error(f"Erro ao baixar EPG: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/maintenance/clean-blacklist', methods=['POST'])
def clean_blacklist():
    """Clean .strm files from gallery for blacklisted items."""
    try:
        from app.services.maintenance import MaintenanceService

        service = MaintenanceService()
        result = service.clean_blacklist_from_gallery()

        logger.info(f"Limpeza de blacklist concluída: {result['deleted_files']} arquivos deletados")

        return jsonify({
            'success': True,
            'message': f'Limpeza concluída: {result["deleted_files"]} arquivos .strm deletados, {result["errors"]} erros',
            'stats': result
        })
    except Exception as e:
        logger.error(f"Erro ao limpar blacklist da galeria: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/maintenance/fix-duplicate-quality', methods=['POST'])
def fix_duplicate_quality():
    """Detect duplicates and mark worst quality as blacklist."""
    try:
        from app.services.maintenance import MaintenanceService

        service = MaintenanceService()
        result = service.fix_duplicate_quality()

        logger.info(f"Correção de duplicatas concluída: {result['blacklisted']} itens marcados como blacklist")

        return jsonify({
            'success': True,
            'message': f'Correção concluída: {result["blacklisted"]} itens marcados como blacklist, {result["hashes_updated"]} hashes atualizados',
            'stats': result
        })
    except Exception as e:
        logger.error(f"Erro ao corrigir duplicatas por qualidade: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/maintenance/clean-exact-duplicates', methods=['POST'])
def clean_exact_duplicates():
    """Remove exact duplicate names from database."""
    try:
        from app.services.maintenance import MaintenanceService

        service = MaintenanceService()
        result = service.clean_exact_duplicates()

        logger.info(f"Limpeza de duplicatas idênticas concluída: {result['records_removed']} registros removidos")

        return jsonify({
            'success': True,
            'message': f'Limpeza concluída: {result["records_removed"]} registros duplicados removidos',
            'stats': result
        })
    except Exception as e:
        logger.error(f"Erro ao limpar duplicatas idênticas: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})




@bp.route('/maintenance/blacklist-duplicates-lowest-quality', methods=['POST'])
def blacklist_duplicates_lowest_quality():
    """Identifica duplicatas por nome sem qualidade/ano e marca as de maior qualidade como blacklist.
    Mantém a MENOR qualidade (prioridade: [L] > SD > HD > FHD > 4K > HDR).
    """
    try:
        from app.services.maintenance import MaintenanceService

        service = MaintenanceService()
        result = service.blacklist_duplicates_keep_lowest_quality()

        logger.info(f"Blacklist de duplicatas (menor qualidade) concluído: {result['total_blacklisted']} itens marcados")

        return jsonify({
            'success': True,
            'message': result['message'],
            'stats': result
        })
    except Exception as e:
        logger.error(f"Erro ao fazer blacklist de duplicatas (menor qualidade): {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/maintenance/remove-years', methods=['POST'])
def remove_years():
    """Remove years from media names and blacklist duplicates."""
    try:
        import re
        from app.database import get_db

        db = get_db()

        # Get all media items
        all_media = db.execute('SELECT id, nome_da_midia FROM midias WHERE status = 1').fetchall()

        updated_count = 0
        blacklisted_count = 0
        skipped_count = 0

        # Pattern to match years (1950-2030) in any position with optional brackets
        year_pattern = re.compile(r'[\(\[\{]?(19[5-9]\d|20[0-3]\d)[\)\]\}]?')

        for media in all_media:
            original_name = media['nome_da_midia']
            media_id = media['id']

            # Remove years from the name
            new_name = year_pattern.sub('', original_name).strip()

            # Clean up multiple spaces that might result from year removal
            new_name = re.sub(r'\s+', ' ', new_name).strip()

            # Check if name actually changed
            if new_name == original_name:
                skipped_count += 1
                continue

            # Check if there's already a media with the same new name
            duplicate = db.execute(
                'SELECT id FROM midias WHERE nome_da_midia = ? AND id != ? AND status = 1',
                (new_name, media_id)
            ).fetchone()

            if duplicate:
                # Mark current media as blacklist since there's a duplicate
                db.execute('UPDATE midias SET black_list = 1 WHERE id = ?', (media_id,))
                blacklisted_count += 1
                logger.info(f"Marcado como blacklist (duplicado): {original_name} -> {new_name}")
            else:
                # Update the name
                db.execute('UPDATE midias SET nome_da_midia = ? WHERE id = ?', (new_name, media_id))
                updated_count += 1
                logger.info(f"Nome atualizado: {original_name} -> {new_name}")

        db.commit()

        logger.info(f"Remoção de anos concluída: {updated_count} atualizados, {blacklisted_count} blacklist, {skipped_count} pulados")

        return jsonify({
            'success': True,
            'updated': updated_count,
            'blacklisted': blacklisted_count,
            'skipped': skipped_count,
            'message': f'Processo concluído: {updated_count} nomes atualizados, {blacklisted_count} marcados como blacklist, {skipped_count} sem alteração'
        })
    except Exception as e:
        logger.error(f"Erro ao remover anos: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics."""
    try:
        from app.database.queries import get_dashboard_stats
        stats = get_dashboard_stats()
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas do dashboard: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/dashboard/category', methods=['POST'])
def get_category_items():
    """Get media items by category."""
    try:
        from app.database.queries import get_media_by_category
        data = request.get_json()
        category = data.get('category')
        black_list = data.get('black_list')
        exported = data.get('exported')
        tmdb_cache = data.get('tmdb_cache')
        limit = data.get('limit', 100)

        # Require at least one filter
        if not category and exported is None and tmdb_cache is None:
            return jsonify({'success': False, 'error': 'Categoria ou filtro não fornecido'})

        items = get_media_by_category(category, black_list, limit, exported, tmdb_cache)

        # Convert to list of dicts
        items_list = [dict(item) for item in items]

        return jsonify({
            'success': True,
            'items': items_list,
            'count': len(items_list)
        })
    except Exception as e:
        logger.error(f"Erro ao obter itens da categoria: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})



@bp.route('/settings/tmdb', methods=['GET'])
def get_tmdb_settings():
    """Get current TMDB settings."""
    try:
        from app.database import get_db

        db = get_db()

        tmdb_api_key = db.execute("""
            SELECT valor FROM system_settings WHERE chave = 'tmdb_api_key'
        """).fetchone()

        tmdb_cache_duration = db.execute("""
            SELECT valor FROM system_settings WHERE chave = 'tmdb_cache_duration'
        """).fetchone()

        return jsonify({
            'success': True,
            'tmdb_api_key': tmdb_api_key['valor'] if tmdb_api_key else '',
            'tmdb_cache_duration': int(tmdb_cache_duration['valor']) if tmdb_cache_duration else 2592000
        })
    except Exception as e:
        logger.error(f"Erro ao obter configurações TMDB: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/settings/tmdb', methods=['POST'])
def save_tmdb_settings():
    """Save TMDB settings."""
    try:
        from app.database import get_db

        data = request.get_json()
        tmdb_api_key = data.get('tmdb_api_key', '')
        tmdb_cache_duration = data.get('tmdb_cache_duration', 2592000)

        db = get_db()

        # Save TMDB API Key
        db.execute("""
            INSERT OR REPLACE INTO system_settings (chave, valor, ultima_atualizacao)
            VALUES ('tmdb_api_key', ?, CURRENT_TIMESTAMP)
        """, (tmdb_api_key,))

        # Save TMDB Cache Duration
        db.execute("""
            INSERT OR REPLACE INTO system_settings (chave, valor, ultima_atualizacao)
            VALUES ('tmdb_cache_duration', ?, CURRENT_TIMESTAMP)
        """, (str(tmdb_cache_duration),))

        db.commit()

        logger.info("Configurações TMDB salvas com sucesso")

        return jsonify({
            'success': True,
            'message': 'Configurações TMDB salvas com sucesso'
        })
    except Exception as e:
        logger.error(f"Erro ao salvar configurações TMDB: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/settings/test-tmdb', methods=['POST'])
def test_tmdb_key():
    """Test if TMDB API key is valid."""
    try:
        from app.services.tmdb import get_movie_info

        data = request.get_json()
        tmdb_api_key = data.get('tmdb_api_key', '')

        if not tmdb_api_key:
            return jsonify({
                'success': False,
                'error': 'API Key não fornecida'
            })

        # Test with a simple search
        result = get_movie_info('Matrix', categoria='Movie')

        if result and result.get('tmdb_id'):
            return jsonify({
                'success': True,
                'message': 'API Key válida'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'API Key inválida ou sem acesso à API'
            })

    except Exception as e:
        logger.error(f"Erro ao testar API key TMDB: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro ao testar API key: {str(e)}'
        })


@bp.route('/settings/database', methods=['GET'])
def get_db_settings():
    """Get current database settings."""
    try:
        from app.database import get_db

        db = get_db()

        db_timeout = db.execute("""
            SELECT valor FROM system_settings WHERE chave = 'db_timeout'
        """).fetchone()

        return jsonify({
            'success': True,
            'db_timeout': int(db_timeout['valor']) if db_timeout else 120
        })
    except Exception as e:
        logger.error(f"Erro ao obter configurações DB: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/settings/database', methods=['POST'])
def save_db_settings():
    """Save database settings."""
    try:
        from app.database import get_db

        data = request.get_json()
        db_timeout = data.get('db_timeout', 120)

        db = get_db()

        db.execute("""
            INSERT OR REPLACE INTO system_settings (chave, valor, ultima_atualizacao)
            VALUES ('db_timeout', ?, CURRENT_TIMESTAMP)
        """, (str(db_timeout),))

        db.commit()

        logger.info(f"Configurações DB salvas com sucesso (timeout: {db_timeout}s)")

        return jsonify({
            'success': True,
            'message': 'Configurações Database salvas com sucesso'
        })
    except Exception as e:
        logger.error(f"Erro ao salvar configurações DB: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/settings/path', methods=['GET'])
def get_path_settings():
    """Get current path settings."""
    try:
        from app.database import get_db

        db = get_db()

        galeria_path = db.execute("""
            SELECT valor FROM system_settings WHERE chave = 'galeria_path'
        """).fetchone()

        return jsonify({
            'success': True,
            'galeria_path': galeria_path['valor'] if galeria_path else ''
        })
    except Exception as e:
        logger.error(f"Erro ao obter configurações de caminho: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/settings/path', methods=['POST'])
def save_path_settings():
    """Save path settings."""
    try:
        from app.database import get_db

        data = request.get_json()
        galeria_path = data.get('galeria_path', '')

        if not galeria_path:
            return jsonify({
                'success': False,
                'error': 'Caminho da galeria não fornecido'
            })

        db = get_db()

        db.execute("""
            INSERT OR REPLACE INTO system_settings (chave, valor, ultima_atualizacao)
            VALUES ('galeria_path', ?, CURRENT_TIMESTAMP)
        """, (galeria_path,))

        db.commit()

        logger.info(f"Configurações de caminho salvas com sucesso (galeria: {galeria_path})")

        return jsonify({
            'success': True,
            'message': 'Configurações de caminho salvas com sucesso'
        })
    except Exception as e:
        logger.error(f"Erro ao salvar configurações de caminho: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/settings/test-path', methods=['POST'])
def test_path():
    """Test if path is valid and accessible."""
    try:
        from pathlib import Path

        data = request.get_json()
        galeria_path = data.get('galeria_path', '')

        if not galeria_path:
            return jsonify({
                'success': False,
                'error': 'Caminho não fornecido'
            })

        path = Path(galeria_path)

        # Check if path exists and is accessible
        if path.exists():
            if path.is_dir():
                # Try to create a test file
                test_file = path / '.test_write'
                try:
                    test_file.touch()
                    test_file.unlink()
                    return jsonify({
                        'success': True,
                        'message': 'Caminho válido e com permissão de escrita'
                    })
                except Exception as e:
                    return jsonify({
                        'success': False,
                        'error': f'Caminho válido mas sem permissão de escrita: {str(e)}'
                    })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Caminho existe mas não é um diretório'
                })
        else:
            return jsonify({
                'success': False,
                'error': 'Caminho não existe'
            })

    except Exception as e:
        logger.error(f"Erro ao testar caminho: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro ao testar caminho: {str(e)}'
        })



@bp.route('/enrich/check-missing-years', methods=['GET'])
def check_missing_years():
    """Check for movies without year."""
    try:
        from app.database import get_db

        db = get_db()

        # Get total movies (Movie category)
        total_movies = db.execute(
            "SELECT COUNT(*) as count FROM midias WHERE categoria = 'Movie' AND status = 1 AND black_list = 0"
        ).fetchone()['count']

        # Get movies with year
        with_years = db.execute(
            "SELECT COUNT(*) as count FROM midias WHERE categoria = 'Movie' AND status = 1 AND black_list = 0 AND ano IS NOT NULL AND ano != ''"
        ).fetchone()['count']

        # Get movies without year
        missing_years = total_movies - with_years

        # Get examples of movies without year (up to 5)
        examples = []
        if missing_years > 0:
            examples_rows = db.execute("""
                SELECT id, nome_da_midia
                FROM midias
                WHERE categoria = 'Movie' AND status = 1 AND black_list = 0 AND (ano IS NULL OR ano = '')
                LIMIT 5
            """).fetchall()
            examples = [dict(row) for row in examples_rows]

        return jsonify({
            'success': True,
            'stats': {
                'total_movies': total_movies,
                'with_years': with_years,
                'missing_years': missing_years
            },
            'examples': examples
        })
    except Exception as e:
        logger.error(f"Erro ao verificar anos faltantes: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/enrich/years-from-tmdb-all', methods=['POST'])
def enrich_years_from_tmdb_all():
    """Enrich all movies without year from TMDB."""
    try:
        from app.database import get_db
        from app.services.tmdb import get_movie_info
        import time

        db = get_db()

        # Get all movies without year
        movies = db.execute("""
            SELECT id, nome_da_midia
            FROM midias
            WHERE categoria = 'Movie' AND status = 1 AND black_list = 0 AND (ano IS NULL OR ano = '')
        """).fetchall()

        total_processed = len(movies)
        updated = 0
        not_found = 0
        errors = 0
        start_time = time.time()

        for movie in movies:
            try:
                movie_info = get_movie_info(movie['nome_da_midia'])
                if movie_info and movie_info.get('tmdb_id'):
                    # Update year if found
                    year = movie_info.get('release_date', '')[:4] if movie_info.get('release_date') else None
                    if year and year.isdigit():
                        db.execute(
                            "UPDATE midias SET ano = ? WHERE id = ?",
                            (int(year), movie['id'])
                        )
                        updated += 1
                else:
                    not_found += 1
            except Exception as e:
                logger.error(f"Erro ao enriquecer filme {movie['nome_da_midia']}: {str(e)}")
                errors += 1

        db.commit()
        duration = int(time.time() - start_time)

        logger.info(f"Enriquecimento TMDB concluído: {updated}/{total_processed} atualizados")

        return jsonify({
            'success': True,
            'message': f'Enriquecimento TMDB concluído',
            'stats': {
                'total_processed': total_processed,
                'updated': updated,
                'not_found': not_found,
                'errors': errors,
                'duration': duration
            }
        })
    except Exception as e:
        logger.error(f"Erro ao enriquecer filmes com TMDB: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/enrich/tmdb-progress', methods=['GET'])
def get_tmdb_progress():
    """Get TMDB enrichment progress."""
    return jsonify({
        'success': True,
        'status': 'completed',  # For now, always return completed since we use synchronous processing
        'progress': 100,
        'message': 'Enriquecimento concluído'
    })



@bp.route('/maintenance/generate-tv-m3u', methods=['POST'])
def generate_tv_m3u():
    """Generate TV M3U + EPG package from database."""
    try:
        from app.database import get_db
        from app.services.tv_m3u_generator import generate_jellyfin_package
        from pathlib import Path

        db = get_db()
        data = request.get_json() or {}
        output_dir_name = data.get('output_dir', 'app/data')

        # Generate TV M3U + EPG package
        output_path = Path(output_dir_name)
        result = generate_jellyfin_package(db, output_path)

        if result.get('success'):
            logger.info(f"Pacote Jellyfin gerado: M3U={result.get('m3u_path')}, EPG={result.get('epg_path')}")

            return jsonify({
                'success': True,
                'message': f'Pacote Jellyfin gerado com sucesso: tv.m3u e epg.xml',
                'stats': {
                    'total_channels': result.get('total_channels', 0),
                    'm3u_path': result.get('m3u_path'),
                    'epg_path': result.get('epg_path'),
                    'm3u_success': result.get('m3u_success', False),
                    'epg_success': result.get('epg_success', False)
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Erro desconhecido')
            })

    except Exception as e:
        logger.error(f"Erro ao gerar pacote Jellyfin: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


# TMDB Validation Endpoints

@bp.route('/validation/validate-short-names', methods=['POST'])
def validate_short_names():
    """Validate Movie items with ≤2 words using TMDB."""
    try:
        from app.database import get_db
        from app.services.tmdb_validator import TMDBValidatorService
        from datetime import datetime

        db = get_db()

        # Update process status
        db.execute('''
            INSERT INTO process_status (etapa, progresso, mensagem, status)
            VALUES ('TMDB Validation', 0, 'Iniciando validação de nomes curtos...', 'running')
        ''')
        db.commit()

        logger.info("Iniciando validação TMDB de nomes curtos")

        # Create validator service
        validator = TMDBValidatorService()

        # Run validation
        result = validator.validate_short_names()

        # Update process status
        db.execute('''
            UPDATE process_status
            SET progresso = 100, mensagem = ?, status = 'completed'
            WHERE status = 'running'
        ''', (f'Validação concluída: {result["validated"]} validados, {result["not_found"]} não encontrados, {result["deduplicated"]} duplicatas removidas',))
        db.commit()

        logger.info(f"Validação TMDB concluída: {result}")

        return jsonify({
            'success': True,
            'message': f'Validação concluída: {result["validated"]} validados, {result["not_found"]} não encontrados, {result["deduplicated"]} duplicatas removidas',
            'stats': result
        })

    except Exception as e:
        logger.error(f"Erro na validação TMDB: {str(e)}")
        # Update process status on error
        try:
            db = get_db()
            db.execute('''
                UPDATE process_status
                SET status = 'failed', mensagem = ?
                WHERE status = 'running'
            ''', (f'Erro: {str(e)}',))
            db.commit()
        except:
            pass
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/validation/progress', methods=['GET'])
def get_validation_progress():
    """Get current TMDB validation progress."""
    try:
        from app.database import get_db

        db = get_db()
        status = db.execute('''
            SELECT progresso, mensagem, status FROM process_status
            WHERE status = 'running' OR etapa = 'TMDB Validation'
            ORDER BY id DESC LIMIT 1
        ''').fetchone()

        if status:
            return jsonify({
                'success': True,
                'progress': status['progresso'],
                'message': status['mensagem'],
                'status': status['status']
            })
        else:
            return jsonify({
                'success': True,
                'progress': 100,
                'message': 'Nenhuma validação em andamento',
                'status': 'completed'
            })

    except Exception as e:
        logger.error(f"Erro ao obter progresso da validação: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/validation/blacklist-unvalidated', methods=['POST'])
def blacklist_unvalidated():
    """Send non-validated Movie items to blacklist."""
    try:
        from app.database import get_db
        from app.services.tmdb_validator import TMDBValidatorService

        db = get_db()
        validator = TMDBValidatorService()

        result = validator.blacklist_unvalidated()

        logger.info(f"Blacklist de não validados: {result}")

        return jsonify({
            'success': True,
            'message': f'{result["blacklisted"]} itens enviados para blacklist',
            'blacklisted': result['blacklisted']
        })

    except Exception as e:
        logger.error(f"Erro ao enviar não validados para blacklist: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/validation/stats', methods=['GET'])
def get_validation_stats():
    """Get TMDB validation statistics."""
    try:
        from app.database import get_db
        from app.services.tmdb_validator import TMDBValidatorService

        db = get_db()
        validator = TMDBValidatorService()

        stats = validator.get_validation_stats()

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        logger.error(f"Erro ao obter estatísticas de validação: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})
