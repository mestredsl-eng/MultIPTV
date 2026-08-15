"""STRM export service with incremental tracking and duplicate prevention."""

import hashlib
import re
import logging
from pathlib import Path
from app.database import get_db
from app.database.retry_helper import safe_execute, safe_commit, DatabaseLockError
from app.services.config import get_galeria_path
from app.services.parser import remove_quality_indicators, count_words

logger = logging.getLogger('process')


def sanitize_filename(name):
    """
    Sanitize filename to remove invalid characters, quality indicators and adult content markers for Windows.
    
    Now uses the canonical remove_quality_indicators() function for consistency with hash calculation.
    """
    if not name:
        return 'unnamed'

    # Use the canonical quality removal function for consistency
    name = remove_quality_indicators(name)

    # Remove invalid characters: < > : " / \ | ? * [ ]
    name = re.sub(r'[<>:"/\\|?*\[\]]', '', name)
    # Remove ellipsis (...) which can cause issues on Windows
    name = re.sub(r'\.{2,}', '', name)
    # Remove leading/trailing spaces and dots
    name = name.strip('. ')
    # Replace multiple spaces with single space
    name = re.sub(r'\s+', ' ', name)
    
    # Truncate to reasonable length for Windows (max 255 chars for filename, but we use 200 to be safe)
    if len(name) > 200:
        name = name[:200]
    
    return name or 'unnamed'


