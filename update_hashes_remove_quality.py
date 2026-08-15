import sqlite3
import os
import re
import hashlib

db_path = os.path.join(os.path.dirname(__file__), 'database', 'iptv.db')

def remove_quality_from_name(nome):
    """Remove quality indicators from name for duplicate detection."""
    if not nome:
        return ''

    normalized = nome.lower()

    # Remove quality indicators in brackets
    normalized = re.sub(r'\[h?\d+\]', '', normalized)
    normalized = re.sub(r'\[hdr\]', '', normalized)
    normalized = re.sub(r'\[dolby\]', '', normalized)
    normalized = re.sub(r'\[atmos\]', '', normalized)
    normalized = re.sub(r'\[dts\]', '', normalized)

    # Remove quality indicators at end or start
    normalized = re.sub(r'\s*(4k|fhd|hd|sd|hdr|dolby|atmos|dts)\s*$', '', normalized)
    normalized = re.sub(r'^\s*(4k|fhd|hd|sd|hdr|dolby|atmos|dts)\s*', '', normalized)

    # Remove extra spaces
    normalized = ' '.join(normalized.split())

    return normalized

def get_quality_score(qualidade, nome):
    """Retorna o score de qualidade."""
    quality_order = {
        '[L]': 10,
        '4K HDR': 9.5,
        '4K': 9,
        'FHD HDR': 8.5,
        'FHD': 8,
        'HD HDR': 7.5,
        'HD': 7,
        'SD': 6,
        '': 5,
    }

    if qualidade:
        if '[L]' in qualidade:
            return quality_order['[L]']
        for q, score in quality_order.items():
            if q and q in qualidade.upper():
                return score

    if nome:
        nome_upper = nome.upper()
        if '[L]' in nome_upper:
            return quality_order['[L]']
        if '4K' in nome_upper and 'HDR' in nome_upper:
            return quality_order['4K HDR']
        if '4K' in nome_upper:
            return quality_order['4K']
        if 'FHD' in nome_upper and 'HDR' in nome_upper:
            return quality_order['FHD HDR']
        if 'FHD' in nome_upper:
            return quality_order['FHD']
        if 'HD' in nome_upper and 'HDR' in nome_upper:
            return quality_order['HD HDR']
        if 'HD' in nome_upper:
            return quality_order['HD']
        if 'SD' in nome_upper:
            return quality_order['SD']

    return quality_order['']

conn = sqlite3.connect(db_path)
db = conn.cursor()

print("Atualizando hash_midia para remover qualidade...")
print("=" * 60)

# Primeiro, remover blacklist de todos
db.execute('UPDATE midias SET black_list = 0 WHERE status = 1')
conn.commit()
print("Blacklist removido de todos os itens")

# Buscar todas as mídias ativas
db.execute('''
    SELECT id, categoria, nome_normalizado, ano, hash_midia, nome_da_midia, qualidade
    FROM midias
    WHERE status = 1
''')
items = db.fetchall()

print(f"Total de mídias ativas: {len(items)}")

# Calcular novos hashes e agrupar
hash_groups = {}
for item in items:
    media_id, categoria, nome_normalizado, ano, old_hash, nome_da_midia, qualidade = item

    # Calcular novo hash sem qualidade
    nome_sem_qualidade = remove_quality_from_name(nome_normalizado)
    hash_input = f"{categoria}|{nome_sem_qualidade}|{ano or ''}"
    new_hash = hashlib.sha256(hash_input.encode()).hexdigest()

    if new_hash not in hash_groups:
        hash_groups[new_hash] = []
    hash_groups[new_hash].append({
        'id': media_id,
        'nome': nome_da_midia,
        'qualidade': qualidade,
        'quality_score': get_quality_score(qualidade, nome_da_midia)
    })

print(f"Grupos de hash únicos: {len(hash_groups)}")

# Processar cada grupo
total_to_blacklist = 0
total_kept = 0
processed_count = 0
ids_to_blacklist = []

for new_hash, group in hash_groups.items():
    if len(group) > 1:
        # Ordenar por score de qualidade (decrescente)
        group.sort(key=lambda x: x['quality_score'], reverse=True)

        # Manter apenas o melhor
        best = group[0]
        others = group[1:]

        if processed_count < 10:
            print(f"\nGrupo hash: {new_hash[:20]}...")
            print(f"  Mantendo (ID {best['id']}, Score {best['quality_score']}): {best['nome'][:60]}...")

        total_kept += 1

        for item in others:
            if processed_count < 10:
                print(f"  Marcando como duplicado (ID {item['id']}, Score {item['quality_score']}): {item['nome'][:60]}...")
            ids_to_blacklist.append(item['id'])
            total_to_blacklist += 1

        processed_count += 1

# Marcar duplicados como blacklist
for media_id in ids_to_blacklist:
    db.execute('UPDATE midias SET black_list = 1 WHERE id = ?', (media_id,))

conn.commit()
print(f"Duplicados marcados como blacklist: {total_to_blacklist}")

# Primeiro, atualizar hash_midia dos itens blacklist para valor temporário único
for media_id in ids_to_blacklist:
    temp_hash = hashlib.sha256(f"BLACKLIST_{media_id}".encode()).hexdigest()
    db.execute('UPDATE midias SET hash_midia = ? WHERE id = ?', (temp_hash, media_id))

conn.commit()
print("Hash_midia atualizado para itens blacklist (valores temporários)")

# Atualizar hashes apenas para itens não blacklist
hashes_updated = 0
for item in items:
    media_id, categoria, nome_normalizado, ano, old_hash, nome_da_midia, qualidade = item

    # Verificar se está em blacklist
    blacklist_check = db.execute('SELECT black_list FROM midias WHERE id = ?', (media_id,)).fetchone()
    if blacklist_check and blacklist_check[0] == 1:
        continue  # Pular itens em blacklist

    # Calcular novo hash sem qualidade
    nome_sem_qualidade = remove_quality_from_name(nome_normalizado)
    hash_input = f"{categoria}|{nome_sem_qualidade}|{ano or ''}"
    new_hash = hashlib.sha256(hash_input.encode()).hexdigest()

    # Atualizar hash
    db.execute('UPDATE midias SET hash_midia = ? WHERE id = ?', (new_hash, media_id))
    hashes_updated += 1

conn.commit()

print("\n" + "=" * 60)
print("Resumo:")
print(f"- Grupos processados: {processed_count}")
print(f"- Itens mantidos (melhor qualidade): {total_kept}")
print(f"- Itens marcados como duplicados: {total_to_blacklist}")
print(f"- Hashes atualizados: {len(items)}")

conn.close()
