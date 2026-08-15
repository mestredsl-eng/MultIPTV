#!/usr/bin/env python3
"""
Script para detectar duplicatas de mídia e marcar a pior qualidade como blacklist.
Recalcula hashes ignorando ano e qualidade, depois compara duplicatas.
"""
import sqlite3
import re
from pathlib import Path
from app.services.parser import calculate_hash_midia, remove_quality_from_name

def get_quality_score(nome):
    """Retorna pontuação de qualidade (maior = melhor)."""
    nome_lower = nome.lower()
    
    # Qualidades em ordem crescente de qualidade
    quality_scores = {
        'sd': 1,
        'dvdrip': 2,
        'hdtv': 3,
        'sdtv': 4,
        'web-dl': 5,
        'webdl': 5,
        'dvd': 6,
        'bdrip': 7,
        'brrip': 8,
        'bluray': 9,
        'hd': 10,
        'fhd': 11,
        '4k': 12,
        'hdr': 13,
    }
    
    max_score = 0
    for quality, score in quality_scores.items():
        if quality in nome_lower:
            max_score = max(max_score, score)
    
    # Se não tem indicador de qualidade, assume qualidade média
    if max_score == 0:
        max_score = 5
    
    # Penalidade por ter [L] (pior qualidade)
    if '[l]' in nome_lower:
        max_score = 0
    
    # Penalidade por ter ano no nome (considerado pior qualidade)
    if re.search(r'[\(\[]\d{4}[\)\]]', nome):
        max_score = max_score - 2  # Reduz score por ter ano
    
    return max_score

def recalculate_and_fix_duplicates():
    """Recalcula hashes e marca duplicatas de pior qualidade como blacklist."""
    db_path = Path(__file__).parent / 'database' / 'iptv.db'
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Buscar todas as mídias não blacklisted
    cursor.execute('''
        SELECT id, nome_da_midia, nome_normalizado, categoria, ano
        FROM midias
        WHERE black_list = 0
    ''')
    
    media_items = cursor.fetchall()
    
    print(f"Processando {len(media_items)} mídias...")
    
    # Dicionário para agrupar por novo hash
    hash_groups = {}
    
    for item in media_items:
        media_id, nome_da_midia, nome_normalizado, categoria, ano = item
        
        # Recalcular hash com nova lógica (ignora ano)
        new_hash = calculate_hash_midia(categoria, nome_normalizado, ano)
        
        if new_hash not in hash_groups:
            hash_groups[new_hash] = []
        
        hash_groups[new_hash].append({
            'id': media_id,
            'nome_da_midia': nome_da_midia,
            'nome_normalizado': nome_normalizado,
            'categoria': categoria,
            'ano': ano,
            'hash': new_hash
        })
    
    # Encontrar duplicatas
    duplicates = {h: items for h, items in hash_groups.items() if len(items) > 1}
    
    print(f"Encontrados {len(duplicates)} grupos de duplicatas...")
    
    # Para cada grupo de duplicatas, manter a melhor qualidade e marcar as outras
    blacklist_count = 0
    updated_hashes = []
    
    for hash_value, items in duplicates.items():
        print(f"\n--- Duplicata: {items[0]['nome_normalizado']} ---")
        
        # Ordenar por qualidade (melhor primeiro)
        items_sorted = sorted(items, key=lambda x: get_quality_score(x['nome_da_midia']), reverse=True)
        
        # Manter a primeira (melhor qualidade)
        best_item = items_sorted[0]
        print(f"Melhor qualidade: {best_item['nome_da_midia']} (score: {get_quality_score(best_item['nome_da_midia'])})")
        
        # Atualizar hash do melhor item (apenas se for diferente)
        cursor.execute('SELECT hash_midia FROM midias WHERE id = ?', (best_item['id'],))
        current_hash = cursor.fetchone()[0]
        if current_hash != hash_value:
            try:
                cursor.execute('UPDATE midias SET hash_midia = ? WHERE id = ?', (hash_value, best_item['id']))
                updated_hashes.append(best_item['id'])
            except sqlite3.IntegrityError:
                # Se o hash já existe, não atualiza
                print(f"  Aviso: Hash já existe, mantendo hash atual")
        
        # Marcar os outros como blacklist
        for item in items_sorted[1:]:
            quality_score = get_quality_score(item['nome_da_midia'])
            print(f"  Blacklist: {item['nome_da_midia']} (score: {quality_score})")
            cursor.execute('UPDATE midias SET black_list = 1 WHERE id = ?', (item['id'],))
            blacklist_count += 1
    
    # Atualizar hashes dos itens únicos também
    for hash_value, items in hash_groups.items():
        if len(items) == 1:
            item = items[0]
            cursor.execute('SELECT hash_midia FROM midias WHERE id = ?', (item['id'],))
            current_hash = cursor.fetchone()[0]
            if current_hash != hash_value:
                try:
                    cursor.execute('UPDATE midias SET hash_midia = ? WHERE id = ?', (hash_value, item['id']))
                    updated_hashes.append(item['id'])
                except sqlite3.IntegrityError:
                    # Se o hash já existe, não atualiza
                    pass
    
    conn.commit()
    conn.close()
    
    print(f"\n=== Resumo ===")
    print(f"Total de mídias processadas: {len(media_items)}")
    print(f"Grupos de duplicatas encontrados: {len(duplicates)}")
    print(f"Itens marcados como blacklist: {blacklist_count}")
    print(f"Hashes atualizados: {len(updated_hashes)}")

if __name__ == '__main__':
    recalculate_and_fix_duplicates()
