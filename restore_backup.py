import shutil
from pathlib import Path

# Paths
db_path = Path(__file__).parent.parent / 'database' / 'iptv.db'
backup_path = Path(__file__).parent.parent / 'backup' / 'iptv_20260605_1155.db'

print("RESTAURANDO BACKUP ANTES DA RECLASSIFICAÇÃO:")
print("=" * 60)
print(f"Backup: {backup_path}")
print(f"Destino: {db_path}")

# Stop Flask server if running
print("\nParando servidor Flask...")
import subprocess
try:
    subprocess.run(['Stop-Process', '-Id', '(Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue).OwningProcess', '-Force'], shell=True, capture_output=True)
except:
    pass

# Restore backup
print("\nRestaurando backup...")
shutil.copy(backup_path, db_path)

print("Backup restaurado com sucesso!")
print("\nReiniciando servidor Flask...")
