# TMDB Validation - Documentação Completa

## Visão Geral

O sistema de validação TMDB foi desenvolvido para garantir que filmes com nomes curtos (≤2 palavras) sejam corretamente identificados e validados antes da exportação. Este sistema inclui correção automática de nomes, deduplicação inteligente e blacklist automática para itens não encontrados.

### Objetivos

1. **Precisão**: Garantir que filmes com nomes ambíguos sejam corretamente identificados
2. **Qualidade**: Corrigir nomes automaticamente para o padrão oficial do TMDB
3. **Organização**: Remover duplicatas mantendo sempre a melhor qualidade
4. **Controle**: Bloquear exportação de filmes não validados
5. **Inteligência**: Busca no endpoint correto (filme vs série) baseado na categoria

## Melhorias Recentes (Atualização)

### TMDB Inteligente - Busca por Categoria

**Problema Anterior**: O `get_movie_info` sempre buscava filmes (`/search/movie`), nunca séries. Para nomes curtos como "homem", retornava resultados incorretos.

**Solução Implementada**:
- Adicionado parâmetro `categoria` para determinar tipo de busca
- Se categoria for Series/Novela/Cartoon → busca em `/search/tv`
- Se categoria for Movie/Adult → busca em `/search/movie`
- **Match exato de ano**: Se ano fornecido, tenta encontrar resultado com ano exato
- Verificação de tipo: Valida se tipo encontrado bate com categoria esperada

**Arquivos**:
- `app/services/tmdb.py` - Função `get_movie_info()` atualizada
- `app/services/tmdb_validator.py` - Chamadas atualizadas para passar categoria
- `app/routes/api.py` - Endpoints de enriquecimento atualizados

**Impacto**: TMDB agora é mais preciso, buscando no endpoint correto baseado na categoria.

### Prevenção de Correções Incorretas

**Problema Anterior**: Risco de duplicação ao pular novamente, pois correções TMDB podiam criar duplicatas.

**Solução Implementada**:
- Adicionada verificação de tipo de mídia no validador
- Se TMDB retorna série mas categoria original é filme → não corrige nome
- Se TMDB retorna filme mas categoria original é série → não corrige nome
- Apenas atualiza tmdb_id e ano, mas mantém nome original

**Arquivos**:
- `app/services/tmdb_validator.py` - Verificação de tipo adicionada

**Impacto**: Menos correções erradas e menos duplicatas no sistema.

## Regras de Validação

### Regra Principal
- **Filmes com ≤2 palavras** no nome precisam de validação TMDB
- **Apenas categoria 'Movie'** é afetada por esta regra
- **Exportação**: Bloqueia filmes não validados (mantém ativo no banco)
- **Validação**: Corrige nomes automaticamente se TMDB encontrar, dá blacklist se não encontrar

### Priorização de Validação
1. **1 palavra** = Máxima prioridade (ex: "Matrix", "Gladiator")
2. **2 palavras** = Alta prioridade (ex: "The Mask", "Pulp Fiction")
3. **3+ palavras** = Baixa prioridade (ex: "The Lord of the Rings")

### Categorias Afetadas
- ✅ **Movie** (Filmes) - Aplica regra de validação
- ❌ **Series** - Não afetada pela regra
- ❌ **TV** - Não afetada pela regra
- ❌ **Sports** - Não afetada pela regra
- ❌ **Outras categorias** - Não afetadas pela regra

## Comportamento de Exportação vs Validação

### Durante a Exportação
- **Apenas bloqueia a exportação, não dá blacklist**
- Se filme com ≤2 palavras não tiver ano TMDB: não é exportado
- Filme continua ativo no banco (`black_list = 0`, `status = 1`)
- Log: "Filme X bloqueado na exportação: necessita validação TMDB"
- Usuário pode validar depois e tentar exportar novamente

### Durante a Validação (Manutenção) - Falha
- **Pode dar blacklist automaticamente**
- Quando usuário clica em "Validar Nomes Curtos (TMDB)"
- Se após todas as tentativas o filme não for encontrado no TMDB
- Sistema marca como blacklist (`black_list = 1`)
- Log: "Filme X enviado para blacklist: não encontrado no TMDB após X tentativas"

### Durante a Validação (Manutenção) - Sucesso
- **Corrige nome automaticamente**
- Se TMDB encontrar a mídia com sucesso
- Atualiza `nome_da_midia` para nome oficial do TMDB
- Atualiza `nome_normalizado` baseado no novo nome
- **MANTÉM** `hash_midia` atual (não recalcula para evitar duplicatas)
- Log detalhado: "Nome corrigido: 'Matrix Edição Especial' → 'The Matrix' (tmdb_id: 603)"
- **Deduplicação inteligente pós-correção**:
  - Verifica se correção criou duplicata com outro filme
  - Se encontrar duplicata: manter melhor qualidade ([L] > 4K > FHD > HD > SD)
  - Se ambas validadas: manter melhor qualidade
  - Se apenas uma validada: manter a validada
  - Enviar pior qualidade/sem validação para blacklist
  - Log detalhado: "Duplicata detectada: Mantendo ID 123 (The Matrix [4K]), enviando ID 456 para blacklist (qualidade: HD)"

