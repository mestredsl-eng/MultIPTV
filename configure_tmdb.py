from app.app import create_app
from app.services.config import set_tmdb_api_key

# Create app context
app = create_app()
with app.app_context():
    # Set TMDB API key
    set_tmdb_api_key('45b57d4da7c238df851f9dcad97bef3c')
    print("TMDB API key configurada com sucesso")
