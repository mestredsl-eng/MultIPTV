# Correções de Classificação e Gerenciamento IPTV

## Visão Geral

Este documento descreve as correções implementadas para resolver problemas de classificação de mídias (séries caindo em filmes) e melhorias no gerenciamento de fontes IPTV.

## Problemas Identificados

### 1. Séries Classificadas como Filmes

**Sintoma**: Séries com padrão S01E01 estavam sendo classificadas como "Movie" em vez de "Series".

**Causa Raiz**:
- O `classifier.py` só verificava padrão S01E01 no nome
- Se não tinha esse padrão, caía como "Movie" por padrão
- **Análise revelou**: As fontes IPTV classificam ERRADO no group-title

**Evidência**:
Analisamos 4 fontes M3U diferentes e confirmamos que as fontes classificam errado:
- "Resident Alien S03e01..." → group-title="Filmes | [XXX] Adultos" (ERRADO!)
- "XXX.The.Gilded.Age.S02e01..." → group-title="XXX - Adultos" (ERRADO!)
- Porém: "Deep In (2026) [L] S01E01" → group-title="Series | Dorama" (CORRETO)

**Conclusão**: O padrão S01E01 no nome é mais confiável que o group-title.

### 2. TMDB Superficial

**Sintoma**: Para nomes curtos como "homem", o TMDB retornava resultados incorretos (ex: "Homem Aranha 2026").

**Causa Raiz**:
- O `get_movie_info` sempre buscava filmes (`/search/movie`), nunca séries
- Não verificava a categoria original antes de buscar
- Sem filtro de ano para reduzir falsos positivos

### 3. Risco de Duplicação

**Sintoma**: Ao pular novamente, poderia trazer "homem" novamente e criar duplicata.

**Causa Raiz**:
- Aplicar correção TMDB podia criar duplicata se não houvesse verificação adequada
- Não verificava se o tipo encontrado batia com a categoria original

### 4. Remoção Incompleta de IPTV

**Sintoma**: Ao remover uma IPTV, dizia que apagou mas não apagava.

**Causa Raiz**:
- A função `delete_iptv` estava fazendo "soft delete" (apenas `ativo = 0`)
- Não removia mídias do banco de dados
- Não removia arquivos .strm da galeria

## Soluções Implementadas

### 1. Classificação Inteligente

**Arquivo**: `app/services/classifier.py`

**Mudanças**:
- Adicionada função `is_series_by_group_title()` para verificar keywords no group-title
- **Prioridade**: padrão S01E01 no nome > group-title > padrão Movie
- Keywords no group-title: "series", "séries", "seriados", "show", "sitcom", "drama", "temporada", "episódio", etc.

**Código**:
```python
def classify_media(entry):
    # ... outras verificações ...
    
    # Series (PRIORITY: name pattern first, then group-title)
    if is_series(name):
        return 'Series'
    
    # If no S01E01 pattern, check group-title as fallback
    if is_series_by_group_title(group_title):
        return 'Series'
    
    # Movies (default)
    return 'Movie'

def is_series_by_group_title(group_title):
    """Check if group-title indicates series content."""
    if not group_title:
        return False
    
    series_keywords = [
        'series', 'séries', 'seriados', 'show', 'sitcom', 'drama',
        'temporada', 'temporadas', 'episódio', 'episodio', 'episode'
    ]
    
    return any(keyword in group_title for keyword in series_keywords)
```

**Impacto**: Séries agora são classificadas corretamente mesmo quando group-title está errado.

### 2. TMDB Inteligente

**Arquivo**: `app/services/tmdb.py`

**Mudanças**:
- Adicionado parâmetro `categoria` para determinar tipo de busca
- Se categoria for Series/Novela/Cartoon → busca em `/search/tv`
- Se categoria for Movie/Adult → busca em `/search/movie`
- **Match exato de ano**: Se ano fornecido, tenta encontrar resultado com ano exato
- Verificação de tipo: Valida se tipo encontrado bate com categoria esperada

