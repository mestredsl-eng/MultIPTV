#!/usr/bin/env python3
"""
Script para remover duplicatas de nomes idênticos no banco de dados.
Mantém apenas uma cópia de cada mídia com o mesmo nome_da_midia.
"""
import sqlite3
from pathlib import Path

def clean_exact_duplicates():
    """Remove duplicatas de nomes idênticos, mantendo apenas uma cópia."""
    db_path = Path(__file__).parent / 'database' / 'iptv.db'
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Buscar todos os nomes que aparecem mais de uma vez
    cursor.execute('''
        SELECT nome_da_midia, COUNT(*) as count
        FROM midias
        GROUP BY nome_da_midia
        HAVING count > 1
        ORDER BY count DESC
    ''')
    
    duplicate_names = cursor.fetchall()
    
    print(f"Encontrados {len(duplicate_names)} nomes duplicados...")
    
    total_removed = 0
    
    for nome, count in duplicate_names:
        # Buscar todos os registros com esse nome
        cursor.execute('''
            SELECT id, nome_da_midia, black_list, url, categoria
            FROM midias
            WHERE nome_da_midia = ?
            ORDER BY black_list ASC, id ASC
        ''', (nome,))
        
        items = cursor.fetchall()
        
        if len(items) <= 1:
            continue
        
        print(f"\n--- Duplicata: {nome} ({count} cópias) ---")
        
        # Manter o primeiro (prioridade: não blacklist, depois menor ID)
        keep_item = items[0]
        remove_items = items[1:]
        
        print(f"Mantendo: ID={keep_item[0]}, blacklist={keep_item[2]}")
        
        for item in remove_items:
            print(f"  Removendo: ID={item[0]}, blacklist={item[2]}")
            # Remover o duplicado
            cursor.execute('DELETE FROM midias WHERE id = ?', (item[0],))
            total_removed += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n=== Resumo ===")
    print(f"Nomes duplicados encontrados: {len(duplicate_names)}")
    print(f"Registros removidos: {total_removed}")

if __name__ == '__main__':
    clean_exact_duplicates()
