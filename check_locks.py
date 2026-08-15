"""Script para verificar e liberar locks presos no banco de dados."""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

DATABASE_PATH = Path(__file__).parent / 'database' / 'iptv.db'

print("VERIFICANDO LOCKS DO BANCO DE DADOS:")
print("=" * 60)

conn = sqlite3.connect(DATABASE_PATH)
db = conn.cursor()

# Verificar export_lock
print("\n1. EXPORT LOCK:")
print("-" * 60)
db.execute('SELECT * FROM export_lock')
lock = db.fetchone()
if lock:
    lock_id, locked, locked_since, locked_by, heartbeat = lock
    print(f"  ID: {lock_id}")
    print(f"  Locked: {locked}")
    print(f"  Locked Since: {locked_since}")
    print(f"  Locked By: {locked_by}")
    print(f"  Last Heartbeat: {heartbeat}")

    if locked:
        # Verificar se o lock está expirado
        if locked_since:
            lock_time = datetime.fromisoformat(locked_since) if isinstance(locked_since, str) else locked_since
            lock_age = datetime.now() - lock_time
            print(f"  Idade do lock: {lock_age}")

            if lock_age.total_seconds() > 3600:  # Mais de 1 hora
                print("  ⚠️  Lock expirado (mais de 1 hora)")
                response = input("  Deseja liberar o lock? (s/n): ")
                if response.lower() == 's':
                    db.execute('UPDATE export_lock SET locked = 0, locked_since = NULL, locked_by = NULL, ultimo_heartbeat = NULL WHERE id = 1')
                    conn.commit()
                    print("  ✅ Lock liberado!")
            else:
                print(f"  ✅ Lock ativo (idade: {lock_age})")
        else:
            print("  ⚠️  Lock ativo mas sem timestamp")
            response = input("  Deseja liberar o lock? (s/n): ")
            if response.lower() == 's':
                db.execute('UPDATE export_lock SET locked = 0, locked_since = NULL, locked_by = NULL, ultimo_heartbeat = NULL WHERE id = 1')
                conn.commit()
                print("  ✅ Lock liberado!")
    else:
        print("  ✅ Nenhum lock ativo")
else:
    print("  ⚠️  Nenhum registro de lock encontrado")

# Verificar process_status
print("\n2. PROCESS STATUS:")
print("-" * 60)
db.execute('SELECT * FROM process_status WHERE status = "running" ORDER BY id DESC LIMIT 5')
running_processes = db.fetchall()
if running_processes:
    print(f"  Processos em execução: {len(running_processes)}")
    for proc in running_processes:
        proc_id, etapa, progresso, mensagem, inicio, fim, status = proc
        print(f"    ID: {proc_id}, Etapa: {etapa}, Progresso: {progresso}%, Início: {inicio}")
else:
    print("  ✅ Nenhum processo em execução")

# Verificar fila_processamento
print("\n3. FILA DE PROCESSAMENTO:")
print("-" * 60)
db.execute('SELECT * FROM fila_processamento WHERE status = "running" ORDER BY id DESC LIMIT 5')
running_queue = db.fetchall()
if running_queue:
    print(f"  Itens na fila em execução: {len(running_queue)}")
    for item in running_queue:
        item_id, etapa, inicio, fim, status = item
        print(f"    ID: {item_id}, Etapa: {etapa}, Início: {inicio}")
else:
    print("  ✅ Nenhum item na fila em execução")

# Verificar execution_stats
print("\n4. EXECUTION STATS:")
print("-" * 60)
db.execute('SELECT * FROM execution_stats WHERE status = "running" ORDER BY id DESC LIMIT 5')
running_stats = db.fetchall()
if running_stats:
    print(f"  Execuções em andamento: {len(running_stats)}")
    for stat in running_stats:
        stat_id, tipo, inicio, fim, duracao, novos, ignorados, exportados, status = stat
        print(f"    ID: {stat_id}, Tipo: {tipo}, Início: {inicio}")
else:
    print("  ✅ Nenhuma execução em andamento")

print("\n" + "=" * 60)
print("Verificação concluída!")
print("\nSugestões:")
print("- Se há locks presos, use este script para liberá-los")
print("- Se há processos 'running' antigos, considere marcá-los como 'failed'")
print("- O erro 'database is locked' pode ser causado por múltiplas operações concorrentes")

conn.close()
