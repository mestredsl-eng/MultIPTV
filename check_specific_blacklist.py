"""Check specific blacklisted channel in M3U."""

from app.app import create_app

app = create_app()
with app.app_context():
    from app.database import get_db
    from pathlib import Path
    from app.services.config import get_galeria_path
    
    db = get_db()
    
    channel_name = "Capital Inicial Acustico MTV"
    
    print(f"Checking channel: {channel_name}")
    print("=" * 60)
    
    # Check in midias table
    media = db.execute('''
        SELECT id, nome_da_midia, black_list, status, categoria, hash_midia
        FROM midias 
        WHERE nome_da_midia LIKE ?
    ''', (f'%{channel_name}%',)).fetchall()
    
    print(f"\nFound {len(media)} matches in midias table:")
    for item in media:
        print(f"  - ID: {item['id']}, Name: {item['nome_da_midia']}")
        print(f"    Blacklist: {item['black_list']}, Status: {item['status']}, Category: {item['categoria']}")
        print(f"    Hash: {item['hash_midia']}")
    
    # Check in tv_channels table
    channels = db.execute('''
        SELECT id, nome_canal, black_list, status, hash_canal
        FROM tv_channels 
        WHERE nome_canal LIKE ?
    ''', (f'%{channel_name}%',)).fetchall()
    
    print(f"\nFound {len(channels)} matches in tv_channels table:")
    for item in channels:
        print(f"  - ID: {item['id']}, Name: {item['nome_canal']}")
        print(f"    Blacklist: {item['black_list']}, Status: {item['status']}")
        print(f"    Hash: {item['hash_canal']}")
    
    # Check M3U file
    galeria_path = Path(get_galeria_path())
    m3u_file = galeria_path / 'TV' / 'tv.m3u'
    
    if m3u_file.exists():
        with open(m3u_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if channel_name in content:
            print(f"\n⚠️  Channel '{channel_name}' FOUND in M3U file")
            # Find the line
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if channel_name in line:
                    print(f"  Line {i}: {line}")
                    if i > 0:
                        print(f"  Line {i-1}: {lines[i-1]}")
        else:
            print(f"\n✅ Channel '{channel_name}' NOT found in M3U file")
    else:
        print(f"\n⚠️  M3U file not found")
