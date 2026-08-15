"""M3U parser service."""

import re
import hashlib
from pathlib import Path


def parse_m3u(file_path):
    """Parse M3U file and extract entries."""
    entries = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        current_entry = None
        
        for line in f:
            line = line.strip()
            
            if line.startswith('#EXTINF:'):
                # Parse EXTINF line
                current_entry = parse_extinf(line)
            elif line and not line.startswith('#'):
                # This is the URL line
                if current_entry:
                    current_entry['url'] = line
                    current_entry['hash'] = calculate_hash(line, current_entry.get('name', ''))
                    entries.append(current_entry)
                    current_entry = None
    
    return entries


def parse_extinf(line):
    """Parse EXTINF line and extract metadata."""
    entry = {
        'name': '',
        'duration': -1,
        'group_title': '',
        'logo': '',
        'tvg_id': '',
        'tvg_name': ''
    }
    
    # Remove #EXTINF:
    line = line[8:]
    
    # Extract duration
    match = re.match(r'(-?\d+)', line)
    if match:
        entry['duration'] = int(match.group(1))
    
    # Extract tvg-id
    match = re.search(r'tvg-id="([^"]*)"', line)
    if match:
        entry['tvg_id'] = match.group(1)
    
    # Extract tvg-name
    match = re.search(r'tvg-name="([^"]*)"', line)
    if match:
        entry['tvg_name'] = match.group(1)
    
    # Extract logo
    match = re.search(r'tvg-logo="([^"]*)"', line)
    if match:
        entry['logo'] = match.group(1)
    
    # Extract group-title
    match = re.search(r'group-title="([^"]*)"', line)
    if match:
        entry['group_title'] = match.group(1)
    
    # Extract name (everything after the last comma)
    if ',' in line:
        entry['name'] = line.rsplit(',', 1)[1].strip()
    
    return entry


def calculate_hash(url, name):
    """Calculate hash from URL and name (for TV channels only)."""
    hash_input = f"{url}|{name}"
    return hashlib.sha256(hash_input.encode()).hexdigest()


def calculate_hash_midia(categoria, nome_normalizado, ano):
    """Calculate hash from categoria + nome_normalizado (NOT URL). Year and quality are removed for duplicate detection."""
    # Remove quality and year from nome_normalizado before calculating hash
    nome_limpo = remove_quality_from_name(nome_normalizado)
    hash_input = f"{categoria}|{nome_limpo}"
    return hashlib.sha256(hash_input.encode()).hexdigest()


