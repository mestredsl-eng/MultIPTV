from app.app import create_app

# Create app context
app = create_app()
with app.app_context():
    from app.database import get_db
    db = get_db()
    
    print("VERIFICANDO TABELAS DE ATIVIDADE:")
    print("=" * 60)
    
    # Check if fila_processamento table exists
    tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    print("Tabelas no banco:")
    for table in tables:
        print(f"  - {table['name']}")
    
    print()
    
    # Check fila_processamento table
    if 'fila_processamento' in [t['name'] for t in tables]:
        fila_count = db.execute('SELECT COUNT(*) as count FROM fila_processamento').fetchone()
        print(f"Total de registros em fila_processamento: {fila_count['count']}")
        
        if fila_count['count'] > 0:
            recent = db.execute('SELECT * FROM fila_processamento ORDER BY inicio DESC LIMIT 5').fetchall()
            print("\nRegistros recentes:")
            for row in recent:
                print(f"  Etapa: {row['etapa']}, Início: {row['inicio']}, Fim: {row['fim']}, Status: {row['status']}")
    else:
        print("Tabela fila_processamento não existe")
    
    print()
    
    # Check process_status table
    if 'process_status' in [t['name'] for t in tables]:
        process_count = db.execute('SELECT COUNT(*) as count FROM process_status').fetchone()
        print(f"Total de registros em process_status: {process_count['count']}")
        
        if process_count['count'] > 0:
            recent = db.execute('SELECT * FROM process_status ORDER BY id DESC LIMIT 5').fetchall()
            print("\nRegistros recentes de process_status:")
            for row in recent:
                print(f"  Etapa: {row['etapa']}, Progresso: {row['progresso']}, Status: {row['status']}")
    else:
        print("Tabela process_status não existe")
