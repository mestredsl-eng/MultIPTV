"""Service for enriching TV channel logos from external sources."""

import logging
import re

logger = logging.getLogger('process')


# Manual mapping for common Brazilian channels
BRAZILIAN_CHANNEL_LOGOS = {
    # Globo
    'globo': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/TV_Globo_2014_logo.svg/200px-TV_Globo_2014_logo.svg.png',
    'globo brasil': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/TV_Globo_2014_logo.svg/200px-TV_Globo_2014_logo.svg.png',
    'globo sp': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/TV_Globo_2014_logo.svg/200px-TV_Globo_2014_logo.svg.png',
    'globo brasilia': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/TV_Globo_2014_logo.svg/200px-TV_Globo_2014_logo.svg.png',
    
    # Record
    'record': 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/ee/RecordTV_logo_2020.svg/200px-RecordTV_logo_2020.svg.png',
    'recordtv': 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/ee/RecordTV_logo_2020.svg/200px-RecordTV_logo_2020.svg.png',
    
    # SBT
    'sbt': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/fa/SBT_logo_2016.svg/200px-SBT_logo_2016.svg.png',
    
    # Band
    'band': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a6/Logo_Band_2011.svg/200px-Logo_Band_2011.svg.png',
    'band sp': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a6/Logo_Band_2011.svg/200px-Logo_Band_2011.svg.png',
    'band news': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a6/Logo_Band_2011.svg/200px-Logo_Band_2011.svg.png',
    'band sports': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a6/Logo_Band_2011.svg/200px-Logo_Band_2011.svg.png',
    
    # RedeTV
    'redetv': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/66/RedeTV_2020.svg/200px-RedeTV_2020.svg.png',
    'redetv!': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/66/RedeTV_2020.svg/200px-RedeTV_2020.svg.png',
    
    # Cultura
    'cultura': 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e3/TV_Cultura_logo.svg/200px-TV_Cultura_logo.svg.png',
    'tv cultura': 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e3/TV_Cultura_logo.svg/200px-TV_Cultura_logo.svg.png',
    
    # TV Brasil
    'tv brasil': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/TV_Brasil_logo_2015.svg/200px-TV_Brasil_logo_2015.svg.png',
    
    # Canais Globo
    'gloob': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/69/Gloob_logo.svg/200px-Gloob_logo.svg.png',
    'gloobinho': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a0/Gloobinho_logo.svg/200px-Gloobinho_logo.svg.png',
    'gnt': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/GNT_logo.svg/200px-GNT_logo.svg.png',
    'multishow': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0d/Multishow_logo.svg/200px-Multishow_logo.svg.png',
    'megapix': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/8b/Megapix_logo.svg/200px-Megapix_logo.svg.png',
    'premiere': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/Premiere_FC_logo.svg/200px-Premiere_FC_logo.svg.png',
    'spacetv': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/Space_logo.svg/200px-Space_logo.svg.png',
    'canal brasil': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Canal_Brasil_logo.svg/200px-Canal_Brasil_logo.svg.png',
    'canal futurama': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Canal_Brasil_logo.svg/200px-Canal_Brasil_logo.svg.png',
    
    # Canais Globosat
    'combate': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Combate_logo.svg/200px-Combate_logo.svg.png',
    'bis': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2d/BIS_logo.svg/200px-BIS_logo.svg.png',
    'cartoon network': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Cartoon_Network_logo_2010.svg/200px-Cartoon_Network_logo_2010.svg.png',
    
    # Canais Discovery
    'discovery': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/66/Discovery_Channel_logo.svg/200px-Discovery_Channel_logo.svg.png',
    'discovery channel': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/66/Discovery_Channel_logo.svg/200px-Discovery_Channel_logo.svg.png',
    'discovery science': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/66/Discovery_Channel_logo.svg/200px-Discovery_Channel_logo.svg.png',
    'discovery turbo': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/66/Discovery_Channel_logo.svg/200px-Discovery_Channel_logo.svg.png',
    'discovery theater': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/66/Discovery_Channel_logo.svg/200px-Discovery_Channel_logo.svg.png',
    'discovery home': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/66/Discovery_Channel_logo.svg/200px-Discovery_Channel_logo.svg.png',
    'discovery kids': 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e2/Discovery_Kids_logo_2019.svg/200px-Discovery_Kids_logo_2019.svg.png',
    'animal planet': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/Animal_Planet_logo_2018.svg/200px-Animal_Planet_logo_2018.svg.png',
    
    # Canais HBO
    'hbo': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6f/HBO_logo.svg/200px-HBO_logo.svg.png',
    'hbo 2': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6f/HBO_logo.svg/200px-HBO_logo.svg.png',
    'hbo family': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6f/HBO_logo.svg/200px-HBO_logo.svg.png',
    'hbo plus': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6f/HBO_logo.svg/200px-HBO_logo.svg.png',
    'hbo signature': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6f/HBO_logo.svg/200px-HBO_logo.svg.png',
    
    # Canais ESPN
    'espn': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/ESPN_logo.svg/200px-ESPN_logo.svg.png',
    'espn 2': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/ESPN_logo.svg/200px-ESPN_logo.svg.png',
    'espn 3': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/ESPN_logo.svg/200px-ESPN_logo.svg.png',
    'espn 4': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/ESPN_logo.svg/200px-ESPN_logo.svg.png',
    
    # Canais Fox/Disney
    'fx': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/FX_2019_logo.svg/200px-FX_2019_logo.svg.png',
    'fox sports': 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/Fox_Sports_logo.svg/200px-Fox_Sports_logo.svg.png',
    'fox sports 2': 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/Fox_Sports_logo.svg/200px-Fox_Sports_logo.svg.png',
    
    # Canais Sony
    'sony': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Sony_Channel_logo.svg/200px-Sony_Channel_logo.svg.png',
    'axn': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4f/AXN_2018_logo.svg/200px-AXN_2018_logo.svg.png',
    
    # Canais Paramount
    'comedy central': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Comedy_Central_logo_2018.svg/200px-Comedy_Central_logo_2018.svg.png',
    'paramount': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/Paramount_Network_logo.svg/200px-Paramount_Network_logo.svg.png',
    
    # Canais Warner
    'warner': 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/Warner_Channel_logo.svg/200px-Warner_Channel_logo.svg.png',
    'tnt': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/TNT_2016_logo.svg/200px-TNT_2016_logo.svg.png',
    'space': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/Space_logo.svg/200px-Space_logo.svg.png',
    
    # Canais BBC
    'bbc': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/BBC_News_2019.svg/200px-BBC_News_2019.svg.png',
    'bbc news': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/BBC_News_2019.svg/200px-BBC_News_2019.svg.png',
    
    # Canais CNN
    'cnn': 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/b1/CNN.svg/200px-CNN.svg.png',
    'cnn brasil': 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/b1/CNN.svg/200px-CNN.svg.png',
    
    # Canais de esportes
    'sportv': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/SporTV_logo_2021.svg/200px-SporTV_logo_2021.svg.png',
    'esporte interativo': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/SporTV_logo_2021.svg/200px-SporTV_logo_2021.svg.png',
    
    # Canais infantes
    'nick': 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e3/Nickelodeon_logo.svg/200px-Nickelodeon_logo.svg.png',
    'nickelodeon': 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e3/Nickelodeon_logo.svg/200px-Nickelodeon_logo.svg.png',
    'cartoon': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Cartoon_Network_logo_2010.svg/200px-Cartoon_Network_logo_2010.svg.png',
    
    # Canais variedades
    'e!': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2d/E!_2019_logo.svg/200px-E!_2019_logo.svg.png',
    'history': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/History_Channel_logo.svg/200px-History_Channel_logo.svg.png',
    'h2': 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/H2_logo.svg/200px-H2_logo.svg.png',
    'national geographic': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Natgeo_logo.svg/200px-Natgeo_logo.svg.png',
    'nat geo': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Natgeo_logo.svg/200px-Natgeo_logo.svg.png',
    
    # Canais de filmes
    'telecine': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/62/Telecine_2021_logo.svg/200px-Telecine_2021_logo.svg.png',
    'telecine premium': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/62/Telecine_2021_logo.svg/200px-Telecine_2021_logo.svg.png',
    'telecine action': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/62/Telecine_2021_logo.svg/200px-Telecine_2021_logo.svg.png',
    'telecine touch': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/62/Telecine_2021_logo.svg/200px-Telecine_2021_logo.svg.png',
    'telecine fun': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/62/Telecine_2021_logo.svg/200px-Telecine_2021_logo.svg.png',
    'telecine pipoca': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/62/Telecine_2021_logo.svg/200px-Telecine_2021_logo.svg.png',
    'hbo signature': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6f/HBO_logo.svg/200px-HBO_logo.svg.png',
    'cinecanal': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6f/HBO_logo.svg/200px-HBO_logo.svg.png',
    'cinemax': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/aa/Cinemax_logo.svg/200px-Cinemax_logo.svg.png',
}