def remove_quality_indicators(nome):
    """
    Remove quality indicators from name for both hash calculation and filename sanitization.
    This is the canonical function - all quality removal should use this.
    
    Combines patterns from both remove_quality_from_name() and sanitize_filename()
    to ensure consistency across the system.
    """
    if not nome:
        return ''

    normalized = nome.lower()

    # Remove quality indicators in brackets (comprehensive list from both functions)
    bracket_patterns = [
        r'\(cinema\)',  # From parser
        r'\[l\]', r'\[4k\]', r'\[fhd\]', r'\[hd\]', r'\[sd\]',  # From both
        r'\[hdr\]', r'\[dolby\]', r'\[atmos\]', r'\[dts\]',  # From both
        r'\[leg\]', r'\[legendado\]', r'\[dub\]', r'\[dublado\]', r'\[dual\]', r'\[alt\]',  # From parser
        r'\[h265\]', r'\[hevc\]', r'\[hybrid\]', r'\[x265\]', r'\[x264\]',  # From both
        r'\[ac3\]', r'\[aac\]',  # From both
        r'\[mp4\]', r'\[mkv\]',  # From parser
        r'\[web-dl\]', r'\[webdl\]', r'\[bluray\]',  # From both
        r'\[bdrip\]', r'\[brrip\]', r'\[dvdrip\]', r'\[dvd\]', r'\[dv\]',  # From both
        r'\[hdtv\]', r'\[sdtv\]',  # From both
        r'\[webrip\]', r'\[bdscr\]', r'\[bdr\]', r'\[br\]',  # Additional common patterns
        r'\[h?\d+\]',  # From parser (catches [h264], [h265], etc.)
    ]

    for pattern in bracket_patterns:
        normalized = re.sub(pattern, '', normalized)

    # Remove quality indicators without brackets (from both functions)
    no_bracket_patterns = [
        r'\s*(4k|fhd|hd|sd|hdr|dolby|atmos|dts|h265|hevc|hybrid|x265|x264|ac3|aac|web-dl|webdl|bluray|bdrip|brrip|dvdrip|dv|dvd|hdtv|sdtv|webrip|bdscr|bdr|br)\s*$',  # End of string
        r'^\s*(4k|fhd|hd|sd|hdr|dolby|atmos|dts|h265|hevc|hybrid|x265|x264|ac3|aac|web-dl|webdl|bluray|bdrip|brrip|dvdrip|dv|dvd|hdtv|sdtv|webrip|bdscr|bdr|br)\s*',  # Start of string
    ]

    for pattern in no_bracket_patterns:
        normalized = re.sub(pattern, '', normalized)

    # Remove resolution patterns (from exporter)
    normalized = re.sub(r'\s*\d+p\s*', '', normalized)  # 720p, 1080p, 2160p
    normalized = re.sub(r'\s*\d+k\s*', '', normalized)  # 4k, 8k

    # Remove year patterns (from parser - important for hash calculation)
    normalized = re.sub(r'\s*-\s*[\(\[]\d{4}[\)\]]\s*', '', normalized)
    normalized = re.sub(r'\s*[\(\[]\d{4}[\)\]]\s*', '', normalized)

    # Remove language indicators (from parser - important for hash calculation)
    normalized = re.sub(r'\s(leg|legendado|dub|dublado|dual|alt)\s*$', '', normalized)
    normalized = re.sub(r'^(leg|legendado|dub|dublado|dual|alt)\s', '', normalized)

    # Remove adult content markers (from exporter)
    normalized = re.sub(r'\[adulto?\]', '', normalized)
    normalized = re.sub(r'\[xxx\]', '', normalized)
    normalized = re.sub(r'\[porn\]', '', normalized)
    normalized = re.sub(r'\bxxx\b', '', normalized)
    normalized = re.sub(r'\bporn\b', '', normalized)
    normalized = re.sub(r'\badulto?\b', '', normalized)

    # Remove extra spaces
    normalized = ' '.join(normalized.split())

    return normalized


def remove_quality_from_name(nome):
    """
    Remove quality indicators from name for duplicate detection.
    
    DEPRECATED: Use remove_quality_indicators() instead.
    This function is kept for backward compatibility but now delegates to the canonical function.
    """
    return remove_quality_indicators(nome)


def normalize_name(name):
    """Normalize name for comparison."""
    import unicodedata
    normalized = unicodedata.normalize('NFKD', name.lower())
    return ''.join(c for c in normalized if not unicodedata.combining(c))


def extract_year(name):
    """Extract year from name with multiple format support."""
    import re

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


def remove_year_from_name(name):
    """Remove year from name for database storage (year is stored separately in 'ano' field)."""
    if not name:
        return name
    
    import re
    
    # Remove year patterns with various formats
    patterns = [
        r'\s*-\s*\(\d{4}\)\s*$',  # - (2024) at end
        r'\s*-\s*\[\d{4}\]\s*$',  # - [2024] at end
        r'\s*-\s*\d{4}\s*$',      # - 2024 at end
        r'\s*\(\d{4}\)\s*$',      # (2024) at end
        r'\s*\[\d{4}\]\s*$',      # [2024] at end
        r'\s*\d{4}\s*$',          # 2024 at end
        r'\s*-\s*\(\d{4}\)\s*',   # - (2024) anywhere
        r'\s*-\s*\[\d{4}\]\s*',   # - [2024] anywhere
        r'\s*-\s*\d{4}\s*',       # - 2024 anywhere
        r'\s*\(\d{4}\)\s*',       # (2024) anywhere
        r'\s*\[\d{4}\]\s*',       # [2024] anywhere
        r'\s\d{4}\s',             # 2024 between spaces
        r'[-._]\d{4}[-._]',       # 2024 with separators
    ]
    
    cleaned_name = name
    for pattern in patterns:
        cleaned_name = re.sub(pattern, ' ', cleaned_name, flags=re.IGNORECASE)
    
    # Clean up extra spaces and hyphens
    cleaned_name = re.sub(r'\s+-\s*$', ' ', cleaned_name)  # Replace trailing " -" with space
    cleaned_name = re.sub(r'\s+-\s+', ' ', cleaned_name)  # Replace " - " with single space
    cleaned_name = re.sub(r'\s+', ' ', cleaned_name)       # Replace multiple spaces with single space
    cleaned_name = cleaned_name.strip()
    
    return cleaned_name


