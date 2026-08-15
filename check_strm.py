from pathlib import Path

files = list(Path('d:/Galeria').rglob('*.strm'))
print(f'Total .strm files: {len(files)}')
if files:
    print(f'First file: {files[0]}')
    print(f'Content: {files[0].read_text()[:200]}')
