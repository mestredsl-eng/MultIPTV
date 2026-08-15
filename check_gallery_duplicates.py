import os
from collections import defaultdict
from pathlib import Path

galeria_path = 'D:/Galeria'

print("Analisando duplicados na galeria...")
print("=" * 60)

# Contar arquivos por nome
file_counts = defaultdict(list)
total_files = 0

for root, dirs, files in os.walk(galeria_path):
    for file in files:
        total_files += 1
        full_path = os.path.join(root, file)
        file_counts[file].append(full_path)

print(f"Total de arquivos na galeria: {total_files}")

# Encontrar duplicados (arquivos com mesmo nome em locais diferentes)
duplicates = {name: paths for name, paths in file_counts.items() if len(paths) > 1}

print(f"\nTotal de arquivos duplicados (mesmo nome): {len(duplicates)}")
print(f"Total de ocorrências duplicadas: {sum(len(paths) for paths in duplicates.values())}")

# Mostrar exemplos de duplicados
print("\nExemplos de duplicados (primeiros 20):")
count = 0
for name, paths in sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True):
    if count >= 20:
        break
    print(f"\nArquivo: {name}")
    print(f"  Ocorrências: {len(paths)}")
    for path in paths[:5]:  # Mostrar até 5 caminhos
        print(f"    - {path}")
    if len(paths) > 5:
        print(f"    ... e mais {len(paths) - 5} ocorrências")
    count += 1

# Contar por extensão
ext_counts = defaultdict(int)
for file in file_counts.keys():
    ext = os.path.splitext(file)[1].lower()
    ext_counts[ext] += 1

print("\nDistribuição por extensão:")
for ext, count in sorted(ext_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"  {ext}: {count}")

# Verificar duplicados por hash_midia (se possível)
print("\nVerificando duplicados por conteúdo (hash)...")
hash_counts = defaultdict(list)

# Apenas para arquivos .strm (que contêm URLs)
for root, dirs, files in os.walk(galeria_path):
    for file in files:
        if file.endswith('.strm'):
            full_path = os.path.join(root, file)
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    hash_counts[content].append(full_path)
            except Exception as e:
                pass

# Encontrar duplicados por conteúdo
content_duplicates = {content: paths for content, paths in hash_counts.items() if len(paths) > 1}

print(f"Total de arquivos .strm duplicados por conteúdo: {len(content_duplicates)}")
print(f"Total de ocorrências duplicadas por conteúdo: {sum(len(paths) for paths in content_duplicates.values())}")

print("\nExemplos de duplicados por conteúdo (primeiros 10):")
count = 0
for content, paths in sorted(content_duplicates.items(), key=lambda x: len(x[1]), reverse=True):
    if count >= 10:
        break
    print(f"\nConteúdo: {content[:50]}...")
    print(f"  Ocorrências: {len(paths)}")
    for path in paths[:3]:  # Mostrar até 3 caminhos
        print(f"    - {path}")
    if len(paths) > 3:
        print(f"    ... e mais {len(paths) - 3} ocorrências")
    count += 1
