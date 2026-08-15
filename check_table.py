from app.app import create_app

app = create_app()
ctx = app.app_context()
ctx.push()

from app.database import get_db
db = get_db()
cursor = db.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='category_corrections'")
result = cursor.fetchone()
print('Tabela category_corrections existe:', result is not None)

ctx.pop()
