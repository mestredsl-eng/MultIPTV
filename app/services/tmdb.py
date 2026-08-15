"""TMDB service with cache."""

import json
import requests
import unicodedata
from app.database import get_db
from app.services.config import get_tmdb_api_key, get_tmdb_cache_duration


TMDB_BASE_URL = "https://api.themoviedb.org/3"


def normalize_title(title):
    """Normalize title for cache lookup (case-insensitive, remove special chars)."""
    normalized = unicodedata.normalize('NFKD', title.lower())
    return ''.join(c for c in normalized if not unicodedata.combining(c))


def get_movie_info(name, year=None, categoria=None):
    """Get movie information from TMDB with cache and optional year filtering.
    
    Args:
        name: Name to search
        year: Optional year filter
        categoria: Original category to determine search type (movie vs tv)
    """
    titulo_normalizado = normalize_title(name)
    db = get_db()

    # Determine search type based on category
    search_type = 'tv' if categoria in ['Series', 'Novela', 'Cartoon'] else 'movie'
    
    # Check cache first using normalized title and type
    cached = db.execute('''
        SELECT * FROM tmdb_cache
        WHERE titulo_normalizado = ? AND tipo = ?
        AND ultima_consulta > datetime('now', '-' || ? || ' seconds')
    ''', (titulo_normalizado, search_type, get_tmdb_cache_duration())).fetchone()

    if cached:
        return json.loads(cached['json'])

    # Call TMDB API
    api_key = get_tmdb_api_key()
    if not api_key:
        # Return placeholder if no API key
        result = {
            'tmdb_id': None,
            'title': name,
            'year': None,
            'poster': None,
            'backdrop': None,
            'adult': False,
            'media_type': search_type
        }
    else:
        try:
            params = {
                'api_key': api_key,
                'query': name,
                'language': 'pt-BR',
                'include_adult': 'true'
            }
            
            # Add year filter if provided to reduce false positives
            if year:
                if search_type == 'movie':
                    params['year'] = year
                else:
                    params['first_air_date_year'] = year
            
            # Choose endpoint based on search type
            endpoint = f"{TMDB_BASE_URL}/search/{search_type}"
            
            response = requests.get(
                endpoint,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if data.get('results'):
                # Get best match considering year filter
                media = data['results'][0]
                
                # If year was provided, try to find exact year match
                if year and len(data['results']) > 1:
                    for result_item in data['results']:
                        if search_type == 'movie':
                            item_year = result_item.get('release_date', '')[:4] if result_item.get('release_date') else None
                        else:
                            item_year = result_item.get('first_air_date', '')[:4] if result_item.get('first_air_date') else None
                        
                        if item_year == str(year):
                            media = result_item
                            break
                
                # Check if media is adult based on TMDB's adult field
                is_adult = media.get('adult', False)
                
                # Extract year based on media type
                if search_type == 'movie':
                    year_extracted = media.get('release_date', '')[:4] if media.get('release_date') else None
                    title = media.get('title')
                else:
                    year_extracted = media.get('first_air_date', '')[:4] if media.get('first_air_date') else None
                    title = media.get('name')

                result = {
                    'tmdb_id': media.get('id'),
                    'title': title,
                    'year': year_extracted,
                    'poster': f"https://image.tmdb.org/t/p/w500{media.get('poster_path')}" if media.get('poster_path') else None,
                    'backdrop': f"https://image.tmdb.org/t/p/w780{media.get('backdrop_path')}" if media.get('backdrop_path') else None,
                    'adult': is_adult,
                    'media_type': search_type
                }
            else:
                result = {
                    'tmdb_id': None,
                    'title': name,
                    'year': None,
                    'poster': None,
                    'backdrop': None,
                    'adult': False,
                    'media_type': search_type
                }
        except Exception as e:
            # Return placeholder on error
            result = {
                'tmdb_id': None,
                'title': name,
                'year': None,
                'poster': None,
                'backdrop': None,
                'adult': False,
                'media_type': search_type
            }

    # Cache result with normalized title and type
    db.execute('''
        INSERT OR REPLACE INTO tmdb_cache
        (tmdb_id, titulo, titulo_normalizado, ano, tipo, poster, backdrop, json, ultima_consulta)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (result['tmdb_id'], result['title'], titulo_normalizado, result['year'], search_type,
          result['poster'], result['backdrop'], json.dumps(result)))
    db.commit()

    return result


def get_tv_info(name):
    """Get TV series information from TMDB with cache."""
    titulo_normalizado = normalize_title(name)
    db = get_db()
    
    # Check cache first using normalized title
    cached = db.execute('''
        SELECT * FROM tmdb_cache 
        WHERE titulo_normalizado = ? AND tipo = 'tv' 
        AND ultima_consulta > datetime('now', '-' || ? || ' seconds')
    ''', (titulo_normalizado, get_tmdb_cache_duration())).fetchone()
    
    if cached:
        return json.loads(cached['json'])
    
    # Call TMDB API
    api_key = get_tmdb_api_key()
    if not api_key:
        # Return placeholder if no API key
        result = {
            'tmdb_id': None,
            'title': name,
            'year': None,
            'poster': None,
            'backdrop': None
        }
    else:
        try:
            response = requests.get(
                f"{TMDB_BASE_URL}/search/tv",
                params={'api_key': api_key, 'query': name, 'language': 'pt-BR'},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('results'):
                tv = data['results'][0]
                result = {
                    'tmdb_id': tv.get('id'),
                    'title': tv.get('name'),
                    'year': tv.get('first_air_date', '')[:4] if tv.get('first_air_date') else None,
                    'poster': f"https://image.tmdb.org/t/p/w500{tv.get('poster_path')}" if tv.get('poster_path') else None,
                    'backdrop': f"https://image.tmdb.org/t/p/w780{tv.get('backdrop_path')}" if tv.get('backdrop_path') else None
                }
            else:
                result = {
                    'tmdb_id': None,
                    'title': name,
                    'year': None,
                    'poster': None,
                    'backdrop': None
                }
        except Exception as e:
            # Return placeholder on error
            result = {
                'tmdb_id': None,
                'title': name,
                'year': None,
                'poster': None,
                'backdrop': None
            }
    
    # Cache result with normalized title
    db.execute('''
        INSERT OR REPLACE INTO tmdb_cache 
        (tmdb_id, titulo, titulo_normalizado, ano, tipo, poster, backdrop, json, ultima_consulta)
        VALUES (?, ?, ?, ?, 'tv', ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (result['tmdb_id'], result['title'], titulo_normalizado, result['year'], 
          result['poster'], result['backdrop'], json.dumps(result)))
    db.commit()
    
    return result
