"""Add manual_category flag to midias table."""

def upgrade(db):
    """Add manual_category column to midias table."""
    db.execute('''
        ALTER TABLE midias ADD COLUMN categoria_manual BOOLEAN DEFAULT 0
    ''')
    db.commit()

def downgrade(db):
    """Remove manual_category column from midias table."""
    # SQLite doesn't support DROP COLUMN directly, so we need to recreate the table
    db.execute('''
        CREATE TABLE midias_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            iptv_id INTEGER NOT NULL,
            nome_da_midia TEXT NOT NULL,
            nome_normalizado TEXT NOT NULL,
            url TEXT NOT NULL,
            local_da_galeria TEXT,
            qualidade TEXT,
            imagem_url TEXT,
            categoria TEXT NOT NULL,
            black_list BOOLEAN DEFAULT 0,
            status BOOLEAN DEFAULT 1,
            id_externo TEXT,
            hash_midia TEXT NOT NULL,
            origem_iptv TEXT,
            ano INTEGER,
            season INTEGER,
            episode INTEGER,
            tmdb_id INTEGER,
            data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_processamento TIMESTAMP,
            ultima_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (iptv_id) REFERENCES iptvs(id) ON DELETE CASCADE,
            CONSTRAINT unique_hash UNIQUE (hash_midia)
        )
    ''')
    
    db.execute('''
        INSERT INTO midias_new (
            id, iptv_id, nome_da_midia, nome_normalizado, url, local_da_galeria,
            qualidade, imagem_url, categoria, black_list, status, id_externo,
            hash_midia, origem_iptv, ano, season, episode, tmdb_id,
            data_coleta, data_processamento, ultima_atualizacao
        )
        SELECT 
            id, iptv_id, nome_da_midia, nome_normalizado, url, local_da_galeria,
            qualidade, imagem_url, categoria, black_list, status, id_externo,
            hash_midia, origem_iptv, ano, season, episode, tmdb_id,
            data_coleta, data_processamento, ultima_atualizacao
        FROM midias
    ''')
    
    db.execute('DROP TABLE midias')
    db.execute('ALTER TABLE midias_new RENAME TO midias')
    
    # Recreate indexes
    db.execute('CREATE INDEX IF NOT EXISTS idx_midias_categoria ON midias(categoria)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_midias_tmdb ON midias(tmdb_id)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_midias_blacklist ON midias(black_list)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_midias_status ON midias(status)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_midias_nome_normalizado ON midias(nome_normalizado)')
    
    db.commit()
