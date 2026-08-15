"""Database query functions for common operations."""

from app.database import get_db


def get_all_iptvs():
    """Get all IPTV sources with media counts and formatted dates."""
    db = get_db()
    iptvs = db.execute('SELECT * FROM iptvs ORDER BY nome').fetchall()
    
    result = []
    for iptv in iptvs:
        iptv_dict = dict(iptv)
        
        # Count media items for this IPTV source
        media_count = db.execute(
            'SELECT COUNT(*) as count FROM midias WHERE iptv_id = ? AND status = 1 AND black_list = 0',
            (iptv['id'],)
        ).fetchone()
        iptv_dict['media_count'] = media_count['count'] if media_count else 0
        
        # Format dates - try ultima_atualizacao first, fallback to data_cadastro
        display_date = None
        
        # Try ultima_atualizacao first
        if iptv_dict.get('ultima_atualizacao'):
            display_date = format_date(iptv_dict['ultima_atualizacao'])
        
        # Fallback to data_cadastro if ultima_atualizacao is None or empty
        if not display_date and iptv_dict.get('data_cadastro'):
            display_date = format_date(iptv_dict['data_cadastro'])
        
        iptv_dict['ultima_atualizacao'] = display_date or '-'
        
        result.append(iptv_dict)
    
    return result


def format_date(date_value):
    """Format date value for display."""
    if not date_value:
        return None
        
    try:
        from datetime import datetime
        if isinstance(date_value, str):
            # Try different date formats
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%S.%f',
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%d',
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(date_value, fmt)
                    return dt.strftime('%d/%m/%Y %H:%M')
                except ValueError:
                    continue
            
            # Try fromisoformat as fallback
            try:
                dt = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                return dt.strftime('%d/%m/%Y %H:%M')
            except:
                pass
                
        elif isinstance(date_value, datetime):
            return date_value.strftime('%d/%m/%Y %H:%M')
            
    except Exception as e:
        pass
        
    return str(date_value) if date_value else None


def get_iptv_by_id(iptv_id):
    """Get IPTV source by ID."""
    db = get_db()
    return db.execute('SELECT * FROM iptvs WHERE id = ?', (iptv_id,)).fetchone()


def create_iptv(nome, url_m3u, url_epg):
    """Create new IPTV source."""
    db = get_db()
    cursor = db.execute(
        'INSERT INTO iptvs (nome, url_m3u, url_epg) VALUES (?, ?, ?)',
        (nome, url_m3u, url_epg)
    )
    db.commit()
    return cursor.lastrowid


def update_iptv(iptv_id, nome, url_m3u, url_epg):
    """Update IPTV source."""
    db = get_db()
    db.execute(
        'UPDATE iptvs SET nome = ?, url_m3u = ?, url_epg = ?, ultima_atualizacao = CURRENT_TIMESTAMP WHERE id = ?',
        (nome, url_m3u, url_epg, iptv_id)
    )
    db.commit()


def delete_iptv(iptv_id):
    """Hard delete IPTV source and associated media (database and gallery files)."""
    from app.services.config import get_galeria_path
    from app.services.exporter import generate_file_path
    from pathlib import Path
    import logging
    
    logger = logging.getLogger('process')
    db = get_db()
    
    # Get all media items from this IPTV before deletion
    media_items = db.execute(
        'SELECT * FROM midias WHERE iptv_id = ?',
        (iptv_id,)
    ).fetchall()
    
    # Remove .strm files from gallery
    galeria_path = Path(get_galeria_path())
    files_removed = 0
    
    for media in media_items:
        # Try to find and remove the .strm file based on media name and category
        try:
            # Create a media item dict for generate_file_path
            media_dict = {
                'categoria': media['categoria'],
                'nome_da_midia': media['nome'],
                'ano': media['ano']
            }
            
            strm_file = generate_file_path(media_dict)
            
            if strm_file.exists():
                strm_file.unlink()
                files_removed += 1
                logger.info(f"Removed gallery file: {strm_file}")
        except Exception as e:
            logger.warning(f"Could not remove gallery file for media {media['nome']}: {e}")
    
    # Get affected media count before deletion
    media_count = db.execute(
        'SELECT COUNT(*) as count FROM midias WHERE iptv_id = ? AND status = 1 AND black_list = 0',
        (iptv_id,)
    ).fetchone()
    
    # Delete associated media items from database
    db.execute('DELETE FROM midias WHERE iptv_id = ?', (iptv_id,))
    
    # Delete the IPTV source from database
    db.execute('DELETE FROM iptvs WHERE id = ?', (iptv_id,))
    
    db.commit()
    
    logger.info(f"Deleted IPTV {iptv_id}: {media_count['count']} media items from DB, {files_removed} files from gallery")
    
    return {
        'media_count': media_count['count'] if media_count else 0,
        'files_removed': files_removed
    }


