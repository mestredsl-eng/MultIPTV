from app.app import create_app
from app.services.tv_builder import build_tv_m3u

# Create app context
app = create_app()
with app.app_context():
    # Generate TV M3U
    tv_m3u_path = build_tv_m3u()
    print(f"TV M3U gerado em: {tv_m3u_path}")
    
    # Show first few lines
    with open(tv_m3u_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        print(f"Total linhas: {len(lines)}")
        print("Primeiras 20 linhas:")
        for line in lines[:20]:
            print(line.strip())
