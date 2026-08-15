from app.app import create_app

# Create app context
app = create_app()
with app.app_context():
    from app.database import get_db
    db = get_db()
    
    print("=" * 80)
    print("RELATÓRIO FINAL - RECLASSIFICAÇÃO INTELIGENTE")
    print("=" * 80)
    print()
    
    # Get audit statistics
    audit_stats = db.execute('''
        SELECT 
            COUNT(*) as total_changed,
            COUNT(DISTINCT media_id) as unique_media,
            AVG(confidence) as avg_confidence,
            MIN(confidence) as min_confidence,
            MAX(confidence) as max_confidence
        FROM classification_audit
    ''').fetchone()
    
    print("ESTATÍSTICAS GERAIS:")
    print(f"  Total de Alterações: {audit_stats['total_changed']}")
    print(f"  Mídias Únicas Alteradas: {audit_stats['unique_media']}")
    print(f"  Confiança Média: {audit_stats['avg_confidence']:.2f}%")
    print(f"  Confiança Mínima: {audit_stats['min_confidence']:.2f}%")
    print(f"  Confiança Máxima: {audit_stats['max_confidence']:.2f}%")
    print()
    
    # Get changes by category
    changes_by_category = db.execute('''
        SELECT categoria_nova, COUNT(*) as count
        FROM classification_audit
        GROUP BY categoria_nova
        ORDER BY count DESC
    ''').fetchall()
    
    print("ALTERAÇÕES POR CATEGORIA:")
    for cat in changes_by_category:
        print(f"  {cat['categoria_nova']}: {cat['count']}")
    print()
    
    # Get categories before and after
    categories_before = db.execute('''
        SELECT categoria, COUNT(*) as count
        FROM midias
        WHERE status = 1
        GROUP BY categoria
        ORDER BY count DESC
    ''').fetchall()
    
    print("CATEGORIAS ATUAIS (APÓS RECLASSIFICAÇÃO):")
    for cat in categories_before:
        print(f"  {cat['categoria']}: {cat['count']}")
    print()
    
    # Get execution stats
    exec_stats = db.execute('''
        SELECT tipo_execucao, inicio, fim, duracao_segundos, itens_novos, itens_ignorados, status
        FROM execution_stats
        WHERE tipo_execucao = 'reclassify'
        ORDER BY inicio DESC
        LIMIT 1
    ''').fetchone()
    
    if exec_stats:
        print("ESTATÍSTICAS DE EXECUÇÃO:")
        print(f"  Tipo: {exec_stats['tipo_execucao']}")
        print(f"  Início: {exec_stats['inicio']}")
        print(f"  Fim: {exec_stats['fim']}")
        print(f"  Duração: {exec_stats['duracao_segundos']} segundos")
        print(f"  Itens Alterados: {exec_stats['itens_novos']}")
        print(f"  Itens Ignorados: {exec_stats['itens_ignorados']}")
        print(f"  Status: {exec_stats['status']}")
        print()
    
    # Get sample of recent changes
    recent_changes = db.execute('''
        SELECT 
            ca.media_id,
            m.nome_da_midia,
            ca.categoria_antiga,
            ca.categoria_nova,
            ca.confidence,
            ca.reason,
            ca.created_at
        FROM classification_audit ca
        JOIN midias m ON ca.media_id = m.id
        ORDER BY ca.created_at DESC
        LIMIT 10
    ''').fetchall()
    
    print("AMOSTRA DE ALTERAÇÕES RECENTES:")
    for change in recent_changes:
        print(f"  {change['nome_da_midia'][:60]}")
        print(f"    {change['categoria_antiga']} -> {change['categoria_nova']}")
        print(f"    Confiança: {change['confidence']:.2f}%")
        print(f"    Motivo: {change['reason']}")
        print()
    
    print("=" * 80)