## Sistema de Correção Automática de Nomes

### Quando Corrige
- Sempre que o TMDB encontrar a mídia com sucesso
- Independente da diferença entre nomes
- Aplica a todas as validações bem-sucedidas

### Campos Atualizados
- `nome_da_midia` → nome oficial do TMDB
- `nome_normalizado` → nome normalizado do TMDB
- `tmdb_id` → ID do TMDB
- `ano` → Ano do TMDB
- `ultima_atualizacao` → Timestamp da correção

### Campos Mantidos
- `hash_midia` → **MANTÉM ATUAL** (não recalcula para evitar duplicatas)
- Todos os outros campos permanecem inalterados

### Exemplos de Correção
- "Matrix Edição Especial Remasterizada" → "The Matrix"
- "Matrix [4K] Remaster" → "The Matrix"
- "Gladiator - Director's Cut" → "Gladiator"
- "The Mask (1994)" → "The Mask" (ano já vai para campo `ano`)

### Log de Correção
```
Nome corrigido: 'Matrix Edição Especial' → 'The Matrix' (tmdb_id: 603)
Nome corrigido: 'Gladiator Director Cut' → 'Gladiator' (tmdb_id: 270)
```

## Sistema de Deduplicação Inteligente

### Momento da Deduplicação
1. **Durante validação** (após cada correção de nome)
   - Verifica se correção criou duplicata pelo novo nome
   - Aplica critério de qualidade imediatamente
   - Log detalhado da decisão

2. **Após validação completa** (varredura final)
   - Varredura em toda tabela `midias` (categoria Movie)
   - Busca duplicatas por `nome_normalizado`
   - Aplica critério de qualidade para cada grupo
   - Log resumido: "Deduplicação final: X duplicatas removidas"

### Critérios de Qualidade
```python
quality_order = {
    '[L]': 10,  # Lossless/Melhor
    '4K': 9,
    'FHD': 8,
    'HD': 7,
    'SD': 6,
    '': 5,  # Sem qualidade definida
}
```

### Lógica de Decisão

#### Caso 1: Apenas uma validada
- Manter a que tem validação TMDB (`tmdb_id IS NOT NULL`)
- Enviar a sem validação para blacklist (`black_list = 1`)
- Log: "Duplicata detectada: Mantendo ID 123 (The Matrix, tmdb_id: 603), enviando ID 456 para blacklist (sem validação)"

#### Caso 2: Ambas validadas
- Manter a de MELHOR QUALIDADE ([L] > 4K > FHD > HD > SD)
- Enviar a de pior qualidade para blacklist
- Log: "Duplicata detectada: Mantendo ID 123 (The Matrix [4K], qualidade: 4K), enviando ID 456 para blacklist (qualidade: HD)"

#### Caso 3: Nenhuma validada
- Manter a de melhor qualidade (padrão existente)
- Log: "Duplicata sem validação: Mantendo melhor qualidade ID 123, enviando ID 456 para blacklist"

### Exemplos de Deduplicação
```
Duplicata detectada: Mantendo ID 123 (The Matrix [4K]), enviando ID 456 para blacklist (qualidade: HD)
Duplicata detectada: Mantendo ID 789 (Gladiator, tmdb_id: 270), enviando ID 101 para blacklist (sem validação)
Deduplicação final: 15 duplicatas removidas
```

## API Endpoints

### POST /api/validation/validate-short-names
Inicia validação de filmes com ≤2 palavras (prioridade alta).

**Request Body**: Vazio

**Response**:
```json
{
  "success": true,
  "message": "Validação concluída: 150 validados, 12 não encontrados, 5 duplicatas removidas",
  "stats": {
    "total": 167,
    "validated": 150,
    "not_found": 12,
    "errors": 0,
    "corrected": 45,
    "deduplicated": 5
  }
}
```

### GET /api/validation/progress
Retorna progresso atual da validação.

**Response**:
```json
{
  "success": true,
  "progress": 65,
  "message": "Validando 108/167 itens...",
  "status": "running"
}
```

### POST /api/validation/blacklist-unvalidated
Envia para blacklist mídias não encontradas no TMDB.

**Request Body**: Vazio

**Response**:
```json
{
  "success": true,
  "message": "12 itens enviados para blacklist",
  "blacklisted": 12
}
```

### GET /api/validation/stats
Retorna estatísticas de validação.

**Response**:
```json
{
  "success": true,
  "stats": {
    "movies_total": 5000,
    "movies_needing_validation": 150,
    "movies_validated": 4850,
    "movies_not_found": 12
  }
}
```

## Interface de Manutenção

### Botões Disponíveis

