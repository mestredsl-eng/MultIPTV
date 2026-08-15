from app.app import create_app
from app.services.tmdb import get_movie_info, get_tv_info

# Create app context
app = create_app()
with app.app_context():
    # Test TMDB with a known movie
    print("Testando TMDB com filme 'Avatar':")
    movie_info = get_movie_info('Avatar')
    print(f"  TMDB ID: {movie_info['tmdb_id']}")
    print(f"  Title: {movie_info['title']}")
    print(f"  Year: {movie_info['year']}")
    print(f"  Poster: {movie_info['poster']}")
    print()
    
    # Test TMDB with a known TV series
    print("Testando TMDB com série 'Breaking Bad':")
    tv_info = get_tv_info('Breaking Bad')
    print(f"  TMDB ID: {tv_info['tmdb_id']}")
    print(f"  Title: {tv_info['title']}")
    print(f"  Year: {tv_info['year']}")
    print(f"  Poster: {tv_info['poster']}")
