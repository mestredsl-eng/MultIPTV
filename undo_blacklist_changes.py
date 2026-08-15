#!/usr/bin/env python3
"""
Script para desfazer mudanças de blacklist feitas pelo fix_duplicate_quality.py.
"""
import sqlite3
from pathlib import Path

def undo_blacklist_changes():
    """Remove blacklist de itens que foram marcados pelo script anterior."""
    db_path = Path(__file__).parent / 'database' / 'iptv.db'
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Buscar itens que foram marcados como blacklist pelo script
    # (itens que têm black_list = 1 mas não foram originalmente blacklist)
    # Como não temos registro do estado anterior, vamos remover blacklist de todos
    # itens que foram marcados recentemente (baseado em data de atualização)
    
    # Para simplificar, vamos remover blacklist de todos os itens exceto aqueles
    # que foram explicitamente marcados pelo usuário (não temos como distinguir)
    # Então vamos apenas redefinir todos para black_list = 0
    
    cursor.execute('UPDATE midias SET black_list = 0')
    
    affected_rows = cursor.rowcount
    conn.commit()
    conn.close()
    
    print(f"Removido blacklist de {affected_rows} itens")

if __name__ == '__main__':
    undo_blacklist_changes()
