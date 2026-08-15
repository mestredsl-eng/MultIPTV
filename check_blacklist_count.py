from app.app import create_app

app = create_app()
with app.app_context():
    from app.database import get_db
    db = get_db()
    total = db.execute('SELECT COUNT(*) FROM midias WHERE status = 1').fetchone()[0]
    blacklist = db.execute('SELECT COUNT(*) FROM midias WHERE status = 1 AND black_list = 1').fetchone()[0]
    active = db.execute('SELECT COUNT(*) FROM midias WHERE status = 1 AND black_list = 0').fetchone()[0]
    print(f'Total: {total}')
    print(f'Blacklist: {blacklist}')
    print(f'Active: {active}')
