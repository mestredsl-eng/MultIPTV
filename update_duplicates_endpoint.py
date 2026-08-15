"""Script to update duplicates endpoint to use DuplicateManager."""

with open('app/routes/api.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_code = """@bp.route('/media/items/<int:media_id>/duplicates', methods=['GET'])
def get_duplicates(media_id):
    \"\"\"Get items with same hash_midia (duplicates).\"\"\"
    from app.database import get_db
    
    db = get_db()
    
    try:
        # Get hash_midia of the item
        item = db.execute('SELECT hash_midia FROM midias WHERE id = ?', (media_id,)).fetchone()
        if not item or not item['hash_midia']:
            return jsonify({'success': True, 'duplicates': []})
        
        hash_midia = item['hash_midia']
        
        # Get all items with same hash_midia
        duplicates = db.execute('''
            SELECT * FROM midias
            WHERE hash_midia = ? AND id != ?
            ORDER BY nome_da_midia
        ''', (hash_midia, media_id)).fetchall()
        
        return jsonify({
            'success': True,
            'duplicates': [dict(item) for item in duplicates],
            'hash_midia': hash_midia
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})"""

new_code = """@bp.route('/media/items/<int:media_id>/duplicates', methods=['GET'])
def get_duplicates(media_id):
    \"\"\"Get items with same hash_midia and base name (enhanced duplicate detection).\"\"\"
    from app.database import get_db
    from app.services.duplicate_manager import DuplicateManager
    
    db = get_db()
    
    try:
        duplicate_manager = DuplicateManager(db)
        
        # Use enhanced duplicate detection
        result = duplicate_manager.find_all_duplicates(media_id)
        
        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']})
        
        return jsonify({
            'success': True,
            'hash_duplicates': result['hash_duplicates'],
            'name_duplicates': result['name_duplicates'],
            'total_duplicates': result['total_duplicates']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})"""

if old_code in content:
    content = content.replace(old_code, new_code)
    with open('app/routes/api.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✅ Endpoint de duplicatas atualizado para usar DuplicateManager')
else:
    print('❌ Código antigo não encontrado no endpoint')
    if 'get_duplicates' in content:
        print('✅ Função get_duplicates encontrada, mas formato diferente')
    else:
        print('❌ Função get_duplicates não encontrada')