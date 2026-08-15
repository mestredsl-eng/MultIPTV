"""TV deduplication service with strong rules."""

import re
from app.database import get_db
from app.services.parser import normalize_name, remove_quality_from_name, calculate_similarity_score, extract_quality_features


def normalize_channel_name(name):
    """Normalize channel name for deduplication."""
    # Remove quality suffixes
    name = re.sub(r'\s*\[?\s*(FHD|HD|SD| -|4K|8K)\s*\]?\s*$', '', name, flags=re.IGNORECASE)
    # Remove state/region suffixes
    name = re.sub(r'\s*\[?\s*(SP|RJ|MG|RS|PR|SC|BA|DF|GO|PE|AM|CE|MA|PA|PI|RN|RR|RO|SE|TO|AC|AL|AP|ES|MS|MT|TO)\s*\]?\s*$', '', name, flags=re.IGNORECASE)
    # Remove [L] suffix
    name = re.sub(r'\s*\[L\]\s*$', '', name, flags=re.IGNORECASE)
    return normalize_name(name.strip())


def deduplicate_tv_channels(db):
    """Deduplicate TV channels with strong priority rules."""
    # Get all TV channels
    channels = db.execute('SELECT * FROM tv_channels WHERE status = 1').fetchall()
    
    # Group by normalized name
    groups = {}
    for channel in channels:
        normalized = normalize_channel_name(channel['nome_canal'])
        if normalized not in groups:
            groups[normalized] = []
        groups[normalized].append(channel)
    
    # For each group, select winner
    for normalized, group in groups.items():
        if len(group) > 1:
            winner = select_winner(group)
            
            # Blacklist all others in tv_channels table
            for channel in group:
                if channel['id'] != winner['id']:
                    db.execute('''
                        UPDATE tv_channels SET black_list = 1 WHERE id = ?
                    ''', (channel['id'],))
    
    db.commit()


def select_winner(channels):
    """Select winner from channel group based on priority rules."""
    # Priority: [L] > FHD > HD > rest
    priority = {'[L]': 4, 'FHD': 3, 'HD': 2, '': 1, ' -': 0}
    
    def get_priority(channel):
        name = channel['nome_canal'].upper()
        for suffix, score in priority.items():
            if suffix in name:
                return score
        return 1
    
    return max(channels, key=get_priority)


def deduplicate_media_advanced(db):
    """Advanced deduplication for media items considering quality features."""
    
    # Get all media items
    medias = db.execute('SELECT * FROM midias WHERE status = 1 AND black_list = 0').fetchall()
    
    # Group by normalized name
    groups = {}
    for media in medias:
        normalized_name = remove_quality_from_name(media['nome_da_midia'])
        year = media['ano'] if 'ano' in media.keys() else None
        
        # Create composite key: normalized_name + year
        group_key = f"{normalized_name}|{year or ''}"
        
        if group_key not in groups:
            groups[group_key] = []
        groups[group_key].append(media)
    
    # Process each group for duplicates
    duplicates_found = 0
    for group_key, group in groups.items():
        if len(group) > 1:
            # Calculate similarity matrix
            duplicate_groups = find_duplicate_groups(group)
            
            # For each duplicate group, select winner
            for dup_group in duplicate_groups:
                if len(dup_group) > 1:
                    winner = select_media_winner(dup_group)
                    
                    # Blacklist all others
                    for media in dup_group:
                        if media['id'] != winner['id']:
                            db.execute('''
                                UPDATE midias SET black_list = 1 WHERE id = ?
                            ''', (media['id'],))
                            duplicates_found += 1
    
    db.commit()
    return duplicates_found


def find_duplicate_groups(media_list):
    """Find duplicate groups based on similarity scoring."""
    if len(media_list) < 2:
        return [media_list]
    
    groups = []
    used_indices = set()
    
    for i, media1 in enumerate(media_list):
        if i in used_indices:
            continue
            
        current_group = [media1]
        used_indices.add(i)
        
        for j, media2 in enumerate(media_list):
            if j in used_indices:
                continue
                
            # Calculate similarity score
            score = calculate_similarity_score(
                media1['nome_da_midia'],
                media2['nome_da_midia']
            )
            
            # If similarity is high enough, consider them duplicates
            if score >= 85:  # High similarity threshold
                current_group.append(media2)
                used_indices.add(j)
        
        groups.append(current_group)
    
    return groups


def select_media_winner(media_list):
    """Select winner from media group based on quality priority."""
    def get_media_score(media):
        name = media['nome_da_midia']
        features = extract_quality_features(name)
        year = media['ano'] if 'ano' in media.keys() else None
        
        score = 0
        
        # Base score for having year
        if year:
            score += 10
        
        # Quality level (4K > FHD > HD > SD)
        score += features['quality_level'] * 10
        
        # HDR bonus
        if features['has_hdr']:
            score += 15
        
        # Language priority: Dublado > Dual > Legendado > None
        if features['is_dublado']:
            score += 20
        elif features['is_dual']:
            score += 15
        elif features['is_legendado']:
            score += 10
        
        # Codec preference: H265/HEVC > H264/x264
        if features['codec'] in ['H265', 'HEVC', 'X265']:
            score += 8
        elif features['codec'] in ['H264', 'X264']:
            score += 5
        
        # Audio preference: Dolby/Atmos > DTS > AC3 > AAC
        if features['audio'] in ['DOLBY', 'ATMOS']:
            score += 10
        elif features['audio'] == 'DTS':
            score += 8
        elif features['audio'] == 'AC3':
            score += 5
        elif features['audio'] == 'AAC':
            score += 3
        
        # Alternative version penalty (usually worse quality)
        if features['has_alt']:
            score -= 5
        
        return score
    
    return max(media_list, key=get_media_score)


def deduplicate_media(db):
    """Deduplicate media items (movies and series) based on hash."""
    # This is handled by the unique constraint on hash_midia
    # But we can clean up duplicates if they exist
    pass
