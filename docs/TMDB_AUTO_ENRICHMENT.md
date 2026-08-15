# Enriquecimento TMDB Automático

## Visão Geral
O sistema agora integra automaticamente o enriquecimento TMDB no fluxo de processamento principal, garantindo que filmes tenham o ano correto obtido da API TMDB para facilitar a identificação no Jellyfin.

## Funcionalidade

### Como Funciona
1. **Extração do Nome**: O ano é extraído do nome do arquivo como fallback
2. **Consulta TMDB**: Para filmes, o sistema consulta a API TMDB automaticamente
3. **Prioridade TMDB**: O ano do TMDB sobrescreve o ano extraído do nome
4. **Cache Inteligente**: Resultados do TMDB são cacheados por 30 dias (configurável)
5. **Fallback**: Se o TMDB falhar, usa o ano extraído do nome

### Benefícios
- **Identificação Precisa**: Ano correto da fonte oficial (TMDB)
- **Menos Erros**: Reduz erros de identificação de filmes com nomes iguais
- **Performance**: Cache reduz chamadas à API
- **Robustez**: Fallback garante que sempre há algum ano
- **Jellyfin Friendly**: Formato ideal para matching automático

## Novos Endpoints

### 1. Classificação com TMDB
`POST /api/process/classify-with-tmdb`

Classifica mídias com enriquecimento TMDB automático para filmes.

**Response**:
```json
{
  "success": true,
  "message": "Classificação concluída: 150 novas mídias, 200 ignoradas, 120 enriquecidas com TMDB"
}
```

### 2. Classificação Bulk com TMDB
`POST /api/process/classify-bulk-tmdb`

Classificação otimizada em lote com TMDB habilitado.

**Request**:
```json
{
  "batch_size": 500,
  "enable_tmdb": true
}
```

**Response**:
```json
{
  "success": true,
  "message": "Classificação concluída com enriquecimento TMDB: 150 novas mídias, 200 ignoradas"
}
```

## Exemplo Prático

### Processo de Enriquecimento

**Entrada**:
- Nome: "Frozen"
- Ano extraído: `null` (não tinha ano no nome)

**Processo**:
1. Sistema classifica como "Movie"
2. Consulta TMDB para "Frozen"
3. TMDB retorna: year="2013", tmdb_id=109439
4. Ano é atualizado para 2013
5. tmdb_id é salvo para referência

**Resultado**:
- Pasta: `D:/Galeria/FILMES/Frozen (2013)/`
- Arquivo: `D:/Galeria/FILMES/Frozen (2013)/Frozen (2013).strm`
- Banco: ano=2013, tmdb_id=109439

### Prioridade de Ano

```
TMDB Year > Ano Extraído do Nome > null
```

**Exemplo 1**:
- Nome: "Matrix (1999)"
- Ano extraído: 1999
- TMDB: 1999
- **Resultado**: 1999 (ambos iguais)

**Exemplo 2**:
- Nome: "Matrix"
- Ano extraído: `null`
- TMDB: 1999
- **Resultado**: 1999 (TMDB usado)

**Exemplo 3**:
- Nome: "Matrix (2020)"
- Ano extraído: 2020
- TMDB: 1999
- **Resultado**: 1999 (TMDB sobrescreve)

## Configuração

### TMDB API Key
A chave da API TMDB deve estar configurada:

```python
# Via interface web
# Menu > Configurações > TMDB API Key

# Ou direto no banco
UPDATE system_settings SET valor = 'sua_chave_aqui' WHERE chave = 'tmdb_api_key'
```

### Cache TMDB
Duração do cache configurável:

```python
# Via interface web
# Menu > Configurações > Tempo de Cache TMDB (segundos)

# Padrão: 2592000 (30 dias)
```

### Habilitar/Desabilitar TMDB
No bulk classifier:

```json
{
  "batch_size": 500,
  "enable_tmdb": false  // Desabilita TMDB
}
```

## Fluxo de Processamento

```
1. Download M3U
   ↓
2. Parse M3U
   ↓
3. Normalizar Nome
   ↓
4. Classificar Categoria
   ↓
5. Extrair Metadados (ano do nome como fallback)
   ↓
6. [Se Movie] Enriquecer com TMDB
   ↓
7. Calcular Hash (com ano final)
   ↓
8. Verificar Duplicados (hash)
   ↓
9. Inserir no Banco (com ano e tmdb_id)
   ↓
10. Exportar (com ano no nome do arquivo)
```

