from app.app import create_app

app = create_app()
ctx = app.app_context()
ctx.push()

from app.database import get_db
db = get_db()

# Create the category_corrections table
db.execute('''
    CREATE TABLE IF NOT EXISTS category_corrections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hash_midia TEXT,
        nome_normalizado TEXT NOT NULL,
        categoria_anterior TEXT NOT NULL,
        categoria_nova TEXT NOT NULL,
        data_correcao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        vezes_aplicada INTEGER DEFAULT 0,
        ultima_aplicacao TIMESTAMP,
        CONSTRAINT unique_correction UNIQUE (hash_midia, nome_normalizado)
    )
''')

# Create indexes
db.execute('CREATE INDEX IF NOT EXISTS idx_corrections_hash ON category_corrections(hash_midia)')
db.execute('CREATE INDEX IF NOT EXISTS idx_corrections_nome ON category_corrections(nome_normalizado)')
db.execute('CREATE INDEX IF NOT EXISTS idx_corrections_categoria ON category_corrections(categoria_nova)')
db.execute('CREATE INDEX IF NOT EXISTS idx_corrections_data ON category_corrections(data_correcao)')

db.commit()
print('Tabela category_corrections criada com sucesso!')

ctx.pop()