**Código**:
```python
def get_movie_info(name, year=None, categoria=None):
    # Determine search type based on category
    search_type = 'tv' if categoria in ['Series', 'Novela', 'Cartoon'] else 'movie'
    
    # Add year filter if provided
    if year:
        if search_type == 'movie':
            params['year'] = year
        else:
            params['first_air_date_year'] = year
    
    # Choose endpoint based on search type
    endpoint = f"{TMDB_BASE_URL}/search/{search_type}"
    
    # If year was provided, try to find exact year match
    if year and len(data['results']) > 1:
        for result_item in data['results']:
            if search_type == 'movie':
                item_year = result_item.get('release_date', '')[:4]
            else:
                item_year = result_item.get('first_air_date', '')[:4]
            
            if item_year == str(year):
                media = result_item
                break
```

**Impacto**: TMDB agora é mais preciso, buscando no endpoint correto baseado na categoria.

### 3. Prevenção de Correções Incorretas

**Arquivo**: `app/services/tmdb_validator.py`

**Mudanças**:
- Adicionada verificação de tipo de mídia no validador
- Se TMDB retorna série mas categoria original é filme → não corrige nome
- Se TMDB retorna filme mas categoria original é série → não corrige nome
- Apenas atualiza tmdb_id e ano, mas mantém nome original

**Código**:
```python
# Verify media type matches category to prevent incorrect corrections
tmdb_media_type = tmdb_result.get('media_type', 'movie')
expected_type = 'tv' if item['categoria'] in ['Series', 'Novela', 'Cartoon'] else 'movie'

if tmdb_media_type != expected_type:
    logger.warning(f"Media type mismatch: '{item['nome_da_midia']}' category '{item['categoria']}' but TMDB found as '{tmdb_media_type}' - skipping correction")
    # Still update TMDB info but don't correct name
    db.execute('''
        UPDATE midias
        SET tmdb_id = ?, ano = ?, ultima_atualizacao = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (tmdb_result['tmdb_id'], tmdb_result['year'], item['id']))
```

**Impacto**: Menos correções erradas e menos duplicatas no sistema.

### 4. Remoção Completa de IPTV

**Arquivo**: `app/database/queries.py`

**Mudanças**:
- Alterado para "hard delete" - remove completamente do banco de dados
- Remove todas as mídias associadas da tabela `midias`
- Remove arquivos .strm da galeria usando função `generate_file_path`
- Feedback detalhado ao usuário com contagem de mídias e arquivos removidos

**Código**:
```python
def delete_iptv(iptv_id):
    """Hard delete IPTV source and associated media (database and gallery files)."""
    # Get all media items from this IPTV before deletion
    media_items = db.execute('SELECT * FROM midias WHERE iptv_id = ?', (iptv_id,)).fetchall()
    
    # Remove .strm files from gallery
    galeria_path = Path(get_galeria_path())
    files_removed = 0
    
    for media in media_items:
        media_dict = {
            'categoria': media['categoria'],
            'nome_da_midia': media['nome'],
            'ano': media['ano']
        }
        
        strm_file = generate_file_path(media_dict)
        
        if strm_file.exists():
            strm_file.unlink()
            files_removed += 1
    
    # Delete associated media items from database
    db.execute('DELETE FROM midias WHERE iptv_id = ?', (iptv_id,))
    
    # Delete the IPTV source from database
    db.execute('DELETE FROM iptvs WHERE id = ?', (iptv_id,))
    
    db.commit()
    
    return {
        'media_count': media_count['count'] if media_count else 0,
        'files_removed': files_removed
    }
```

**Impacto**: Agora ao remover uma IPTV, ela é completamente limpa: banco de dados + galeria.

### 5. Teste de Conexão IPTV

**Arquivos**: `app/routes/api.py`, `app/templates/registration.html`

