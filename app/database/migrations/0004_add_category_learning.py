"""Add category learning table to track manual category corrections."""

def upgrade(db):
    """Add category_corrections table to learn from user corrections."""
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
    
    # Create indexes for efficient lookups
    db.execute('CREATE INDEX IF NOT EXISTS idx_corrections_hash ON category_corrections(hash_midia)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_corrections_nome ON category_corrections(nome_normalizado)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_corrections_categoria ON category_corrections(categoria_nova)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_corrections_data ON category_corrections(data_correcao)')
    
    db.commit()


def downgrade(db):
    """Remove category_corrections table."""
    db.execute('DROP TABLE IF EXISTS category_corrections')
    db.commit()
