import os
import shutil
from pathlib import Path

galeria_path = 'D:/Galeria'

print("Limpando galeria completamente...")
print("=" * 60)

# Contar arquivos antes
total_files = 0
for root, dirs, files in os.walk(galeria_path):
    for file in files:
        total_files += 1

print(f"Total de arquivos antes da limpeza: {total_files}")

# Remover todos os arquivos .strm
removed_count = 0
for root, dirs, files in os.walk(galeria_path):
    for file in files:
        if file.endswith('.strm'):
            full_path = os.path.join(root, file)
            try:
                os.remove(full_path)
                removed_count += 1
            except Exception as e:
                print(f"Erro ao remover {full_path}: {e}")

print(f"Arquivos .strm removidos: {removed_count}")

# Remover diretórios vazios
removed_dirs = 0
for root, dirs, files in os.walk(galeria_path, topdown=False):
    for dir in dirs:
        dir_path = os.path.join(root, dir)
        try:
            if not os.listdir(dir_path):
                os.rmdir(dir_path)
                removed_dirs += 1
        except Exception as e:
            pass

print(f"Diretórios vazios removidos: {removed_dirs}")

# Contar arquivos depois
total_files_after = 0
for root, dirs, files in os.walk(galeria_path):
    for file in files:
        total_files_after += 1

print(f"Total de arquivos após limpeza: {total_files_after}")
print(f"Arquivos removidos: {total_files - total_files_after}")

print("\nGaleria limpa. Pronto para reexportação.")
