"""M3U downloader service - Adapted from original iptv_manager."""

import requests
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timedelta
from app.services.config import get_m3u_refresh_interval

logger = logging.getLogger('process')


def get_cache_path(url, cache_dir):
    """Gera um caminho de cache único para a URL"""
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    url_hash = hashlib.md5(url.encode()).hexdigest()
    return cache_dir / f"{url_hash}.m3u"


def should_download(cache_path):
    """Verifica se o arquivo deve ser baixado novamente (mais de 6h)"""
    if not cache_path.exists():
        return True
    
    file_mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
    time_diff = datetime.now() - file_mtime
    
    return time_diff.total_seconds() > get_m3u_refresh_interval()


def download_m3u(url, cache_dir):
    """Baixa um arquivo M3U da URL"""
    cache_path = get_cache_path(url, cache_dir)
    
    if not should_download(cache_path):
        logger.info(f"Usando cache para {url}")
        return str(cache_path)
    
    logger.info(f"Baixando {url}...")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive'
        }
        response = requests.get(url, timeout=30, headers=headers)
        response.raise_for_status()
        
        cache_path.write_text(response.text, encoding='utf-8')
        logger.info(f"Download concluído: {cache_path}")
        return str(cache_path)
    except requests.RequestException as e:
        logger.error(f"Erro ao baixar {url}: {e}")
        if cache_path.exists():
            logger.warning(f"Usando cache existente")
            return str(cache_path)
        raise


def download_all_m3u(iptv_sources, cache_dir):
    """Baixa todos os M3Us das fontes IPTV cadastradas"""
    if not iptv_sources:
        return []
    
    logger.info(f"Baixando {len(iptv_sources)} M3Us...")
    
    # Baixar sequencialmente (adaptado do original)
    downloaded_files = []
    for idx, source in enumerate(iptv_sources, 1):
        logger.info(f"  Download {idx}/{len(iptv_sources)}: {source['nome']}")
        try:
            cache_file = download_m3u(source['url_m3u'], cache_dir)
            downloaded_files.append({
                'iptv_id': source['id'],
                'nome': source['nome'],
                'cache_file': cache_file
            })
        except Exception as e:
            logger.error(f"  Erro ao baixar {source['nome']}: {e}")
    
    logger.info(f"  Downloads concluídos: {len(downloaded_files)}/{len(iptv_sources)}")
    return downloaded_files


def cleanup_cache(cache_dir, max_age_hours=24):
    """Limpa arquivos de cache antigos"""
    cache_dir = Path(cache_dir)
    
    if not cache_dir.exists():
        return
    
    max_age = timedelta(hours=max_age_hours)
    now = datetime.now()
    cleaned_count = 0
    
    for cache_file in cache_dir.glob('*.m3u'):
        file_mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        age = now - file_mtime
        
        if age > max_age:
            try:
                cache_file.unlink()
                cleaned_count += 1
                logger.info(f"Removido cache antigo: {cache_file.name}")
            except Exception as e:
                logger.error(f"Erro ao remover {cache_file}: {e}")
    
    if cleaned_count > 0:
        logger.info(f"Limpeza de cache concluída: {cleaned_count} arquivos removidos")
    else:
        logger.info("Nenhum arquivo de cache antigo encontrado")
