import requests
import hashlib
from pathlib import Path

url = "http://185.66.90.136/get.php?username=a90049896&password=112233Aa&type=m3u_plus"
cache_dir = Path(__file__).parent / 'cache'
cache_dir.mkdir(parents=True, exist_ok=True)

url_hash = hashlib.md5(url.encode()).hexdigest()
cache_file = cache_dir / f"{url_hash}.m3u"

print(f"Testando download de: {url}")
print(f"Cache file: {cache_file}")

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive'
}

try:
    print("Iniciando requisição HTTP...")
    response = requests.get(url, timeout=300, headers=headers)
    print(f"Status code: {response.status_code}")
    print(f"Content length: {len(response.text)}")
    
    cache_file.write_text(response.text, encoding='utf-8')
    print(f"Arquivo salvo: {cache_file}")
    print(f"Tamanho do arquivo: {cache_file.stat().st_size} bytes")
    print("Download concluído com sucesso!")
except Exception as e:
    print(f"Erro: {e}")
