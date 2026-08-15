"""Script para limpar processos presos no banco de dados."""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

DATABASE_PATH = Path(__file__).parent / 'database' / 'iptv.db'

print("LIMPANDO PROCESSOS PRESOS:")
print("=" * 60)

conn = sqlite3.connect(DATABASE_PATH)
db = conn.cursor()

# Configuração: processos mais antigos que X horas são considerados presos
MAX_HOURS = 2  # Processos com mais de 2 horas são considerados presos

# Limpar process_status antigos
print("\n1. LIMPANDO PROCESS_STATUS:")
print("-" * 60)
db.execute('''
    SELECT id, etapa, inicio, status
    FROM process_status
    WHERE status = 'running'
    ORDER BY inicio
''')
running_processes = db.fetchall()

if running_processes:
    print(f"  Processos 'running' encontrados: {len(running_processes)}")
    for proc_id, etapa, inicio, status in running_processes:
        if inicio:
            try:
                proc_time = datetime.fromisoformat(inicio) if isinstance(inicio, str) else inicio
                age = datetime.now() - proc_time
                age_hours = age.total_seconds() / 3600

                print(f"    ID: {proc_id}, Etapa: {etapa}, Idade: {age_hours:.1f}h")

                if age_hours > MAX_HOURS:
                    print(f"      → Marcando como 'failed' (mais de {MAX_HOURS}h)")
                    db.execute('''
                        UPDATE process_status
                        SET fim = CURRENT_TIMESTAMP, status = 'failed'
                        WHERE id = ?
                    ''', (proc_id,))
                    conn.commit()
                    print(f"      ✅ Processo {proc_id} marcado como failed")
            except Exception as e:
                print(f"      ⚠️  Erro ao processar {proc_id}: {e}")
else:
    print("  ✅ Nenhum processo 'running' encontrado")

# Limpar fila_processamento antiga
print("\n2. LIMPANDO FILA_DE_PROCESSAMENTO:")
print("-" * 60)
db.execute('''
    SELECT id, etapa, inicio, status
    FROM fila_processamento
    WHERE status = 'running'
    ORDER BY inicio
''')
running_queue = db.fetchall()

if running_queue:
    print(f"  Itens 'running' na fila: {len(running_queue)}")
    for item_id, etapa, inicio, status in running_queue:
        if inicio:
            try:
                item_time = datetime.fromisoformat(inicio) if isinstance(inicio, str) else inicio
                age = datetime.now() - item_time
                age_hours = age.total_seconds() / 3600

                print(f"    ID: {item_id}, Etapa: {etapa}, Idade: {age_hours:.1f}h")

                if age_hours > MAX_HOURS:
                    print(f"      → Marcando como 'failed' (mais de {MAX_HOURS}h)")
                    db.execute('''
                        UPDATE fila_processamento
                        SET fim = CURRENT_TIMESTAMP, status = 'failed'
                        WHERE id = ?
                    ''', (item_id,))
                    conn.commit()
                    print(f"      ✅ Item {item_id} marcado como failed")
            except Exception as e:
                print(f"      ⚠️  Erro ao processar {item_id}: {e}")
else:
    print("  ✅ Nenhum item 'running' na fila")

# Limpar execution_stats antigos
print("\n3. LIMPANDO EXECUTION_STATS:")
print("-" * 60)
db.execute('''
    SELECT id, tipo_execucao, inicio, status
    FROM execution_stats
    WHERE status = 'running'
    ORDER BY inicio
''')
running_stats = db.fetchall()

if running_stats:
    print(f"  Execuções 'running': {len(running_stats)}")
    for stat_id, tipo, inicio, status in running_stats:
        if inicio:
            try:
                stat_time = datetime.fromisoformat(inicio) if isinstance(inicio, str) else inicio
                age = datetime.now() - stat_time
                age_hours = age.total_seconds() / 3600

                print(f"    ID: {stat_id}, Tipo: {tipo}, Idade: {age_hours:.1f}h")

                if age_hours > MAX_HOURS:
                    print(f"      → Marcando como 'failed' (mais de {MAX_HOURS}h)")
                    db.execute('''
                        UPDATE execution_stats
                        SET fim = CURRENT_TIMESTAMP, status = 'failed'
                        WHERE id = ?
                    ''', (stat_id,))
                    conn.commit()
                    print(f"      ✅ Execução {stat_id} marcada como failed")
            except Exception as e:
                print(f"      ⚠️  Erro ao processar {stat_id}: {e}")
else:
    print("  ✅ Nenhuma execução 'running' encontrada")

# Verificar resultado final
print("\n" + "=" * 60)
print("Limpeza concluída!")
print("\nVerificando estado final:")
print("-" * 60)

db.execute('SELECT COUNT(*) FROM process_status WHERE status = "running"')
proc_count = db.fetchone()[0]
print(f"  Processos 'running' restantes: {proc_count}")

db.execute('SELECT COUNT(*) FROM fila_processamento WHERE status = "running"')
queue_count = db.fetchone()[0]
print(f"  Itens 'running' na fila restantes: {queue_count}")

db.execute('SELECT COUNT(*) FROM execution_stats WHERE status = "running"')
stats_count = db.fetchone()[0]
print(f"  Execuções 'running' restantes: {stats_count}")

conn.close()
print("\n✅ Banco de dados limpo com sucesso!")