def extract_quality_features(name):
    """Extract quality features from name for better duplicate detection."""
    if not name:
        return {
            'has_hdr': False,
            'has_alt': False,
            'is_legendado': False,
            'is_dublado': False,
            'is_dual': False,
            'quality_level': 0,
            'codec': None,
            'audio': None
        }
    
    features = {
        'has_hdr': False,
        'has_alt': False,
        'is_legendado': False,
        'is_dublado': False,
        'is_dual': False,
        'quality_level': 0,
        'codec': None,
        'audio': None
    }
    
    name_lower = name.lower()
    
    # Check HDR
    features['has_hdr'] = bool(re.search(r'\[?hdr\]?', name_lower))
    
    # Check alternative version
    features['has_alt'] = bool(re.search(r'\[?alt\]?', name_lower))
    
    # Check language
    features['is_legendado'] = bool(re.search(r'\[?(leg|legendado)\]?', name_lower))
    features['is_dublado'] = bool(re.search(r'\[?(dub|dublado)\]?', name_lower))
    features['is_dual'] = bool(re.search(r'\[?dual\]?', name_lower))
    
    # Quality level priority
    quality_patterns = [
        (r'\[?4k\]?', 4),
        (r'\[?fhd\]?', 3),
        (r'\[?hd\]?', 2),
        (r'\[?sd\]?', 1),
    ]
    
    for pattern, level in quality_patterns:
        if re.search(pattern, name_lower):
            features['quality_level'] = level
            break
    
    # Codec
    codec_patterns = [
        r'\[?h265\]?',
        r'\[?hevc\]?',
        r'\[?x265\]?',
        r'\[?h264\]?',
        r'\[?x264\]?',
    ]
    
    for pattern in codec_patterns:
        if re.search(pattern, name_lower):
            features['codec'] = pattern.replace(r'\[?', '').replace(r'\]?', '').upper()
            break
    
    # Audio
    audio_patterns = [
        r'\[?dolby\]?',
        r'\[?atmos\]?',
        r'\[?dts\]?',
        r'\[?ac3\]?',
        r'\[?aac\]?',
    ]
    
    for pattern in audio_patterns:
        if re.search(pattern, name_lower):
            features['audio'] = pattern.replace(r'\[?', '').replace(r'\]?', '').upper()
            break
    
    return features


def calculate_similarity_score(name1, name2):
    """Calculate similarity score between two media names considering quality features."""
    # Normalize names for comparison
    norm1 = remove_quality_from_name(name1)
    norm2 = remove_quality_from_name(name2)
    
    # Basic name similarity
    if norm1 == norm2:
        base_score = 100
    else:
        # Calculate Levenshtein distance or similar
        base_score = calculate_string_similarity(norm1, norm2)
    
    if base_score < 80:  # If base names are too different, not duplicates
        return 0
    
    # Extract features
    features1 = extract_quality_features(name1)
    features2 = extract_quality_features(name2)
    
    # Penalize differences in important features
    penalty = 0
    
    # Language mismatch penalty
    if features1['is_legendado'] != features2['is_legendado']:
        penalty += 10
    if features1['is_dublado'] != features2['is_dublado']:
        penalty += 10
    if features1['is_dual'] != features2['is_dual']:
        penalty += 5
    
    # Quality level penalty
    quality_diff = abs(features1['quality_level'] - features2['quality_level'])
    penalty += quality_diff * 5
    
    # HDR penalty
    if features1['has_hdr'] != features2['has_hdr']:
        penalty += 15
    
    # Alternative version penalty (lower, as it's less critical)
    if features1['has_alt'] != features2['has_alt']:
        penalty += 3
    
    # Codec penalty (minor)
    if features1['codec'] != features2['codec']:
        penalty += 2
    
    # Audio penalty (minor)
    if features1['audio'] != features2['audio']:
        penalty += 2
    
    final_score = max(0, base_score - penalty)
    return final_score


