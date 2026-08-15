"""Test script to verify blacklist status is preserved during TV export."""

from app.app import create_app

# Create app context
app = create_app()
with app.app_context():
    from app.database import get_db
    from app.services.exporter import generate_tv_m3u_and_epg
    
    db = get_db()
    
    print("=" * 60)
    print("TESTING BLACKLIST EXPORT FIX")
    print("=" * 60)
    
    # Check current state
    print("\n1. Checking TV media items in midias table:")
    tv_items = db.execute('''
        SELECT id, nome_da_midia, black_list, status 
        FROM midias 
        WHERE categoria = 'TV' 
        ORDER BY black_list DESC, nome_da_midia 
        LIMIT 10
    ''').fetchall()
    
    print(f"   Total TV items in midias: {len(tv_items)}")
    blacklisted_count = sum(1 for item in tv_items if item['black_list'] == 1)
    print(f"   Blacklisted: {blacklisted_count}")
    print(f"   Active: {len(tv_items) - blacklisted_count}")
    
    if tv_items:
        print("\n   Sample items:")
        for item in tv_items[:5]:
            status = "BLACKLISTED" if item['black_list'] == 1 else "ACTIVE"
            print(f"   - {item['nome_da_midia']}: {status}")
    
    # Check tv_channels table before export
    print("\n2. Checking tv_channels table before export:")
    tv_channels_before = db.execute('''
        SELECT id, nome_canal, black_list, status 
        FROM tv_channels 
        ORDER BY black_list DESC, nome_canal 
        LIMIT 10
    ''').fetchall()
    
    print(f"   Total channels in tv_channels: {len(tv_channels_before)}")
    blacklisted_channels_before = sum(1 for item in tv_channels_before if item['black_list'] == 1)
    print(f"   Blacklisted: {blacklisted_channels_before}")
    print(f"   Active: {len(tv_channels_before) - blacklisted_channels_before}")
    
    # Run the export function
    print("\n3. Running generate_tv_m3u_and_epg()...")
    try:
        generate_tv_m3u_and_epg(db)
        print("   Export completed successfully")
    except Exception as e:
        print(f"   ERROR during export: {e}")
        import traceback
        traceback.print_exc()
    
    # Check tv_channels table after export
    print("\n4. Checking tv_channels table after export:")
    tv_channels_after = db.execute('''
        SELECT id, nome_canal, black_list, status 
        FROM tv_channels 
        ORDER BY black_list DESC, nome_canal 
        LIMIT 10
    ''').fetchall()
    
    print(f"   Total channels in tv_channels: {len(tv_channels_after)}")
    blacklisted_channels_after = sum(1 for item in tv_channels_after if item['black_list'] == 1)
    print(f"   Blacklisted: {blacklisted_channels_after}")
    print(f"   Active: {len(tv_channels_after) - blacklisted_channels_after}")
    
    # Verify blacklist consistency
    print("\n5. Verifying blacklist consistency between midias and tv_channels:")
    inconsistent = db.execute('''
        SELECT m.nome_da_midia, m.black_list as media_blacklist, t.black_list as channel_blacklist
        FROM midias m
        LEFT JOIN tv_channels t ON m.hash_midia = t.hash_canal
        WHERE m.categoria = 'TV' AND t.black_list != m.black_list
        LIMIT 10
    ''').fetchall()
    
    if inconsistent:
        print(f"   ⚠️  FOUND {len(inconsistent)} INCONSISTENT ITEMS:")
        for item in inconsistent:
            print(f"   - {item['nome_da_midia']}: midias={item['media_blacklist']}, tv_channels={item['channel_blacklist']}")
    else:
        print("   ✅ All blacklist statuses are CONSISTENT")
    
    # Check if blacklisted channels are in the M3U file
    print("\n6. Checking if blacklisted channels are in tv.m3u file:")
    from pathlib import Path
    from app.services.config import get_galeria_path
    
    galeria_path = Path(get_galeria_path())
    m3u_file = galeria_path / 'TV' / 'tv.m3u'
    
    if m3u_file.exists():
        with open(m3u_file, 'r', encoding='utf-8') as f:
            m3u_content = f.read()
        
        # Get blacklisted channel names
        blacklisted_names = db.execute('''
            SELECT nome_canal FROM tv_channels WHERE black_list = 1 AND status = 1
        ''').fetchall()
        
        blacklisted_in_m3u = []
        for channel in blacklisted_names:
            if channel['nome_canal'] in m3u_content:
                blacklisted_in_m3u.append(channel['nome_canal'])
        
        if blacklisted_in_m3u:
            print(f"   ⚠️  FOUND {len(blacklisted_in_m3u)} BLACKLISTED CHANNELS IN M3U:")
            for name in blacklisted_in_m3u[:5]:
                print(f"   - {name}")
        else:
            print("   ✅ No blacklisted channels found in M3U file")
    else:
        print(f"   ⚠️  M3U file not found at {m3u_file}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)