def normalize_channel_name(name):
    """Normalize channel name for logo matching."""
    # Remove special characters, convert to lowercase
    name = re.sub(r'[^\w\s]', '', name.lower())
    name = re.sub(r'\s+', ' ', name.strip())
    return name


def get_logo_from_mapping(channel_name):
    """Get logo URL from manual mapping."""
    normalized = normalize_channel_name(channel_name)
    
    # Direct match
    if normalized in BRAZILIAN_CHANNEL_LOGOS:
        return BRAZILIAN_CHANNEL_LOGOS[normalized]
    
    # Partial match
    for key, logo_url in BRAZILIAN_CHANNEL_LOGOS.items():
        if key in normalized or normalized in key:
            return logo_url
    
    return None


def enrich_channel_logos(db):
    """Enrich logos for TV channels that don't have them."""
    
    channels = db.execute('''
        SELECT id, nome_canal, logo_url 
        FROM tv_channels 
        WHERE status = 1 AND black_list = 0 
        AND (logo_url IS NULL OR logo_url = '')
        ORDER BY nome_canal
    ''').fetchall()
    
    total_channels = len(channels)
    logger.info(f"Enriching logos for {total_channels} channels")
    
    updated_count = 0
    
    for channel in channels:
        channel_id = channel['id']
        channel_name = channel['nome_canal']
        logo_url = channel['logo_url'] if 'logo_url' in channel.keys() else ''
        
        if logo_url:
            continue  # Skip if already has logo
        
        # Try to get logo from mapping
        new_logo_url = get_logo_from_mapping(channel_name)
        
        if new_logo_url:
            db.execute('UPDATE tv_channels SET logo_url = ? WHERE id = ?', (new_logo_url, channel_id))
            db.commit()
            updated_count += 1
            logger.info(f"Updated logo for {channel_name}: {new_logo_url}")
        else:
            logger.debug(f"No logo found for {channel_name}")
    
    logger.info(f"Logo enrichment complete: {updated_count}/{total_channels} channels updated")
    
    return {
        'total_channels': total_channels,
        'updated_count': updated_count,
        'success': True
    }