def get_media_count():
    """Get total media count (excluding blacklist)."""
    db = get_db()
    result = db.execute('SELECT COUNT(*) as count FROM midias WHERE status = 1 AND black_list = 0').fetchone()
    return result['count'] if result else 0


def get_media_count_by_status(status):
    """Get media count by status (excluding blacklist)."""
    db = get_db()
    result = db.execute(
        'SELECT COUNT(*) as count FROM midias WHERE status = ? AND black_list = 0',
        (status,)
    ).fetchone()
    return result['count'] if result else 0


def get_exported_count():
    """Get exported media count from database.
    
    FIXED: Removed duplicate definition (was defined twice).
    Returns count of items in exported_media table.
    """
    db = get_db()
    result = db.execute('SELECT COUNT(*) as count FROM exported_media').fetchone()
    return result['count'] if result else 0


def get_not_exported_count():
    """Get count of media items not yet exported (total - exported, excluding blacklist)."""
    db = get_db()
    # Get total active media (excluding blacklist)
    total = db.execute("SELECT COUNT(*) as count FROM midias WHERE status = 1 AND black_list = 0").fetchone()['count']
    
    # Get exported count
    exported = db.execute(
        'SELECT COUNT(*) as count FROM midias m JOIN exported_media e ON m.hash_midia = e.hash_midia WHERE m.black_list = 0'
    ).fetchone()['count']
    
    return total - exported


def get_media_count_by_category(categoria):
    """Get media count by category (excluding blacklist)."""
    db = get_db()
    result = db.execute(
        'SELECT COUNT(*) as count FROM midias WHERE categoria = ? AND status = 1 AND black_list = 0',
        (categoria,)
    ).fetchone()
    return result['count'] if result else 0


def get_series_unique_count(categoria):
    """Get unique series titles count (excluding blacklist)."""
    import re
    db = get_db()
    # Get all names
    items = db.execute(
        'SELECT nome_da_midia FROM midias WHERE categoria = ? AND status = 1 AND black_list = 0',
        (categoria,)
    ).fetchall()

    unique_series = set()
    for item in items:
        name = item['nome_da_midia']
        # Remove season/episode patterns to get base name
        # Pattern: S01E01, s01e01, Season 1, Session 1, etc.
        base_name = re.sub(r'[Ss]\d+[Ee]\d+.*', '', name)  # S01E01
        base_name = re.sub(r'[Ss]eason\s*\d+.*', '', base_name, flags=re.IGNORECASE)  # Season 1
        base_name = re.sub(r'[Ss]ession\s*\d+.*', '', base_name, flags=re.IGNORECASE)  # Session 1
        base_name = base_name.strip()
        if base_name:  # Only add non-empty names
            unique_series.add(base_name)

    return len(unique_series)


def get_tv_channels_count():
    """Get TV channels count (count media in TV category, excluding blacklist)."""
    db = get_db()
    result = db.execute('SELECT COUNT(*) as count FROM midias WHERE categoria = "TV" AND status = 1 AND black_list = 0').fetchone()
    return result['count'] if result else 0


def get_blacklist_count():
    """Get blacklist count."""
    db = get_db()
    result = db.execute('SELECT COUNT(*) as count FROM midias WHERE black_list = 1 AND status = 1').fetchone()
    return result['count'] if result else 0


def get_duplicate_count():
    """Get duplicate media count by hash_midia (excluding blacklist)."""
    db = get_db()
    result = db.execute('''
        SELECT COUNT(*) as count FROM (
            SELECT hash_midia, COUNT(*) as cnt
            FROM midias
            WHERE status = 1 AND black_list = 0
            GROUP BY hash_midia
            HAVING cnt > 1
        )
    ''').fetchone()
    return result['count'] if result else 0


def get_tmdb_cache_count():
    """Get TMDB cache count."""
    db = get_db()
    result = db.execute('SELECT COUNT(*) as count FROM tmdb_cache').fetchone()
    return result['count'] if result else 0


