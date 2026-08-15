import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'database', 'iptv.db')

conn = sqlite3.connect(db_path)
db = conn.cursor()

print("Reiniciando blacklist e corrigindo por qualidade...")
print("=" * 60)

# Primeiro, remover blacklist de todos os itens ativos
db.execute('UPDATE midias SET black_list = 0 WHERE status = 1')
conn.commit()
print("Blacklist removido de todos os itens ativos")

# Definir ordem de qualidade (maior valor = melhor qualidade)
quality_order = {
    '[L]': 10,  # Lossless/Melhor
    '4K': 9,
    'FHD': 8,
    'HD': 7,
    'SD': 6,
    '': 5,  # Sem qualidade definida
}

def get_quality_score(qualidade, nome):
    """Retorna o score de qualidade. Maior = melhor."""
    # Primeiro verificar o campo qualidade
    if qualidade:
        # Verificar se tem [L] no nome
        if '[L]' in qualidade:
            return quality_order['[L]']

        # Verificar outras qualidades
        for q, score in quality_order.items():
            if q and q in qualidade.upper():
                return score
    
    # Se não tem qualidade definida, verificar no nome
    if nome:
        nome_upper = nome.upper()
        
        # Verificar [L] no nome
        if '[L]' in nome_upper:
            return quality_order['[L]']
        
        # Verificar outras qualidades no nome
        if '4K' in nome_upper:
            return quality_order['4K']
        if 'FHD' in nome_upper:
            return quality_order['FHD']
        if 'HD' in nome_upper:
            return quality_order['HD']
        if 'SD' in nome_upper:
            return quality_order['SD']
    
    return quality_order['']

# Buscar todas as mídias ativas
db.execute('''
    SELECT id, nome_da_midia, nome_normalizado, qualidade, black_list
    FROM midias
    WHERE status = 1
    ORDER BY nome_normalizado
''')
items = db.fetchall()

print(f"Total de mídias ativas: {len(items)}")

# Agrupar por nome normalizado
name_groups = {}
for item in items:
    media_id, nome, nome_normalizado, qualidade, black_list = item
    key = nome_normalizado or nome.lower()
    if key not in name_groups:
        name_groups[key] = []
    name_groups[key].append({
        'id': media_id,
        'nome': nome,
        'nome_normalizado': nome_normalizado,
        'qualidade': qualidade,
        'black_list': black_list,
        'quality_score': get_quality_score(qualidade, nome)
    })

print(f"Grupos de nomes únicos: {len(name_groups)}")

# Encontrar grupos com múltiplas qualidades
multi_quality_groups = {k: v for k, v in name_groups.items() if len(v) > 1}
print(f"Grupos com múltiplas qualidades: {len(multi_quality_groups)}")

# Processar cada grupo
total_to_blacklist = 0
total_kept = 0
processed_count = 0

for name, group in multi_quality_groups.items():
    # Ordenar por score de qualidade (decrescente)
    group.sort(key=lambda x: x['quality_score'], reverse=True)
    
    # Manter apenas o melhor
    best = group[0]
    others = group[1:]
    
    print(f"\nGrupo: {name}")
    print(f"  Mantendo (ID {best['id']}, Score {best['quality_score']}): {best['nome'][:60]}... [Qualidade: {best['qualidade']}]")
    total_kept += 1
    
    for item in others:
        print(f"  Marcando como duplicado (ID {item['id']}, Score {item['quality_score']}): {item['nome'][:60]}... [Qualidade: {item['qualidade']}]")
        db.execute('UPDATE midias SET black_list = 1 WHERE id = ?', (item['id'],))
        total_to_blacklist += 1
    
    processed_count += 1

conn.commit()

print("\n" + "=" * 60)
print("Resumo:")
print(f"- Grupos processados: {processed_count}")
print(f"- Itens mantidos (melhor qualidade): {total_kept}")
print(f"- Itens marcados como duplicados: {total_to_blacklist}")

conn.close()