def calculate_string_similarity(str1, str2):
    """Calculate string similarity using a simple algorithm."""
    if not str1 or not str2:
        return 0
    
    if str1 == str2:
        return 100
    
    # Simple Levenshtein distance calculation
    m, n = len(str1), len(str2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if str1[i-1] == str2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
    
    max_len = max(m, n)
    similarity = (1 - dp[m][n] / max_len) * 100
    return similarity


def calculate_hash_with_year(categoria, nome_normalizado, ano):
    """Calcula hash incluindo ano para identificar conteúdo específico."""
    nome_limpo = remove_quality_from_name(nome_normalizado)
    hash_input = f"{categoria}|{nome_limpo}|{ano or 0}"
    return hashlib.sha256(hash_input.encode()).hexdigest()


def calculate_hash_base(categoria, nome_normalizado):
    """Calcula hash base sem ano para agrupar versões de qualidade."""
    nome_limpo = remove_quality_from_name(nome_normalizado)
    hash_input = f"{categoria}|{nome_limpo}"
    return hashlib.sha256(hash_input.encode()).hexdigest()


def map_quality_level_to_string(level):
    """Converte quality_level numérico para string."""
    quality_map = {
        4: '4K',
        3: 'FHD',
        2: 'HD',
        1: 'SD',
        0: 'SD'
    }
    return quality_map.get(level, 'SD')


def calcular_score_qualidade(qualidade, tem_legendado, has_hdr=False, codec=None, audio=None):
    """
    Calcula score de qualidade usando pontuação ponderada.
    Maior score = melhor qualidade.
    """
    score = 0
    
    # Resolução (peso: 40)
    qualidade_scores = {'4K': 40, 'FHD': 30, 'HD': 20, 'SD': 10, None: 5}
    score += qualidade_scores.get(qualidade, 5)
    
    # HDR (peso: 15)
    if has_hdr:
        score += 15
    
    # Legenda (peso: 10)
    if tem_legendado:
        score += 10
    
    # Codec (peso: 10)
    codec_scores = {'H265': 10, 'HEVC': 10, 'H264': 5, 'X264': 5, None: 0}
    score += codec_scores.get(codec, 0)
    
    # Áudio (peso: 5)
    audio_scores = {'ATMOS': 5, 'DOLBY': 4, 'DTS': 3, 'AC3': 2, 'AAC': 1, None: 0}
    score += audio_scores.get(audio, 0)
    
    return score


def count_words(name):
    """
    Count words in a media name for validation purposes.
    
    Removes quality indicators, special characters, and counts words separated by spaces.
    Used for TMDB validation rule: movies with ≤2 words need TMDB validation.
    
    Args:
        name: Media name to count words from
        
    Returns:
        int: Number of words in the name
    """
    if not name:
        return 0
    
    # Remove quality indicators using the canonical function
    cleaned = remove_quality_indicators(name)
    
    # Remove special characters but keep spaces and basic punctuation
    cleaned = re.sub(r'[^\w\s\-]', ' ', cleaned)
    
    # Replace multiple spaces/hyphens with single space
    cleaned = re.sub(r'[\s\-]+', ' ', cleaned)
    
    # Strip and split by spaces
    words = cleaned.strip().split()
    
    return len(words)