def get_dashboard_stats():
    """Get all dashboard statistics.
    
    FIXED: Changed 'duplicados' to use get_duplicate_count() instead of get_not_exported_count()
    'duplicados' should show actual duplicates, not non-exported items.
    """
    import re
    db = get_db()

    # Get all series-like categories in one query
    series_categories = ['Series', 'Educational', 'Documentary', 'Cartoon', 'Novela']
    series_items = db.execute('''
        SELECT categoria, nome_da_midia FROM midias
        WHERE categoria IN (?, ?, ?, ?, ?) AND status = 1 AND black_list = 0
    ''', series_categories).fetchall()

    # Calculate unique counts for each category
    unique_counts = {cat: set() for cat in series_categories}
    for item in series_items:
        categoria = item['categoria']
        name = item['nome_da_midia']
        # Remove season/episode patterns
        base_name = re.sub(r'[Ss]\d+[Ee]\d+.*', '', name)
        base_name = re.sub(r'[Ss]eason\s*\d+.*', '', base_name, flags=re.IGNORECASE)
        base_name = re.sub(r'[Ss]ession\s*\d+.*', '', base_name, flags=re.IGNORECASE)
        base_name = base_name.strip()
        if base_name:
            unique_counts[categoria].add(base_name)

    return {
        'iptvs': len(get_all_iptvs()),
        'midias': get_media_count(),
        'filmes': get_media_count_by_category('Movie'),
        'series': get_media_count_by_category('Series'),
        'series_unique': len(unique_counts['Series']),
        'tv': get_media_count_by_category('TV'),
        'tv_channels': get_tv_channels_count(),
        'duplicados': get_duplicate_count(),  # FIXED: was get_not_exported_count()
        'blacklist': get_blacklist_count(),
        'adult': get_media_count_by_category('Adult'),
        'educational': get_media_count_by_category('Educational'),
        'educational_unique': len(unique_counts['Educational']),
        'documentary': get_media_count_by_category('Documentary'),
        'documentary_unique': len(unique_counts['Documentary']),
        'cartoon': get_media_count_by_category('Cartoon'),
        'cartoon_unique': len(unique_counts['Cartoon']),
        'novela': get_media_count_by_category('Novela'),
        'novela_unique': len(unique_counts['Novela']),
        'sports': get_media_count_by_category('Sports'),
        'exportados': get_exported_count(),
        'tmdb_cache': get_tmdb_cache_count(),
        'not_exported': get_not_exported_count(),
    }


def get_last_execution_stats():
    """Get last execution statistics."""
    db = get_db()
    result = db.execute(
        'SELECT * FROM execution_stats WHERE status = "completed" ORDER BY inicio DESC LIMIT 1'
    ).fetchone()
    return dict(result) if result else None


def get_process_status():
    """Get current process status."""
    db = get_db()
    result = db.execute(
        'SELECT * FROM process_status WHERE status = "running" ORDER BY id DESC LIMIT 1'
    ).fetchone()
    return dict(result) if result else None


def get_recent_activity(limit=10):
    """Get recent processing activity."""
    db = get_db()
    return db.execute(
        'SELECT etapa as etapa, inicio as inicio, fim as fim, status as status FROM process_status ORDER BY id DESC LIMIT ?',
        (limit,)
    ).fetchall()


def get_media_by_category(category, black_list=None, limit=100, exported=None, tmdb_cache=None):
    """Get media items by category with optional blacklist, exported, and tmdb_cache filters."""
    db = get_db()
    
    # Build query based on filters - include IPTV name via JOIN
    if category:
        query = 'SELECT m.*, i.nome as iptv_nome FROM midias m LEFT JOIN iptvs i ON m.iptv_id = i.id WHERE m.categoria = ?'
        params = [category]
    elif exported is not None:
        if exported:
            query = 'SELECT m.*, i.nome as iptv_nome FROM midias m LEFT JOIN iptvs i ON m.iptv_id = i.id JOIN exported_media e ON m.hash_midia = e.hash_midia WHERE 1=1'
        else:
            query = 'SELECT m.*, i.nome as iptv_nome FROM midias m LEFT JOIN iptvs i ON m.iptv_id = i.id LEFT JOIN exported_media e ON m.hash_midia = e.hash_midia WHERE e.hash_midia IS NULL'
        params = []
    elif tmdb_cache is not None:
        if tmdb_cache:
            query = 'SELECT m.*, i.nome as iptv_nome FROM midias m LEFT JOIN iptvs i ON m.iptv_id = i.id JOIN tmdb_cache t ON m.hash_midia = t.hash_midia WHERE 1=1'
        else:
            query = 'SELECT m.*, i.nome as iptv_nome FROM midias m LEFT JOIN iptvs i ON m.iptv_id = i.id LEFT JOIN tmdb_cache t ON m.hash_midia = t.hash_midia WHERE t.hash_midia IS NULL'
        params = []
    else:
        # Default: return all items if no specific filter
        query = 'SELECT m.*, i.nome as iptv_nome FROM midias m LEFT JOIN iptvs i ON m.iptv_id = i.id WHERE 1=1'
        params = []

    # Apply blacklist filter
    if black_list is not None:
        query += ' AND m.black_list = ?'
        params.append(black_list)

    # Apply status filter (active items only)
    query += ' AND m.status = 1'

    query += ' ORDER BY m.nome_da_midia'
    
    # Apply limit only if specified
    if limit is not None:
        query += ' LIMIT ?'
        params.append(limit)

    return db.execute(query, params).fetchall()
