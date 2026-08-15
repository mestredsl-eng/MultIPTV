#!/usr/bin/env python
"""Script automatizado para executar exportação completa com monitoramento."""

import subprocess
import time
import requests
from pathlib import Path
import sys

def start_flask():
    """Inicia servidor Flask em background."""
    print("🚀 Iniciando servidor Flask...")
    process = subprocess.Popen(
        ['python', 'run.py'],
        cwd='C:/Users/mestr/OneDrive/Documentos/IPTV/mestre-IPTV',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(5)  # Aguarda servidor iniciar
    print("✅ Servidor Flask iniciado")
    return process

def start_export():
    """Inicia exportação via API."""
    print("📤 Iniciando exportação via API...")
    try:
        response = requests.post('http://localhost:5000/api/process/export', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ {data.get('message')}")
                return True
            else:
                print(f"❌ Erro: {data.get('error')}")
                return False
    except requests.exceptions.Timeout:
        print("⏳ Exportação iniciada (timeout normal - processo em background)")
        return True
    except Exception as e:
        print(f"❌ Erro ao iniciar exportação: {e}")
        return False

def monitor_log():
    """Monitora log de processo até completar."""
    log_path = Path('C:/Users/mestr/OneDrive/Documentos/IPTV/mestre-IPTV/app/logs/process.log')
    
    if not log_path.exists():
        print("❌ Log não encontrado")
        return False
    
    print(f"📊 Monitorando log: {log_path}")
    print("=" * 60)
    
    last_size = 0
    error_count = 0
    start_time = time.time()
    
    while True:
        try:
            current_size = log_path.stat().st_size
            
            if current_size > last_size:
                with open(log_path, 'r', encoding='utf-8') as f:
                    f.seek(last_size)
                    new_lines = f.readlines()
                
                for line in new_lines:
                    line = line.strip()
                    if 'ERROR' in line and 'Erro ao exportar' in line:
                        error_count += 1
                        if error_count <= 10:  # Mostra só os primeiros 10 erros
                            print(f"❌ {error_count}: {line}")
                    elif 'Exportação concluída' in line:
                        elapsed = time.time() - start_time
                        print(f"\n{'='*60}")
                        print(f"✅ EXPORTAÇÃO CONCLUÍDA")
                        print(f"⏱️  Tempo total: {elapsed:.0f} segundos ({elapsed/60:.1f} minutos)")
                        print(f"📊 Total de erros: {error_count}")
                        print(f"{'='*60}\n")
                        return True
                    elif 'TV M3U e EPG gerados' in line:
                        print(f"📺 {line}")
                
                last_size = current_size
            
            time.sleep(2)
            
            # Timeout de segurança (4 horas)
            if time.time() - start_time > 14400:
                print(f"\n⚠️  Timeout de segurança atingido (4 horas)")
                print(f"📊 Total de erros até agora: {error_count}")
                return False
                
        except Exception as e:
            print(f"⚠️  Erro ao monitorar log: {e}")
            time.sleep(2)

def main():
    """Executa fluxo completo."""
    try:
        # Iniciar Flask
        flask_process = start_flask()
        
        # Iniciar exportação
        if not start_export():
            return False
        
        # Monitorar log
        success = monitor_log()
        
        # Parar Flask
        print("🛑 Parando servidor Flask...")
        flask_process.terminate()
        flask_process.wait(timeout=5)
        
        return success
        
    except KeyboardInterrupt:
        print("\n⚠️  Processo interrompido pelo usuário")
        return False
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