def calculate_file_hash(arquivo):
    """Calculate SHA256 hash of file content."""
    if not Path(arquivo).exists():
        return None
    sha256_hash = hashlib.sha256()
    with open(arquivo, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def acquire_export_lock(db):
    """Acquire export lock to prevent concurrent exports."""
    try:
        lock = safe_execute(db, 'SELECT * FROM export_lock WHERE id = 1').fetchone()

        if lock['locked']:
            # Check if lock is stale (older than 1 hour or heartbeat expired)
            if lock['locked_since']:
                from datetime import datetime
                try:
                    lock_age = datetime.now() - datetime.fromisoformat(lock['locked_since'])
                    if lock_age.total_seconds() > 3600:
                        # Release stale lock
                        safe_execute(db, 'UPDATE export_lock SET locked = 0, locked_since = NULL, ultimo_heartbeat = NULL WHERE id = 1')
                        safe_commit(db)
                        logger.info("Export lock stale liberado")
                    else:
                        # Check heartbeat (if heartbeat is older than 2 minutes, consider stale)
                        if lock['ultimo_heartbeat']:
                            heartbeat_age = datetime.now() - datetime.fromisoformat(lock['ultimo_heartbeat'])
                            if heartbeat_age.total_seconds() > 120:
                                # Heartbeat expired, release lock
                                safe_execute(db, 'UPDATE export_lock SET locked = 0, locked_since = NULL, ultimo_heartbeat = NULL WHERE id = 1')
                                safe_commit(db)
                                logger.info("Export lock heartbeat expirado liberado")
                            else:
                                raise Exception("Export already in progress (heartbeat active)")
                        else:
                            raise Exception("Export already in progress")
                except Exception as e:
                    logger.warning(f"Erro ao verificar lock age: {e}")
                    raise Exception("Export already in progress")
            else:
                raise Exception("Export already in progress")

        # Acquire lock
        safe_execute(db, '''
            UPDATE export_lock
            SET locked = 1, locked_since = CURRENT_TIMESTAMP, locked_by = 'web', ultimo_heartbeat = CURRENT_TIMESTAMP
            WHERE id = 1
        ''')
        safe_commit(db)
    except DatabaseLockError as e:
        logger.error(f"Database locked ao adquirir export lock: {e}")
        raise
    except Exception as e:
        logger.error(f"Erro ao adquirir export lock: {e}")
        raise


def generate_tv_m3u_and_epg(db):
    """Generate TV M3U and EPG from TV channels, updating tv_channels table."""
    try:
        from pathlib import Path
        from app.services.tv_m3u_generator import generate_tv_m3u, generate_epg_xmltv
        from app.services.config import get_galeria_path
        import requests

        galeria_path = Path(get_galeria_path())
        tv_dir = galeria_path / 'TV'
        tv_dir.mkdir(parents=True, exist_ok=True)

        # Get all TV media items - ONLY with black_list = 0
        tv_items = safe_execute(db, '''
            SELECT id, iptv_id, nome_da_midia, nome_normalizado, url, imagem_url, 
                   hash_midia, qualidade, black_list, status
            FROM midias 
            WHERE categoria = 'TV' AND black_list = 0 AND status = 1
        ''').fetchall()

        if not tv_items:
            logger.info("Nenhum canal TV encontrado para exportar")
            return

        logger.info(f"Processando {len(tv_items)} canais TV (apenas non-blacklist)...")

        # Update tv_channels table from TV media items
        for item in tv_items:
            nome_canal = item['nome_da_midia']
            hash_canal = item['hash_midia']

            # Generate tvg_id if not available (use normalized name)
            tvg_id = nome_canal.lower().replace(' ', '-').replace(':', '')

            # Check if channel already exists
            existing = safe_execute(db, '''
                SELECT id FROM tv_channels WHERE hash_canal = ?
            ''', (hash_canal,)).fetchone()

            if existing:
                # Update existing channel - preserve blacklist status from midias table
                safe_execute(db, '''
                    UPDATE tv_channels
                    SET nome_normalizado = ?, url = ?, logo_url = ?,
                        qualidade = ?, tvg_id = ?, black_list = ?, ultima_atualizacao = CURRENT_TIMESTAMP
                    WHERE hash_canal = ?
                ''', (item['nome_normalizado'], item['url'], item['imagem_url'],
                     item['qualidade'], tvg_id, item['black_list'], hash_canal))
            else:
                # Insert new channel - use blacklist status from midias table
                safe_execute(db, '''
                    INSERT INTO tv_channels
                    (iptv_id, nome_canal, nome_normalizado, url, logo_url, categoria,
                     qualidade, hash_canal, tvg_id, black_list, status)
                    VALUES (?, ?, ?, ?, ?, 'TV', ?, ?, ?, ?, 1)
                ''', (item['iptv_id'], nome_canal, item['nome_normalizado'],
                     item['url'], item['imagem_url'], item['qualidade'],
                     hash_canal, tvg_id, item['black_list']))

        # Remove channels from tv_channels that are blacklisted in midias
        safe_execute(db, '''
            UPDATE tv_channels
            SET black_list = 1, status = 0
            WHERE hash_canal IN (
                SELECT hash_midia FROM midias WHERE categoria = 'TV' AND black_list = 1
            )
        ''')

        db.commit()
        logger.info(f"tv_channels atualizado com {len(tv_items)} canais ativos")

        # Get EPG URLs from active IPTV sources
        epg_urls = safe_execute(db, '''
            SELECT url_epg FROM iptvs WHERE ativo = 1 AND url_epg IS NOT NULL AND url_epg != ''
        ''').fetchall()
        epg_url_list = [epg['url_epg'] for epg in epg_urls]

        # Generate TV M3U
        tv_m3u_path = tv_dir / 'tv.m3u'
        m3u_result = generate_tv_m3u(db, tv_m3u_path)
        
        if m3u_result['success']:
            logger.info(f"tv.m3u gerado: {m3u_result['total_channels']} canais")
        
        # Generate EPG
        epg_path = tv_dir / 'epg.xml'
        epg_result = generate_epg_xmltv(db, epg_path, epg_url_list)
        
        if epg_result['success']:
            logger.info(f"epg.xml gerado")
        else:
            logger.warning(f"EPG não gerado (continuando): {epg_result.get('error')}")

        logger.info("TV M3U e EPG gerados com sucesso")

    except Exception as e:
        logger.error(f"Erro ao gerar TV M3U e EPG: {str(e)}")
        raise


def release_export_lock(db):
    """Release export lock."""
    try:
        safe_execute(db, 'UPDATE export_lock SET locked = 0, locked_since = NULL, locked_by = NULL WHERE id = 1')
        safe_commit(db)
        logger.info("Export lock liberado")
    except DatabaseLockError as e:
        logger.error(f"Database locked ao liberar export lock: {e}")
        raise
    except Exception as e:
        logger.error(f"Erro ao liberar export lock: {e}")
        raise


def update_heartbeat(db):
    """Update heartbeat for export lock."""
    try:
        safe_execute(db, 'UPDATE export_lock SET ultimo_heartbeat = CURRENT_TIMESTAMP WHERE id = 1')
        safe_commit(db)
    except DatabaseLockError as e:
        logger.warning(f"Database locked ao atualizar heartbeat: {e}")
        # Não falhar se heartbeat falhar
    except Exception as e:
        logger.warning(f"Erro ao atualizar heartbeat: {e}")
        # Não falhar se heartbeat falhar


def generate_file_path(media_item):
    """Generate file path for STRM file based on category with standardized folder names."""
    import re
    galeria_path = Path(get_galeria_path())
    categoria = media_item['categoria'] if 'categoria' in media_item.keys() else 'Movie'
    nome = sanitize_filename(media_item['nome_da_midia'] if 'nome_da_midia' in media_item.keys() else '')

    ano = media_item['ano'] if 'ano' in media_item.keys() else ''

    # For series-like categories, remove SXXEXX from folder name FIRST
    series_categories = ['Series', 'Novela', 'Cartoon', 'Documentary', 'Educational']
    no_year_categories = ['Series', 'Novela', 'Cartoon', 'Documentary', 'Educational', 'Sports']
    if categoria in series_categories:
        # Remove SXXEXX pattern from folder name
        nome_pasta = re.sub(r'\s*S\d+E\d+.*$', '', nome, flags=re.IGNORECASE).strip()
        # Also remove year from folder name for series-like categories
        nome_pasta = re.sub(r'\s*\(\d{4}\)\s*$', '', nome_pasta).strip()
    else:
        nome_pasta = nome

    # Truncate very long folder names to avoid path length issues (max 100 chars for folder name)
    if len(nome_pasta) > 100:
        nome_pasta = nome_pasta[:100]

    # Truncate file name if too long (max 150 chars for full filename including extension)
    nome_arquivo = nome
    # Remove year from filename for categories that should not have year
    if categoria in no_year_categories:
        nome_arquivo = re.sub(r'\s*\(\d{4}\)\s*$', '', nome_arquivo).strip()
    if len(nome_arquivo) > 150:
        nome_arquivo = nome_arquivo[:150]

    # Standardized folder names as per plan
    if categoria == 'Movie':
        folder = galeria_path / 'FILMES'
        if ano:
            # Check if year is already in the filename to avoid duplication
            year_pattern = re.compile(r'\(\d{4}\)')
            if year_pattern.search(nome_arquivo):
                # Year already present, use as-is
                folder = folder / nome_arquivo
                arquivo = folder / f"{nome_arquivo}.strm"
            else:
                folder = folder / f"{nome_arquivo} ({ano})"
                # Incluir ano também no nome do arquivo para facilitar identificação no Jellyfin
                arquivo = folder / f"{nome_arquivo} ({ano}).strm"
        else:
            folder = folder / nome_arquivo
            arquivo = folder / f"{nome_arquivo}.strm"
    elif categoria == 'Series':
        folder = galeria_path / 'SERIES' / nome_pasta
        season = media_item['season'] if 'season' in media_item.keys() and media_item['season'] is not None else 1
        folder = folder / f"Season {season:02d}"
        episode = media_item['episode'] if 'episode' in media_item.keys() and media_item['episode'] is not None else 1
        arquivo = folder / f"{nome_pasta} S{season:02d}E{episode:02d}.strm"
    elif categoria == 'Novela':
        folder = galeria_path / 'NOVELAS' / nome_pasta
        season = media_item['season'] if 'season' in media_item.keys() and media_item['season'] is not None else 1
        folder = folder / f"Season {season:02d}"
        episode = media_item['episode'] if 'episode' in media_item.keys() and media_item['episode'] is not None else 1
        arquivo = folder / f"{nome_pasta} S{season:02d}E{episode:02d}.strm"
    elif categoria == 'Cartoon':
        folder = galeria_path / 'DESENHOS' / nome_pasta
        season = media_item['season'] if 'season' in media_item.keys() and media_item['season'] is not None else 1
        folder = folder / f"Season {season:02d}"
        episode = media_item['episode'] if 'episode' in media_item.keys() and media_item['episode'] is not None else 1
        arquivo = folder / f"{nome_pasta} S{season:02d}E{episode:02d}.strm"
    elif categoria == 'Documentary':
        folder = galeria_path / 'DOCUMENTARIOS' / nome_pasta
        season = media_item['season'] if 'season' in media_item.keys() and media_item['season'] is not None else 1
        folder = folder / f"Season {season:02d}"
        episode = media_item['episode'] if 'episode' in media_item.keys() and media_item['episode'] is not None else 1
        arquivo = folder / f"{nome_pasta} S{season:02d}E{episode:02d}.strm"
    elif categoria == 'Educational':
        folder = galeria_path / 'EDUCACIONAL' / nome_pasta
        season = media_item['season'] if 'season' in media_item.keys() and media_item['season'] is not None else 1
        folder = folder / f"Season {season:02d}"
        episode = media_item['episode'] if 'episode' in media_item.keys() and media_item['episode'] is not None else 1
        arquivo = folder / f"{nome_pasta} S{season:02d}E{episode:02d}.strm"
    elif categoria == 'Adult':
        folder = galeria_path / 'FILMES_XXX'
        if ano:
            # Check if year is already in the filename to avoid duplication
            year_pattern = re.compile(r'\(\d{4}\)')
            if year_pattern.search(nome_arquivo):
                # Year already present, use as-is
                folder = folder / nome_arquivo
                arquivo = folder / f"{nome_arquivo}.strm"
            else:
                folder = folder / f"{nome_arquivo} ({ano})"
                # Incluir ano também no nome do arquivo para facilitar identificação
                arquivo = folder / f"{nome_arquivo} ({ano}).strm"
        else:
            folder = folder / nome_arquivo
            arquivo = folder / f"{nome_arquivo}.strm"
    elif categoria == 'Sports':
        folder = galeria_path / 'ESPORTES' / nome_arquivo
        arquivo = folder / f"{nome_arquivo}.strm"
    elif categoria == 'TV':
        arquivo = galeria_path / 'TV' / 'tv.m3u'
    else:
        arquivo = galeria_path / categoria / f"{nome}.strm"

    return str(arquivo)


def validate_export_permission(media_item, db):
    """
    Validate if media item can be exported based on TMDB validation rules.
    
    Rules:
    - Movies with ≤2 words in name require TMDB validation (year field must be set)
    - Other categories are not affected by this rule
    - If validation fails, export is blocked but item remains active
    
    Args:
        media_item: Dictionary containing media item data
        db: Database connection
        
    Returns:
        tuple: (can_export: bool, reason: str)
    """
    categoria = media_item.get('categoria')
    nome_da_midia = media_item.get('nome_da_midia', '')
    ano = media_item.get('ano')
    
    # Only apply validation rule to Movie category
    if categoria != 'Movie':
        return True, "Category not affected by validation rule"
    
    # Count words in the name
    word_count = count_words(nome_da_midia)
    
    # Check if needs validation (≤2 words)
    if word_count <= 2:
        if ano is None:
            reason = f"Export blocked: '{nome_da_midia}' has {word_count} word(s) and no TMDB year. Requires TMDB validation."
            logger.warning(reason)
            return False, reason
        else:
            logger.info(f"Export allowed: '{nome_da_midia}' has {word_count} word(s) but TMDB year ({ano}) is set.")
            return True, "TMDB validation satisfied"
    
    # More than 2 words, no validation required
    return True, "Name has >2 words, validation not required"


def export_media(media_item, db):
    """Export single media item with duplicate prevention and blacklist safety check."""
    try:
        hash_midia = media_item['hash_midia'] if 'hash_midia' in media_item.keys() else None

        # SAFETY CHECK #1: Verify current database status
        # This catches items that were blacklisted AFTER the initial query
        current_status = safe_execute(db, '''
            SELECT black_list, status FROM midias WHERE hash_midia = ?
        ''', (hash_midia,)).fetchone()

        if current_status and (current_status[0] == 1 or current_status[1] == 0):
            logger.warning(f"SKIPPING EXPORT: Item is blacklisted or inactive: {media_item.get('nome_da_midia', 'unknown')} (hash: {hash_midia})")
            # Remove from exported_media if present (cleanup)
            safe_execute(db, '''
                DELETE FROM exported_media WHERE hash_midia = ?
            ''', (hash_midia,))
            safe_commit(db)
            return

        # SAFETY CHECK #2: Validate export permission based on TMDB validation rules
        can_export, validation_reason = validate_export_permission(media_item, db)
        if not can_export:
            logger.warning(f"SKIPPING EXPORT: {validation_reason}")
            # Remove from exported_media if present (cleanup)
            safe_execute(db, '''
                DELETE FROM exported_media WHERE hash_midia = ?
            ''', (hash_midia,))
            safe_commit(db)
            return

        arquivo = generate_file_path(media_item)

        # Check if this media was previously exported to a different path
        exported = safe_execute(db, '''
            SELECT * FROM exported_media WHERE hash_midia = ?
        ''', (hash_midia,)).fetchone()

        # If previously exported to a different path, delete old file
        if exported and exported['arquivo'] != arquivo:
            old_file = Path(exported['arquivo'])
            if old_file.exists():
                try:
                    old_file.unlink()
                    logger.info(f"Arquivo antigo removido: {old_file}")
                    # Try to remove empty parent directories
                    try:
                        old_file.parent.rmdir()
                    except:
                        pass
                except Exception as e:
                    logger.warning(f"Erro ao remover arquivo antigo {old_file}: {e}")

        # Export (create STRM file) - always overwrite if exists
        try:
            # Create parent directories with error handling
            parent_dir = Path(arquivo).parent
            parent_dir.mkdir(parents=True, exist_ok=True)
            
            # Write the STRM file
            url = media_item['url'] if 'url' in media_item.keys() else ''
            with open(arquivo, 'w', encoding='utf-8') as f:
                f.write(url)
                
        except FileNotFoundError as e:
            logger.error(f"Erro ao criar diretório ou arquivo (caminho não encontrado): {arquivo} - {e}")
            raise
        except OSError as e:
            # Handle Windows-specific path length errors
            if "path too long" in str(e).lower() or len(str(arquivo)) > 260:
                logger.error(f"Erro: caminho muito longo para Windows: {arquivo} (length: {len(str(arquivo))})")
                # Try to use shortened path
                try:
                    import os
                    short_path = os.path.abspath(arquivo)
                    if len(short_path) > 260:
                        # Use extended-length path syntax for Windows
                        short_path = "\\\\?\\" + os.path.abspath(arquivo)
                    parent_dir = Path(short_path).parent
                    parent_dir.mkdir(parents=True, exist_ok=True)
                    url = media_item['url'] if 'url' in media_item.keys() else ''
                    with open(short_path, 'w', encoding='utf-8') as f:
                        f.write(url)
                    arquivo = short_path
                    logger.info(f"Usando caminho estendido do Windows: {short_path}")
                except Exception as e2:
                    logger.error(f"Erro ao usar caminho estendido: {e2}")
                    raise e
            else:
                logger.error(f"Erro de OS ao exportar: {e}")
                raise

        # Calculate hash of exported file
        file_hash = calculate_file_hash(arquivo)

        # Register export with hash
        safe_execute(db, '''
            INSERT OR REPLACE INTO exported_media
            (hash_midia, arquivo, ultima_exportacao, hash_arquivo)
            VALUES (?, ?, CURRENT_TIMESTAMP, ?)
        ''', (hash_midia, arquivo, file_hash))
        safe_commit(db)

    except DatabaseLockError as e:
        logger.error(f"Database locked ao exportar mídia {media_item['nome_da_midia'] if 'nome_da_midia' in media_item.keys() else 'unknown'}: {e}")
        raise
    except Exception as e:
        logger.error(f"Erro ao exportar mídia {media_item['nome_da_midia'] if 'nome_da_midia' in media_item.keys() else 'unknown'}: {e}")
        raise


def export_all_media(media_items, db):
    """Export all media items with lock protection, heartbeat, and BLACKLIST FILTERING."""
    try:
        acquire_export_lock(db)

        # CRITICAL FIX: Filter out blacklist items BEFORE processing
        # This prevents items that were blacklisted after the initial query from being exported
        filtered_items = []
        skipped_blacklist = 0
        
        for item in media_items:
            # Get fresh status from database
            item_dict = dict(item) if hasattr(item, 'keys') else item
            hash_midia = item_dict.get('hash_midia')
            
            if hash_midia:
                current_status = safe_execute(db, '''
                    SELECT black_list, status FROM midias WHERE hash_midia = ?
                ''', (hash_midia,)).fetchone()
                
                # Only include if NOT blacklisted and ACTIVE
                if current_status and current_status[0] == 0 and current_status[1] == 1:
                    filtered_items.append(item_dict)
                else:
                    skipped_blacklist += 1
                    logger.info(f"Filtered out blacklist item before export: {item_dict.get('nome_da_midia', 'unknown')}")
            else:
                filtered_items.append(item_dict)
        
        logger.info(f"Export: {len(filtered_items)} items to export, {skipped_blacklist} skipped (blacklist)")

        total = len(filtered_items)
        exported_count = 0
        tv_items_count = 0
        
        for i, item in enumerate(filtered_items):
            try:
                export_media(item, db)
                exported_count += 1
                # Count TV items
                if item.get('categoria') == 'TV':
                    tv_items_count += 1
            except Exception as e:
                logger.error(f"Erro ao exportar {item.get('nome_da_midia', 'unknown')}: {e}")
                continue

            # Update progress every 100 items
            if (i + 1) % 100 == 0:
                try:
                    progress = int((i + 1) / total * 100) if total > 0 else 0
                    safe_execute(db, '''
                        UPDATE process_status
                        SET progresso = ?, mensagem = ?
                        WHERE status = 'running'
                    ''', (progress, f'Exportando {i + 1}/{total} itens...'))
                    safe_commit(db)
                except DatabaseLockError:
                    logger.warning("Database locked ao atualizar progresso, continuando...")
                except Exception as e:
                    logger.warning(f"Erro ao atualizar progresso: {e}")

            # Update heartbeat every 30 seconds
            update_heartbeat(db)

        logger.info(f"Exportação concluída: {exported_count}/{total} itens exportados")
        
        # Generate TV M3U and EPG after regular export
        if tv_items_count > 0:
            logger.info("Gerando TV M3U e EPG...")
            generate_tv_m3u_and_epg(db)
        
        return exported_count

    finally:
        release_export_lock(db)
