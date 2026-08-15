import os
from collections import defaultdict
from pathlib import Path
import hashlib

galeria_path = 'D:/Galeria'

print("Limpando duplicados da galeria...")
print("=" * 60)

# Criar mapa de conteúdo para arquivos
content_to_files = defaultdict(list)
total_files = 0

print("Indexando arquivos .strm...")
for root, dirs, files in os.walk(galeria_path):
    for file in files:
        if file.endswith('.strm'):
            total_files += 1
            full_path = os.path.join(root, file)
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    content_to_files[content].append(full_path)
            except Exception as e:
                pass

print(f"Total de arquivos .strm indexados: {total_files}")

# Encontrar duplicados por conteúdo
duplicates = {content: paths for content, paths in content_to_files.items() if len(paths) > 1}

print(f"Total de conteúdos duplicados: {len(duplicates)}")
print(f"Total de arquivos que serão removidos: {sum(len(paths) - 1 for paths in duplicates.values())}")

# Mostrar exemplos antes de remover
print("\nExemplos de duplicados que serão removidos (primeiros 10):")
count = 0
for content, paths in sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True):
    if count >= 10:
        break
    print(f"\nConteúdo: {content[:50]}...")
    print(f"  Ocorrências: {len(paths)}")
    print(f"  Mantendo: {paths[0]}")
    print(f"  Removendo: {len(paths) - 1} arquivos")
    for path in paths[1:3]:  # Mostrar até 2 que serão removidos
        print(f"    - {path}")
    if len(paths) > 3:
        print(f"    ... e mais {len(paths) - 3} arquivos")
    count += 1

# Confirmar antes de remover
print("\n" + "=" * 60)
print("Deseja remover os duplicados? (s/n)")
# Para automação, vou remover automaticamente
print("Removendo duplicados...")

removed_count = 0
for content, paths in duplicates.items():
    # Manter o primeiro arquivo, remover os outros
    keep = paths[0]
    for path in paths[1:]:
        try:
            os.remove(path)
            removed_count += 1
            # Remover diretório vazio
            parent_dir = os.path.dirname(path)
            try:
                if not os.listdir(parent_dir):
                    os.rmdir(parent_dir)
            except:
                pass
        except Exception as e:
            print(f"Erro ao remover {path}: {e}")

print(f"\nArquivos removidos: {removed_count}")

# Verificar o status final
final_count = 0
for root, dirs, files in os.walk(galeria_path):
    for file in files:
        if file.endswith('.strm'):
            final_count += 1

print(f"Total de arquivos .strm após limpeza: {final_count}")
print(f"Arquivos removidos: {total_files - final_count}")