## Performance

### Cache Impact
- **Primeira consulta**: ~500ms (chamada à API)
- **Consultas cacheadas**: ~5ms (banco local)
- **Taxa de cache**: >90% após processamento inicial

### Bulk Processing
- **Batch size**: 500 itens (configurável)
- **Redução de roundtrips**: ~99% menos queries ao banco
- **TMDB em lote**: Consultas paralelas quando possível

## Troubleshooting

### TMDB Não Retorna Ano
**Sintoma**: Filme não tem ano mesmo após enriquecimento

**Causas**:
1. Filme não encontrado no TMDB
2. Chave API inválida
3. Limite de API atingido

**Soluções**:
1. Verificar chave API: `GET /api/enrich/check-missing-years`
2. Usar ano extraído como fallback (automático)
3. Adicionar manualmente via banco

### Erro "API Key Invalid"
**Sintoma**: Log mostra erro de autenticação TMDB

**Solução**:
1. Obter nova chave em https://www.themoviedb.org/settings/api
2. Atualizar via interface web
3. Limpar cache TMDB se necessário

### Performance Lenta
**Sintoma**: Processamento muito lento com TMDB

**Causas**:
1. Cache desabilitado
2. Primeiro processamento (sem cache)
3. Muitos filmes não cacheados

**Soluções**:
1. Usar `/api/process/classify-bulk-tmdb`
2. Aumentar tamanho do batch
3. Verificar cache TMDB

## Compatibilidade

### Jellyfin
O formato `Nome (Ano).strm` é o padrão recomendado pelo Jellyfin:
- Matching automático com TMDB
- Evita conflitos
- Facilita organização

### Emby/Plex
Formato também compatível com Emby e Plex.

## Interface Web

### Página de Manutenção
O sistema inclui interface web para enriquecimento TMDB:

**Localização**: Menu > Manutenção

**Botões Disponíveis**:
1. **Verificar Anos Faltantes** - Verifica status de anos em filmes
2. **Enriquecer TMDB** - Enriquece filmes via interface web

**Funcionalidades**:
- Verificação interativa de anos faltantes
- Enriquecimento em lotes de 100 filmes
- Feedback visual detalhado
- Integração com sistema de logs

Para detalhes completos da interface web, veja `TMDB_INTERFACE_BUTTON.md`

## Scripts Existentes

### Enriquecimento Manual
Para filmes já processados sem ano:

```bash
# Verificar filmes sem ano
curl http://localhost:5000/api/enrich/check-missing-years

# Enriquecer filmes existentes
curl -X POST http://localhost:5000/api/enrich/years-from-tmdb \
  -H "Content-Type: application/json" \
  -d '{"limit": 100}'
```

### Reexportação
Para atualizar arquivos já exportados:

```bash
python reexport_movies_with_year.py
```

## Monitoramento

### Logs
Processo de enriquecimento é logado:
```
INFO - Enriquecendo com TMDB: Frozen
INFO - Filme 'Frozen' atualizado com ano 2013
WARNING - Erro ao obter info TMDB para Unknown Movie: API limit reached
```

### Estatísticas
Verificar estatísticas de enriquecimento:
```sql
SELECT COUNT(*) FROM midias WHERE tmdb_id IS NOT NULL;
SELECT COUNT(*) FROM midias WHERE categoria = 'Movie' AND ano IS NOT NULL;
```

## Boas Práticas

1. **Configurar TMDB API Key**: Primeiro passo antes de processar
2. **Usar Cache**: Deixe cache habilitado (padrão 30 dias)
3. **Processar em Lotes**: Use endpoints bulk para grandes volumes
4. **Monitorar Logs**: Acompanhar erros de API TMDB
5. **Verificar Resultados**: Use endpoints de verificação após processamento

## Status

✅ Implementado e integrado ao fluxo principal
✅ Cache inteligente habilitado
✅ Fallback automático funcionando
✅ Compatível com Jellyfin
✅ Endpoints dedicados disponíveis
