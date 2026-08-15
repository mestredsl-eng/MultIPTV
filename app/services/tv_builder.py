"""TV M3U builder service."""

from app.database import get_db
from app.services.config import get_galeria_path
from pathlib import Path


def build_tv_m3u():
    """Build TV M3U file from tv_channels table."""
    db = get_db()
    
    # Get all active TV channels
    channels = db.execute('''
        SELECT * FROM tv_channels 
        WHERE status = 1 AND black_list = 0
        ORDER BY nome_canal
    ''').fetchall()
    
    galeria_path = Path(get_galeria_path())
    tv_dir = galeria_path / 'TV'
    tv_dir.mkdir(parents=True, exist_ok=True)
    
    m3u_file = tv_dir / 'tv.m3u'
    
    with open(m3u_file, 'w', encoding='utf-8') as f:
        f.write('#EXTM3U\n')
        f.write('#EXTINF:0,Mestre IPTV TV Channels\n\n')
        
        for channel in channels:
            # Build EXTINF line with proper Jellyfin format
            tvg_id = channel['tvg_id'] if 'tvg_id' in channel.keys() and channel['tvg_id'] else channel['nome_canal']
            logo_url = channel['logo_url'] if 'logo_url' in channel.keys() else ''
            categoria = channel['categoria'] if 'categoria' in channel.keys() else 'TV'
            channel_name = channel['nome_canal']
            
            extinf = f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{channel_name}" tvg-logo="{logo_url}" group-title="{categoria}",{channel_name}\n'
            f.write(extinf)
            f.write(f'{channel["url"]}\n\n')
    
    return str(m3u_file)


def get_channel_mapping():
    """Get common Brazilian channel mapping for EPG."""
    mapping = {
        'Globo': 'globo',
        'Record': 'record',
        'SBT': 'sbt',
        'Band': 'band',
        'RedeTV': 'redetv',
        'TV Cultura': 'cultura',
        'TV Brasil': 'tvbrasil',
    }
    return mapping
