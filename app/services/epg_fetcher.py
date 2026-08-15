"""EPG (Electronic Program Guide) fetcher service - Adapted from original iptv_manager."""

import requests
import xml.etree.ElementTree as ET
import logging
from typing import Dict, List, Optional
from pathlib import Path
import hashlib
import gzip

logger = logging.getLogger('process')


def get_epg_cache_path(url: str, cache_dir: Path) -> Path:
    """Gera um caminho de cache único para a URL do EPG"""
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    url_hash = hashlib.md5(url.encode()).hexdigest()
    return cache_dir / f"{url_hash}.xml"


def fetch_epg_from_url(url: str, cache_dir: Path, use_cache: bool = True) -> Optional[str]:
    """
    Baixa um arquivo EPG XMLTV de uma URL
    Suporta arquivos .gz comprimidos
    Se use_cache=True, usa cache se disponível
    """
    cache_path = get_epg_cache_path(url, cache_dir)
    
    # Verificar se o cache existe e é válido (6 horas)
    if use_cache and cache_path.exists():
        from datetime import datetime, timedelta
        file_mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        time_diff = datetime.now() - file_mtime
        if time_diff.total_seconds() < 6 * 3600:  # 6 horas
            logger.info(f"Usando cache EPG: {cache_path.name}")
            return cache_path.read_text(encoding='utf-8')
    
    # Baixar EPG
    try:
        logger.info(f"Baixando EPG de {url}...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=60, headers=headers)
        response.raise_for_status()
        
        # Verificar se é gzip
        content = response.content
        if url.endswith('.gz') or response.headers.get('content-encoding') == 'gzip':
            try:
                content = gzip.decompress(content)
                logger.info("EPG descomprimido (gzip)")
            except Exception as e:
                logger.warning(f"Erro ao descomprimir EPG: {e}, tentando usar conteúdo original")
        
        # Converter para string
        xml_content = content.decode('utf-8', errors='ignore')
        
        # Salvar no cache
        cache_path.write_text(xml_content, encoding='utf-8')
        logger.info(f"EPG salvo no cache: {cache_path}")
        
        return xml_content
    except requests.RequestException as e:
        logger.error(f"Erro ao baixar EPG de {url}: {e}")
        # Tentar usar cache existente mesmo se expirado
        if cache_path.exists():
            logger.warning(f"Usando cache existente (expirado)")
            return cache_path.read_text(encoding='utf-8')
        return None


def parse_xmltv(xml_content: str) -> Dict[str, Dict]:
    """
    Parseia um arquivo XMLTV e retorna um dicionário de canais
    """
    channels = {}
    
    try:
        root = ET.fromstring(xml_content)
        
        # Extrair informações dos canais
        for channel in root.findall('channel'):
            channel_id = channel.get('id')
            display_names = channel.findall('display-name')
            if display_names:
                name = display_names[0].text
                channels[channel_id] = {'name': name, 'programs': []}
        
        # Extrair programação
        for programme in root.findall('programme'):
            channel_id = programme.get('channel')
            if channel_id in channels:
                program = {
                    'start': programme.get('start'),
                    'stop': programme.get('stop'),
                    'title': programme.find('title').text if programme.find('title') is not None else '',
                    'desc': programme.find('desc').text if programme.find('desc') is not None else ''
                }
                channels[channel_id]['programs'].append(program)
    
    except ET.ParseError as e:
        logger.error(f"Erro ao parsear XMLTV: {e}")
    
    logger.info(f"Parseados {len(channels)} canais do XMLTV")
    return channels


def search_epg_for_channel(channel_name: str, epg_sources: List[str], cache_dir: Path) -> Optional[Dict]:
    """
    Busca EPG para um canal específico em várias fontes
    """
    channel_name_lower = channel_name.lower()
    
    for source_url in epg_sources:
        xml_content = fetch_epg_from_url(source_url, cache_dir)
        if xml_content:
            channels = parse_xmltv(xml_content)
            
            for channel_id, channel_data in channels.items():
                if channel_name_lower in channel_data['name'].lower():
                    return {
                        'channel_id': channel_id,
                        'name': channel_data['name'],
                        'programs': channel_data['programs'],
                        'source_url': source_url
                    }
    
    return None


def fetch_epg_for_channels(channel_names: List[str], epg_sources: List[str], cache_dir: Path, max_channels: int = None) -> Dict[str, Dict]:
    """
    Busca EPG para múltiplos canais
    Se max_channels for None, busca todos os canais
    """
    epg_data = {}

    # Limitar o número de canais para verificar (se especificado)
    if max_channels is not None and len(channel_names) > max_channels:
        logger.info(f"Limitando busca de EPG para {max_channels} canais (de {len(channel_names)})")
        channel_names = channel_names[:max_channels]

    total = len(channel_names)
    
    for idx, channel_name in enumerate(channel_names, 1):
        if idx % 20 == 0 or idx == total:
            logger.info(f"Progresso: {idx}/{total} canais verificados para EPG...")
        
        epg_info = search_epg_for_channel(channel_name, epg_sources, cache_dir)
        if epg_info:
            epg_data[channel_name] = epg_info
    
    return epg_data


def download_epg_file(epg_url: str, output_path: Path) -> bool:
    """
    Baixa o arquivo EPG completo e salva no caminho especificado
    Suporta arquivos .gz comprimidos
    Retorna True se sucesso, False caso contrário
    """
    try:
        logger.info(f"Baixando EPG completo de {epg_url}...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(epg_url, timeout=120, headers=headers)
        response.raise_for_status()
        
        # Verificar se é gzip
        content = response.content
        if epg_url.endswith('.gz') or response.headers.get('content-encoding') == 'gzip':
            try:
                content = gzip.decompress(content)
                logger.info("EPG descomprimido (gzip)")
            except Exception as e:
                logger.warning(f"Erro ao descomprimir EPG: {e}, tentando usar conteúdo original")
        
        # Converter para string
        xml_content = content.decode('utf-8', errors='ignore')
        
        # Salvar arquivo
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(xml_content, encoding='utf-8')
        logger.info(f"EPG salvo em: {output_path}")
        
        # Validar XML
        try:
            ET.fromstring(xml_content)
            logger.info("EPG validado: XML válido")
        except ET.ParseError as e:
            logger.warning(f"EPG pode estar corrompido: {e}")
        
        return True
    except requests.RequestException as e:
        logger.error(f"Erro ao baixar EPG completo: {e}")
        return False
