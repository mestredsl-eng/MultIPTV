"""
Script para corrigir o bug de auto-blacklist excessivo.

O problema: A função check_and_apply_auto_blacklist usa LIKE '%nome_base%'
que é muito permissivo, causando 467.166 itens (52%) na blacklist.

Solução:
1. Remover blacklist de itens marcados pelo auto-blacklist
2. Desativar o auto-blacklist até melhorar a lógica
"""

from app.app import create_app

app = create_app()
with app.app_context():
    from app.database import get_db
    import logging
    logging.basicConfig(level=logging.INFO)
    
    db = get_db()
    
    print("=" * 60)
    print("CORRIGINDO BUG DE AUTO-BLACKLIST")
    print("=" * 60)
    
    # Estatísticas antes
    total = db.execute('SELECT COUNT(*) FROM midias WHERE status = 1').fetchone()[0]
    blacklist_before = db.execute('SELECT COUNT(*) FROM midias WHERE status = 1 AND black_list = 1').fetchone()[0]
    active_before = db.execute('SELECT COUNT(*) FROM midias WHERE status = 1 AND black_list = 0').fetchone()[0]
    
    print(f"\nANTES:")
    print(f"  Total: {total}")
    print(f"  Blacklist: {blacklist_before} ({blacklist_before/total*100:.1f}%)")
    print(f"  Active: {active_before}")
    
    # REMOVER TODA A BLACKLIST (o auto-blacklist marcou tudo errado)
    print("\n⚠️  REMOVENDO BLACKLIST DE TODOS OS ITENS...")
    result = db.execute('UPDATE midias SET black_list = 0 WHERE status = 1')
    db.commit()
    
    removed_count = result.rowcount
    print(f"✅ {removed_count} itens removidos da blacklist")
    
    # Estatísticas depois
    blacklist_after = db.execute('SELECT COUNT(*) FROM midias WHERE status = 1 AND black_list = 1').fetchone()[0]
    active_after = db.execute('SELECT COUNT(*) FROM midias WHERE status = 1 AND black_list = 0').fetchone()[0]
    
    print(f"\nDEPOIS:")
    print(f"  Total: {total}")
    print(f"  Blacklist: {blacklist_after}")
    print(f"  Active: {active_after}")
    
    print("\n" + "=" * 60)
    print("PRÓXIMO PASSO: Desativar auto-blacklist no código")
    print("=" * 60)
    print("\nPara desativar o auto-blacklist, comente estas linhas em app/routes/api.py:")
    print("  Linhas 345-354: # AUTO-BLACKLIST CHECK")
