"""Configuration service for system settings."""

from app.database import get_db


def get_setting(chave, default=None):
    """Get a setting from system_settings table."""
    db = get_db()
    result = db.execute('SELECT valor FROM system_settings WHERE chave = ?', (chave,)).fetchone()
    if result:
        return result['valor']
    return default


def set_setting(chave, valor, descricao=None):
    """Set a setting in system_settings table."""
    db = get_db()
    if descricao:
        db.execute('''
            INSERT OR REPLACE INTO system_settings (chave, valor, descricao, ultima_atualizacao)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (chave, valor, descricao))
    else:
        db.execute('''
            INSERT OR REPLACE INTO system_settings (chave, valor, ultima_atualizacao)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (chave, valor))
    db.commit()


def get_tmdb_api_key():
    """Get TMDB API key from settings."""
    return get_setting('tmdb_api_key')


def set_tmdb_api_key(api_key):
    """Set TMDB API key in settings."""
    set_setting('tmdb_api_key', api_key, 'TMDB API Key para enriquecimento de mídias')


def get_galeria_path():
    """Get gallery path from settings."""
    return get_setting('galeria_path', 'D:/Galeria')


def set_galeria_path(path):
    """Set gallery path in settings."""
    set_setting('galeria_path', path, 'Caminho da galeria de mídias')


def get_m3u_refresh_interval():
    """Get M3U refresh interval in seconds from settings."""
    return int(get_setting('tempo_refresh_m3u', '21600'))


def set_m3u_refresh_interval(seconds):
    """Set M3U refresh interval in settings."""
    set_setting('tempo_refresh_m3u', str(seconds), 'Tempo de refresh do M3U em segundos (6 horas)')


def get_tmdb_cache_duration():
    """Get TMDB cache duration in seconds from settings."""
    return int(get_setting('tempo_cache_tmdb', '2592000'))


def set_tmdb_cache_duration(seconds):
    """Set TMDB cache duration in settings."""
    set_setting('tempo_cache_tmdb', str(seconds), 'Tempo de cache do TMDB em segundos (30 dias)')


def get_ultima_execucao():
    """Get last execution timestamp from settings."""
    return get_setting('ultima_execucao')


def set_ultima_execucao(timestamp):
    """Set last execution timestamp in settings."""
    set_setting('ultima_execucao', timestamp, 'Timestamp da última execução completa')


def get_all_settings():
    """Get all system settings."""
    db = get_db()
    return db.execute('SELECT * FROM system_settings ORDER BY chave').fetchall()
