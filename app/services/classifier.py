"""Media classification service."""

import re
from app.services.parser import normalize_name


def classify_media(entry):
    """Classify media entry into category."""
    name = entry.get('name', '').lower()
    group_title = entry.get('group_title', '').lower()
    url = entry.get('url', '')

    # Adult content
    if is_adult(name, group_title):
        return 'Adult'

    # TV channels
    if is_tv(name, group_title, url):
        return 'TV'

    # Sports
    if is_sports(name, group_title):
        return 'Sports'

    # Educational
    if is_educational(name, group_title):
        return 'Educational'

    # Documentaries
    if is_documentary(name, group_title):
        return 'Documentary'

    # Cartoons
    if is_cartoon(name, group_title):
        return 'Cartoon'

    # Novelas
    if is_novela(name, group_title):
        return 'Novela'

    # Series (PRIORITY: name pattern first, then group-title)
    # S01E01 pattern is more reliable than group-title (sources often misclassify)
    if is_series(name):
        return 'Series'
    
    # If no S01E01 pattern, check group-title as fallback
    if is_series_by_group_title(group_title):
        return 'Series'

    # Movies (default)
    return 'Movie'


def is_adult(name, group_title):
    """Check if content is adult."""
    adult_keywords = ['xxx', 'porn', 'adult', 'sex', 'hardcore', 'softcore']
    return any(keyword in name or keyword in group_title for keyword in adult_keywords)


def is_tv(name, group_title, url=None):
    """Check if content is TV channel."""
    # TV should only be .ts or live streams, not MP4/MKV files
    if url:
        url_lower = url.lower()
        # If it's a video file (mp4, mkv, avi, etc.), it's not TV
        if any(ext in url_lower for ext in ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm']):
            return False

    tv_keywords = ['channel', 'canal', 'tv', 'live']
    return any(keyword in name or keyword in group_title for keyword in tv_keywords)


def is_sports(name, group_title):
    """Check if content is sports."""
    sports_keywords = ['sport', 'futebol', 'football', 'nba', 'ufc', 'esporte']
    return any(keyword in name or keyword in group_title for keyword in sports_keywords)


def is_educational(name, group_title):
    """Check if content is educational."""
    educational_keywords = ['curso', 'aula', 'educational', 'learning', 'tutorial']
    return any(keyword in name or keyword in group_title for keyword in educational_keywords)


def is_documentary(name, group_title):
    """Check if content is documentary."""
    documentary_keywords = ['documentary', 'documentário', 'doc']
    return any(keyword in name or keyword in group_title for keyword in documentary_keywords)


def is_cartoon(name, group_title):
    """Check if content is cartoon/anime."""
    cartoon_keywords = ['cartoon', 'anime', 'desenho', 'animation']
    return any(keyword in name or keyword in group_title for keyword in cartoon_keywords)


def is_novela(name, group_title):
    """Check if content is novela (soap opera)."""
    novela_keywords = ['novela', 'soap', 'telenovela']
    return any(keyword in name or keyword in group_title for keyword in novela_keywords)


def is_series(name):
    """Check if content is series (has season/episode pattern)."""
    # Pattern: S01E01, S1E1, S01e01, S02E01, Season 1 Episode 1, etc.
    # More flexible pattern to catch variations like S03e01, S02E01, etc.
    season_episode_pattern = r'[Ss]\d{1,2}[Ee]\d{1,2}|Season\s*\d+.*Episode\s*\d+'
    return bool(re.search(season_episode_pattern, name))


def is_series_by_group_title(group_title):
    """Check if group-title indicates series content."""
    if not group_title:
        return False
    
    series_keywords = [
        'series', 'séries', 'seriados', 'show', 'sitcom', 'drama',
        'temporada', 'temporadas', 'episódio', 'episodio', 'episode'
    ]
    
    return any(keyword in group_title for keyword in series_keywords)


def extract_season_episode(name):
    """Extract season and episode numbers from name."""
    season = None
    episode = None
    
    # Pattern: S01E01
    match = re.search(r'[Ss](\d{1,2})[Ee](\d{1,2})', name)
    if match:
        season = int(match.group(1))
        episode = int(match.group(2))
    
    # Pattern: Season 1 Episode 1
    match = re.search(r'Season\s*(\d+).*Episode\s*(\d+)', name, re.IGNORECASE)
    if match:
        season = int(match.group(1))
        episode = int(match.group(2))
    
    return season, episode


def extract_year(name):
    """Extract year from name with multiple format support."""
    # Try different year formats
    patterns = [
        r'\((\d{4})\)',  # (2024)
        r'\[(\d{4})\]',  # [2024]
        r'\s(\d{4})\s',  # 2024 between spaces
        r'(\d{4})$',     # 2024 at end
        r'[-._](\d{4})[-._]',  # 2024 with separators
    ]

    for pattern in patterns:
        match = re.search(pattern, name)
        if match:
            year = int(match.group(1))
            # Validate reasonable year range (1900-2030)
            if 1900 <= year <= 2030:
                return year

    return None
