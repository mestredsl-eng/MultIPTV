# Botão Enriquecer TMDB - Interface Web

## Visão Geral
O botão "Enriquecer TMDB" na página de Manutenção permite enriquecer filmes com dados do TMDB diretamente pela interface web, facilitando a identificação no Jellyfin.

## Localização
**Página**: Manutenção (`/maintenance`)
**Seção**: Ferramentas de Manutenção
**Botões**:
1. **Verificar Anos Faltantes** (azul) - Verifica status antes de enriquecer
2. **Enriquecer TMDB** (primário/azul) - Executa o enriquecimento

## Funcionalidade

### 1. Verificar Anos Faltantes
**Botão**: "Verificar Anos Faltantes" (ícone de busca)

**Função**:
- Conta total de filmes no sistema
- Conta filmes com ano
- Conta filmes sem ano
- Mostra exemplos de filmes sem ano
- Oferece opção para enriquecer automaticamente

**Exemplo de Output**:
```
Status de Anos em Filmes:

Total de Filmes: 1500
Com Ano: 1200
Sem Ano: 300

Exemplos sem ano:
1. Frozen
2. Avatar
3. Titanic
4. Matrix
5. Inception

Deseja enriquecer os 300 filmes sem ano?
[OK] [Cancelar]
```

### 2. Enriquecer TMDB
**Botão**: "Enriquecer TMDB" (ícone de banco de dados)

**Função**:
- Enriquece TODOS os filmes sem ano (sem limite)
- Consulta API TMDB para cada filme
- Atualiza ano no banco de dados
- Salva tmdb_id para referência
- Mostra estatísticas detalhadas

**Exemplo de Output**:
```
Enriquecimento concluído em 120s: 285 atualizados, 15 não encontrados, 0 erros

Atualizados: 285
Não encontrados: 15
Erros: 0
Duração: 120s
Total processados: 300
```

## Fluxo de Uso

### Fluxo Recomendado
1. Acessar página de Manutenção
2. Clicar em "Verificar Anos Faltantes"
3. Revisar estatísticas e exemplos
4. Clicar em "OK" para enriquecer automaticamente
5. Aguardar conclusão
6. Reexportar filmes para atualizar nomes de arquivos

### Fluxo Manual
1. Acessar página de Manutenção
2. Clicar diretamente em "Enriquecer TMDB"
3. Confirmar operação
4. Aguardar conclusão
5. Revisar estatísticas

## Requisitos
- **TMDB API Key**: Deve estar configurada
- **Conexão Internet**: Necessária para consultar TMDB
- **Permissões**: Escrita no banco de dados

## Erros Comuns

### "API Key Invalid"
**Causa**: Chave TMDB não configurada ou inválida

**Solução**:
1. Configurar chave via interface web
2. Obter nova chave em https://www.themoviedb.org/settings/api
3. Tentar novamente

### "Filme não encontrado"
**Causa**: TMDB não encontrou o filme

**Impacto**: Filme mantém ano extraído do nome (se disponível)

### "Erro de conexão"
**Causa**: Sem internet ou TMDB fora do ar

**Solução**:
1. Verificar conexão
2. Tentar novamente mais tarde
3. Filmes mantêm ano extraído como fallback

## Integração com Exportação

### Após Enriquecimento
Após enriquecer filmes com ano:

1. **Reexportar Filmes**:
   ```bash
   python reexport_movies_with_year.py
   ```

2. **Ou pela interface**:
   - Usar botão "Reset Exportados" na página Manutenção
   - Processar exportação novamente
   - Arquivos terão ano no nome: `Nome (Ano).strm`

### Resultado Final
```
Antes: D:/Galeria/FILMES/Frozen/Frozen.strm
Depois: D:/Galeria/FILMES/Frozen (2013)/Frozen (2013).strm
```

## Performance

### Tempos Estimados
- **Verificação**: ~2 segundos
- **Enriquecimento (todos os filmes)**: Depende da quantidade
  - 100 filmes: ~30-60 segundos
  - 500 filmes: ~3-5 minutos
  - 1000 filmes: ~6-10 minutos
- **Cache**: Consultas subsequentes ~5ms

### Fatores que Afetam
- Velocidade da internet
- Carga do servidor TMDB
- Quantidade de filmes
- Taxa de cache TMDB
- Limite de taxa da API TMDB (40 req/10s)

## Logs e Monitoramento

### Logs do Sistema
Processo é logado em `app/logs/process.log`:
```
INFO - Enriquecendo com TMDB: Frozen
INFO - Filme 'Frozen' atualizado com ano 2013
WARNING - Erro ao obter info TMDB para Unknown Movie: API limit reached
```

### Logs via Interface
Acessar página de Logs para acompanhar em tempo real.

## API Alternativa

### Via API REST
Se preferir usar API diretamente:

```bash
# Verificar anos faltantes
curl http://localhost:5000/api/enrich/check-missing-years

# Enriquecer TODOS os filmes (sem limite)
curl -X POST http://localhost:5000/api/enrich/years-from-tmdb-all \
  -H "Content-Type: application/json" \
  -d '{}'

# Enriquecer com limite específico
curl -X POST http://localhost:5000/api/enrich/years-from-tmdb \
  -H "Content-Type: application/json" \
  -d '{"limit": 100}'
```

## Boas Práticas

1. **Verificar Primeiro**: Use "Verificar Anos Faltantes" antes de enriquecer
2. **Monitorar Logs**: Acompanhar processo via página de Logs
3. **Reexportar Após**: Reexportar filmes após enriquecer
4. **Configurar API Key**: Ter certeza que TMDB API Key está configurada
5. **Respeitar TMDB**: O sistema respeita limites da API TMDB automaticamente

## Troubleshooting

### Botão Não Responde
1. Verificar se servidor está rodando
2. Verificar console do navegador para erros
3. Recarregar a página
4. Verificar logs do servidor

### Nenhum Filme Encontrado
1. Verificar se há filmes sem ano
2. Verificar se TMDB API Key está configurada
3. Verificar logs para erros específicos

### Erro ao Salvar
1. Verificar permissões do banco de dados
2. Verificar se banco não está locked
3. Verificar espaço em disco

## Compatibilidade

### Navegadores
- ✅ Chrome/Edge (Recomendado)
- ✅ Firefox
- ✅ Safari
- ⚠️ IE11 (Não suportado)

### Dispositivos
- ✅ Desktop (Melhor experiência)
- ✅ Tablet (Funcional)
- ⚠️ Mobile (Limitado devido a tamanho de tela)

## Status

✅ Botão implementado na interface
✅ Verificação de anos faltantes funcional
✅ Enriquecimento TMDB funcional (SEM LIMITE)
✅ Feedback detalhado ao usuário
✅ Integração com sistema de logs
✅ Processamento de todos os filmes sem ano
✅ Compatível com Jellyfin
