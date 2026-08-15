"""Clean up duplicate and orphaned entries in tv_channels table."""

from app.app import create_app

app = create_app()
with app.app_context():
    from app.database import get_db
    
    db = get_db()
    
    print("=" * 60)
    print("CLEANING TV_CHANNELS DUPLICATES")
    print("=" * 60)
    
    # Find duplicate channel names
    duplicates = db.execute('''
        SELECT nome_canal, COUNT(*) as count
        FROM tv_channels
        GROUP BY nome_canal
        HAVING COUNT(*) > 1
        ORDER BY count DESC
    ''').fetchall()
    
    print(f"\nFound {len(duplicates)} duplicate channel names:")
    
    total_removed = 0
    
    for dup in duplicates:
        channel_name = dup['nome_canal']
        count = dup['count']
        
        print(f"\n  {channel_name} ({count} duplicates)")
        
        # Get all entries for this channel
        entries = db.execute('''
            SELECT id, hash_canal, black_list, status, ultima_atualizacao
            FROM tv_channels
            WHERE nome_canal = ?
            ORDER BY ultima_atualizacao DESC
        ''', (channel_name,)).fetchall()
        
        # Keep the most recent one, remove others
        if len(entries) > 1:
            keep = entries[0]
            remove = entries[1:]
            
            print(f"    Keeping: ID {keep['id']}, Blacklist: {keep['black_list']}, Hash: {keep['hash_canal'][:20]}...")
            
            for entry in remove:
                print(f"    Removing: ID {entry['id']}, Blacklist: {entry['black_list']}, Hash: {entry['hash_canal'][:20]}...")
                db.execute('DELETE FROM tv_channels WHERE id = ?', (entry['id'],))
                total_removed += 1
    
    # Find orphaned channels (not in midias)
    orphaned = db.execute('''
        SELECT tc.id, tc.nome_canal, tc.hash_canal
        FROM tv_channels tc
        LEFT JOIN midias m ON tc.hash_canal = m.hash_midia AND m.categoria = 'TV'
        WHERE m.hash_midia IS NULL
    ''').fetchall()
    
    print(f"\n\nFound {len(orphaned)} orphaned channels (not in midias table):")
    
    for orphan in orphaned[:10]:  # Show first 10
        print(f"  - {orphan['nome_canal']} (ID: {orphan['id']})")
    
    if len(orphaned) > 10:
        print(f"  ... and {len(orphaned) - 10} more")
    
    # Remove orphaned channels
    if orphaned:
        print(f"\nRemoving {len(orphaned)} orphaned channels...")
        for orphan in orphaned:
            db.execute('DELETE FROM tv_channels WHERE id = ?', (orphan['id'],))
            total_removed += 1
    
    db.commit()
    
    print(f"\n" + "=" * 60)
    print(f"TOTAL REMOVED: {total_removed} entries")
    print("=" * 60)
    
    # Verify cleanup
    remaining = db.execute('SELECT COUNT(*) FROM tv_channels').fetchone()[0]
    print(f"Remaining channels in tv_channels: {remaining}")
