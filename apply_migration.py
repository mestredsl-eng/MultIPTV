from app.app import create_app

# Create app context
app = create_app()
with app.app_context():
    from app.database import get_db
    db = get_db()
    
    # Read and execute migration
    with open('database/0003_create_classification_audit.sql', 'r') as f:
        sql = f.read()
    
    db.executescript(sql)
    db.commit()
    
    print('Tabela classification_audit criada com sucesso')