**Mudanças**:
- Adicionado botão "Testar" para cada IPTV na página de cadastro
- Testa até 5 mídias ativas da IPTV usando requests (HEAD request)
- Calcula taxa de sucesso e determina status (online/offline)
- Atualiza timestamp de última atualização
- Feedback visual com badge colorido e estatísticas

**Código**:
```python
@bp.route('/iptv/sources/<int:iptv_id>/test-connection', methods=['POST'])
def test_iptv_connection(iptv_id):
    # Get IPTV source info
    iptv = db.execute('SELECT * FROM iptvs WHERE id = ?', (iptv_id,)).fetchone()
    
    # Get a sample of active media from this IPTV
    media_samples = db.execute(
        'SELECT url FROM midias WHERE iptv_id = ? AND status = 1 AND black_list = 0 LIMIT 5',
        (iptv_id,)
    ).fetchall()
    
    # Test each media URL
    for media in media_samples:
        response = requests.head(url, timeout=10, allow_redirects=True)
        
        if response.status_code in [200, 206, 302, 301]:
            success_count += 1
    
    # Determine overall status
    success_rate = (success_count / tested_count) * 100 if tested_count > 0 else 0
    
    return jsonify({
        'success': True,
        'status': 'online' if success_rate > 50 else 'offline',
        'tested_count': tested_count,
        'success_count': success_count,
        'success_rate': success_rate,
        'message': f'{success_count}/{tested_count} mídias acessíveis ({success_rate:.1f}%)'
    })
```

**Impacto**: Usuário pode verificar se IPTVs estão funcionando em tempo real.

## Padrões Encontrados nas Fontes M3U

### Variações de Séries
- "Resident Alien S03e01" (S maiúsculo, e minúsculo)
- "Deep In (2026) [L] S01E01" (padrão completo)
- "Elite S01 Elite - S01E01 - Bem-vindos" (com contexto)
- "A Nobreza do Amor (2026) S01E71" (novela com episódio alto)

### Classificação Incorreta nas Fontes
- "Resident Alien S03e01..." → group-title="Filmes | [XXX] Adultos" (ERRADO!)
- "XXX.The.Gilded.Age.S02e01..." → group-title="XXX - Adultos" (ERRADO!)
- Porém: "Deep In (2026) [L] S01E01" → group-title="Series | Dorama" (CORRETO)

### Conclusão
O padrão S01E01 no nome é mais confiável que o group-title, pois as fontes classificam errado.

## Compatibilidade e Atualizações

### Chamadas de get_movie_info Atualizadas
Todas as chamadas do `get_movie_info` foram atualizadas para passar o parâmetro `categoria`:
- `app/routes/api.py` - Endpoints de enriquecimento
- `app/services/tmdb_validator.py` - Validação TMDB
- `app/services/bulk_classifier.py` - Classificação em lote

### Tratamento de Erros JavaScript
Adicionado escape de aspas simples e duplas na página de cadastro para evitar erros quando nomes contêm aspas.

## Testes e Validação

### Análise de Fontes M3U
- Analisamos 4 fontes M3U diferentes
- Confirmado que fontes classificam errado no group-title
- Padrão S01E01 no nome é mais confiável

### Teste de Remoção
- Verificado que remoção agora deleta completamente
- Arquivos .strm são removidos da galeria
- Feedback detalhado ao usuário

### Teste de Conexão
- Botão de teste funciona corretamente
- Feedback visual claro com estatísticas
- Atualiza timestamp de última atualização

## Resumo

As correções implementadas resolveram os problemas principais:

1. **Classificação correta**: Séries não caem mais em filmes
2. **TMDB preciso**: Busca no endpoint correto baseado na categoria
3. **Prevenção de duplicatas**: Verifica tipo antes de corrigir
4. **Remoção completa**: IPTVs são completamente removidas
5. **Teste de conexão**: Usuário pode verificar IPTVs antes de usar

O sistema agora é mais robusto para lidar com múltiplas fontes IPTV com classificações inconsistentes.