from app.app import create_app
from app.services.tv_m3u_generator import generate_epg_xmltv
from pathlib import Path
from app.services.config import get_galeria_path

app = create_app()
with app.app_context():
    from app.database import get_db
    db = get_db()

    galeria_path = Path(get_galeria_path())
    epg_file = galeria_path / 'TV' / 'epg.xml'

    # Gerar EPG sem fontes externas primeiro (apenas com canais do banco)
    result = generate_epg_xmltv(db, epg_file, epg_sources=None)
    print(f"Resultado: {result}")
    
    # Mostrar primeiras linhas para verificação
    print("\n--- Primeiras linhas do epg.xml ---")
    with open(epg_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines[:30]:
            print(line.strip())
