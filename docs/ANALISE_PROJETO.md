# Análise do Projeto Mestre IPTV Manager

## Visão Geral
Sistema web de gerenciamento IPTV com interface moderna para processamento de listas M3U, classificação de conteúdo, deduplicação e exportação para formato STRM compatível com Jellyfin/Emby.

## Arquitetura
- **Framework**: Flask 3.0.0
- **Banco de Dados**: SQLite com WAL mode
- **Padrão**: MVC com serviços separados
- **Processamento**: Incremental com cache
- **Interface**: Tema escuro responsivo

## Estrutura do Banco de Dados
- `iptvs`: Fontes IPTV cadastradas
- `midias`: Conteúdo processado (filmes, séries, etc.)
- `tv_channels`: Canais de TV
- `tmdb_cache`: Cache de consultas TMDB
- `exported_media`: Rastreamento de exportações
- `export_lock`: Prevenção de exportações concorrentes
- `process_status`: Status de processamento
- `fila_processamento`: Fila de etapas
- `execution_stats`: Estatísticas de execução
- `system_settings`: Configurações do sistema

## Problemas Identificados

### 1. Segurança
- **SECRET_KEY hardcoded**: `'dev-secret-key-change-in-production'` em app.py
- **DEBUG=True**: Habilitado em produção
- **Sem autenticação**: Interface web aberta
- **SQL Injection**: Algumas queries usando concatenação
- **API Key exposta**: TMDB API key em config.py (linha 38)

### 2. Código
- **Duplicação**: Scripts de manutenção duplicam lógica (fix_duplicates_*.py)
- **Inconsistência**: Hash calculado de forma diferente em parser vs reclassifier
- **Error handling**: Exceções genéricas sem tratamento específico
- **Hardcoded paths**: Caminhos como D:/Galeria hardcoded em múltiplos lugares
- **Background thread**: Implementação incompleta no background_thread.py
- **Parser**: Função calculate_hash não usada (calculate_hash_midia é a usada)

### 3. Performance
- **N+1 queries**: Queries em loop sem bulk operations
- **Cache subutilizado**: TMDB cache não usado em alguns pontos
- **Índices faltantes**: Pode faltar índices compostos
- **Memory**: Carregamento completo de M3U em memória
- **Lock timeout**: Timeout de 30s pode ser insuficiente

### 4. Funcionalidades
- **Reclassifier não integrado**: Serviço avançado de reclassificação não usado
- **Falta validação**: Sem validação de URLs, campos obrigatórios
- **Sem rollback**: Backup automático mas sem rollback automático
- **Logs limitados**: Sem filtros, busca ou exportação
- **EPG incompleto**: EPG baixado mas não integrado ao export
- **Sem testes**: Nenhum teste automatizado

### 5. Interface
- **Sem feedback**: Erros genéricos sem detalhes
- **Loading states**: Sem indicadores de loading adequados
- **Responsividade**: Dashboard pode ter problemas em mobile
- **Acessibilidade**: Falta ARIA labels, contrastes

## Oportunidades de Melhoria

### Código
1. Centralizar configurações em arquivo .env
2. Implementar autenticação na interface web
3. Adicionar validação de dados com Pydantic/FValid
4. Refatorar scripts de manutenção em serviços reutilizáveis
5. Integrar reclassifier avançado ao fluxo principal
6. Adicionar tratamento de erros específico
7. Implementar logging estruturado

### Performance
1. Implementar bulk inserts/updates
2. Adicionar cache Redis para dados frequentes
3. Otimizar queries com índices compostos
4. Processamento streaming para M3U grandes
5. Implementar connection pooling
6. Adicionar async/await para I/O operations

### Funcionalidades
1. Sistema de busca avançado
2. Filtros e ordenação na interface
3. Exportação em múltiplos formatos
4. Integração completa de EPG
5. Agendamento de tarefas
6. Sistema de notificações
7. API REST completa
8. Webhooks para integrações

### Monitoramento
1. Métricas de performance (Prometheus)
2. Health checks
3. Alertas por email/Telegram
4. Dashboard administrativo
5. Análise de uso

## Próximos Passos Prioritários
1. ✅ Corrigir segurança (SECRET_KEY, DEBUG)
2. ✅ Implementar autenticação básica
3. ✅ Refatorar scripts de manutenção
4. ✅ Otimizar queries com bulk operations
5. ✅ Integrar reclassifier avançado
6. ✅ Adicionar testes básicos
7. ✅ Melhorar error handling
8. ✅ Enriquecimento TMDB automático
9. ✅ Interface web para TMDB
10. ✅ Inclusão de ano em nomes de arquivos

## Funcionalidades TMDB Implementadas
- **Enriquecimento Automático**: Integrado ao fluxo de classificação
- **Interface Web**: Botão Enriquecer TMDB na página Manutenção
- **Ano em Arquivos**: Filmes exportados com ano no nome
- **API Endpoints**: Múltiplos endpoints para enriquecimento
- **Cache Inteligente**: Reduz chamadas à API TMDB
- **Fallback Automático**: Usa ano extraído se TMDB falhar

**Documentação**:
- `TMDB_AUTO_ENRICHMENT.md` - Enriquecimento automático detalhado
- `TMDB_INTERFACE_BUTTON.md` - Interface web para TMDB
- `YEAR_IN_FILENAME.md` - Inclusão de ano em arquivos
