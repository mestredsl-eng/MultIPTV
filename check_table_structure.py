from app.app import create_app

app = create_app()
with app.app_context():
    from app.database import get_db
    db = get_db()

    # Verificar estrutura da tabela midias
    table_info = db.execute("PRAGMA table_info(midias)").fetchall()

    print("Estrutura da tabela midias:")
    for col in table_info:
        print(f"  {col[1]} ({col[2]})")