"""Test script for blacklist duplicates lowest quality feature."""

from app.app import create_app

# Create app context
app = create_app()
with app.app_context():
    from app.database import get_db
    from app.services.maintenance import MaintenanceService
    
    print("TESTE: Blacklist Duplicatas (Menor Qualidade)")
    print("=" * 60)
    
    service = MaintenanceService()
    db = get_db()
    
    # Get current statistics
    total_midias = db.execute('SELECT COUNT(*) FROM midias WHERE status = 1 AND black_list = 0').fetchone()[0]
    print(f"Total de mídias ativas (sem blacklist): {total_midias}")
    
    # Check for potential duplicates by normalized name
    from app.services.parser import remove_quality_from_name
    import re
    
    def get_base_name(nome):
        """Remove qualidade e ano do nome para comparação."""
        base = remove_quality_from_name(nome)
        base = re.sub(r'[\(\[\{]?\d{4}[\)\]\}]?', '', base)
        base = re.sub(r'\s+', ' ', base).strip()
        return base.lower()
    
    media_items = db.execute('''
        SELECT id, nome_da_midia, qualidade
        FROM midias
        WHERE status = 1 AND black_list = 0
    ''').fetchall()
    
    groups = {}
    for media in media_items:
        base_name = get_base_name(media['nome_da_midia'])
        if base_name not in groups:
            groups[base_name] = []
        groups[base_name].append({
            'id': media['id'],
            'nome': media['nome_da_midia'],
            'qualidade': media['qualidade']
        })
    
    duplicate_groups = {k: v for k, v in groups.items() if len(v) > 1}
    print(f"Grupos de duplicatas encontrados: {len(duplicate_groups)}")
    
    if len(duplicate_groups) > 0:
        print("\nExemplos de duplicatas (primeiros 5 grupos):")
        count = 0
        for base_name, group in duplicate_groups.items():
            if count >= 5:
                break
            print(f"\nNome base: {base_name}")
            for item in group:
                print(f"  - ID: {item['id']}, Nome: {item['nome'][:50]}, Qualidade: {item['qualidade'] or 'N/A'}")
            count += 1
    
    print("\n" + "=" * 60)
    print("Deseja executar o blacklist de duplicatas? (s/n)")
    
    # For automated testing, just show the analysis
    print("\nAnálise concluída. Execute a função através da interface web para aplicar as mudanças.")
