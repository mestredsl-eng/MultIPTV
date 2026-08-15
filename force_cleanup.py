"""Script simples para limpar processos presos de forma direta."""

import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).parent / 'database' / 'iptv.db'

print("LIMPANDO PROCESSOS PRESOS (MODO SIMPLES):")
print("=" * 60)

try:
    # Abrir banco com timeout maior
    conn = sqlite3.connect(DATABASE_PATH, timeout=60.0)
    db = conn.cursor()

    # Desabilitar sincronização temporariamente para operações rápidas
    db.execute('PRAGMA synchronous=OFF')

    print("\n1. Marcando process_status antigos como 'failed'...")
    db.execute('''
        UPDATE process_status
        SET status = 'failed', fim = CURRENT_TIMESTAMP
        WHERE status = 'running'
    ''')
    affected = db.rowcount
    print(f"   ✅ {affected} processos atualizados")

    print("\n2. Marcando fila_processamento antiga como 'failed'...")
    db.execute('''
        UPDATE fila_processamento
        SET status = 'failed', fim = CURRENT_TIMESTAMP
        WHERE status = 'running'
    ''')
    affected = db.rowcount
    print(f"   ✅ {affected} itens atualizados")

    print("\n3. Marcando execution_stats antigos como 'failed'...")
    db.execute('''
        UPDATE execution_stats
        SET status = 'failed', fim = CURRENT_TIMESTAMP
        WHERE status = 'running'
    ''')
    affected = db.rowcount
    print(f"   ✅ {affected} execuções atualizadas")

    # Reabilitar sincronização
    db.execute('PRAGMA synchronous=NORMAL')

    conn.commit()
    conn.close()

    print("\n" + "=" * 60)
    print("✅ Limpeza concluída com sucesso!")
    print("\nO banco de dados agora está limpo e pronto para operações.")

except sqlite3.OperationalError as e:
    print(f"\n❌ Erro de banco de dados: {e}")
    print("Sugestões:")
    print("- Feche todas as conexões ao banco de dados")
    print("- Pare o servidor web se estiver rodando")
    print("- Verifique se há outros processos acessando o banco")
except Exception as e:
    print(f"\n❌ Erro inesperado: {e}")