#### Validar Nomes Curtos (TMDB)
- **Função**: Inicia validação de filmes com ≤2 palavras
- **Ícone**: 🎬 (film)
- **Cor**: Azul (btn-info)
- **Comportamento**:
  - Mostra confirmação antes de iniciar
  - Exibe modal de progresso em tempo real
  - Corrige nomes automaticamente
  - Remove duplicatas mantendo melhor qualidade
  - Envia não encontrados para blacklist

#### Blacklist Não Validados
- **Função**: Envia para blacklist filmes não encontrados no TMDB
- **Ícone**: 🛡️ (shield-x)
- **Cor**: Vermelho (btn-danger)
- **Comportamento**:
  - Mostra confirmação antes de executar
  - Marca como blacklist todos os filmes sem validação TMDB
  - Atualiza estatísticas automaticamente

### Estatísticas de Validação

#### Cards de Estatísticas
- **Total de Filmes**: Quantidade total de filmes no banco
- **Precisando Validação**: Filmes com ≤2 palavras sem ano TMDB
- **Validados**: Filmes com validação TMDB completa
- **Não Encontrados**: Filmes enviados para blacklist (não encontrados no TMDB)

### Atualização Automática
- Estatísticas são carregadas ao abrir a página de manutenção
- Atualizadas automaticamente após cada operação de validação
- Polling não implementado (atualização manual via botões)

## Exemplos de Uso

### Exemplo 1: Validação Bem-Sucedida
```
Filme: "Matrix" (1 palavra, sem ano)
1. Sistema busca no TMDB
2. Encontra: "The Matrix" (1999, tmdb_id: 603)
3. Corrige nome: "Matrix" → "The Matrix"
4. Atualiza: nome_da_midia, nome_normalizado, tmdb_id, ano
5. Verifica duplicatas: Nenhuma encontrada
6. Log: "Nome corrigido: 'Matrix' → 'The Matrix' (tmdb_id: 603)"
```

### Exemplo 2: Validação com Deduplicação
```
Filme 1: "Matrix [4K]" (corrigido para "The Matrix")
Filme 2: "Matrix [HD]" (corrigido para "The Matrix")

1. Ambos corrigidos para "The Matrix"
2. Sistema detecta duplicata pelo nome_normalizado
3. Compara qualidade: 4K vs HD
4. Mantém Matrix [4K] (melhor qualidade)
5. Envia Matrix [HD] para blacklist
6. Log: "Duplicata detectada: Mantendo ID 123 (The Matrix [4K]), enviando ID 456 para blacklist (qualidade: HD)"
```

### Exemplo 3: Validação Falha
```
Filme: "FilmeInexistente123" (1 palavra, sem ano)
1. Sistema busca no TMDB com variações
2. Não encontrado após todas as tentativas
3. Marca como blacklist: black_list = 1
4. Log: "TMDB not found: 'FilmeInexistente123' - sent to blacklist"
```

### Exemplo 4: Exportação Bloqueada
```
Filme: "Test" (1 palavra, sem ano)
1. Usuário clica em "Exportar"
2. Sistema verifica regra de validação
3. Detecta: 1 palavra, sem ano TMDB
4. Bloqueia exportação
5. Filme permanece ativo no banco
6. Log: "Export blocked: 'Test' has 1 word(s) and no TMDB year. Requires TMDB validation."
```

## Troubleshooting

### Problema: Filmes não são validados
**Causa**: TMDB API Key não configurada
**Solução**: 
- Configure TMDB_API_KEY em Configurações ou .env
- Obtenha chave gratuita em https://www.themoviedb.org/settings/api

### Problema: Muitos filmes na blacklist
**Causa**: Validação muito agressiva ou TMDB retornando resultados incorretos
**Solução**:
- Verifique logs para entender razão dos blacklists
- Considere ajustar critérios de busca
- Use "Enriquecer TMDB" manual para casos específicos

### Problema: Nomes incorretamente corrigidos
**Causa**: TMDB retornando filme errado
**Solução**:
- Verifique se nome original era muito genérico
- Considere usar nome mais específico
- Correção manual via banco de dados se necessário

### Problema: Duplicatas não removidas
**Causa**: Critérios de qualidade não aplicados corretamente
**Solução**:
- Verifique se indicadores de qualidade estão sendo detectados
- Execute "Corrigir Duplicados" manualmente
- Verifique logs para entender decisões

### Problema: Exportação ainda bloqueada após validação
**Causa**: Validação não atualizou campo `ano` corretamente
**Solução**:
- Verifique se tmdb_id foi salvo corretamente
- Verifique se ano foi extraído do TMDB
- Execute validação novamente para filme específico

## Melhorias Futuras

1. **Whitelist Manual**: Sistema para marcar filmes específicos como "não enviar para blacklist"
2. **Undo Function**: Capacidade de reverter operações de blacklist
3. **Similaridade Score**: Sistema de pontuação para melhor precisão de busca TMDB
4. **Multiple TMDB Sources**: Integração com IMDB como fonte adicional
5. **Batch Validation**: Validação em lote com pausas para respeitar rate limits
6. **Preview Interface**: Interface para review de correções antes de aplicar