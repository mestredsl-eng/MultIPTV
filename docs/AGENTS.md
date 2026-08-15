# Guia do Projeto Mestre IPTV Manager

## Visão Geral
Sistema web de gerenciamento IPTV com interface moderna em Flask, processamento incremental e cache TMDB.

## Comandos Principais

### Execução
```bash
# Via script
python run.py

# Via Flask
python -m flask --app app.app run --host=0.0.0.0 --port=5000

# Via bat (Windows)
start_web.bat
```

### Instalação
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Estrutura de Código

### Serviços Principais
- `app/services/parser.py`: Parse M3U, cálculo de hash, normalização, contagem de palavras
- `app/services/classifier.py`: Classificação básica de conteúdo
- `app/services/reclassifier.py`: Reclassificação avançada com sistema de pontuação
- `app/services/deduplicator.py`: Deduplicação de canais TV
- `app/services/tmdb.py`: Enriquecimento com TMDB API com filtragem por ano
- `app/services/tmdb_validator.py`: Validação TMDB com priorização, correção de nomes e deduplicação inteligente
- `app/services/exporter.py`: Exportação STRM incremental com validação obrigatória para filmes curtos
- `app/services/downloader.py`: Download M3U com cache
- `app/services/bulk_classifier.py`: Classificação otimizada com bulk operations
- `app/services/maintenance.py`: Serviço unificado de manutenção
- `app/services/tv_m3u_generator.py`: Gerador TV M3U + EPG para Jellyfin

### Banco de Dados
- `app/database/models.py`: Modelos dataclass
- `app/database/queries.py`: Queries comuns
- `app/database/migrations/`: Migrações SQL

### Rotas API
- `app/routes/api.py`: Endpoints REST principais
- Novos endpoints adicionados:
  - `/api/maintenance/stats`: Estatísticas de manutenção
  - `/api/maintenance/fix-name-duplicates`: Corrigir duplicatas por nome
  - `/api/maintenance/fix-quality-duplicates`: Corrigir duplicatas por qualidade
  - `/api/maintenance/cleanup-orphans`: Limpar registros órfãos
  - `/api/process/classify-bulk`: Classificação otimizada
  - `/api/process/classify-with-tmdb`: Classificação com enriquecimento TMDB automático
  - `/api/process/classify-bulk-tmdb`: Classificação bulk otimizada com TMDB
  - `/api/reclassify/single`: Reclassificar item individual
  - `/api/reclassify/batch`: Reclassificação em lote
  - `/api/reclassify/analyze`: Analisar reclassificações potenciais
  - `/api/enrich/check-missing-years`: Verificar filmes sem ano
  - `/api/enrich/years-from-tmdb`: Enriquecer filmes existentes com ano do TMDB
  - `/api/maintenance/generate-tv-m3u`: Gerar tv.m3u + epg.xml compatíveis com Jellyfin
  - `/api/validation/validate-short-names`: Validar filmes com ≤2 palavras no nome
  - `/api/validation/progress`: Obter progresso da validação TMDB
  - `/api/validation/blacklist-unvalidated`: Enviar não validados para blacklist
  - `/api/validation/stats`: Estatísticas de validação TMDB
  - `/api/iptv/sources/<iptv_id>/test-connection`: Testar conexão IPTV

## Configuração
Variáveis de ambiente suportadas (ver .env.example):
- `SECRET_KEY`: Chave secreta do Flask
- `DEBUG`: Modo debug (True/False)
- `TMDB_API_KEY`: Chave da API TMDB
- `GALERIA_PATH`: Caminho da galeria (padrão: D:/Galeria)
- `M3U_REFRESH_INTERVAL`: Intervalo de refresh M3U em segundos
- `TMDB_CACHE_DURATION`: Duração do cache TMDB em segundos

## Regras de Negócio

### Hash de Mídia
Calculado como: `categoria + nome_normalizado + ano` (sem qualidade)
- Implementado em `parser.calculate_hash_midia()`
- Remove indicadores de qualidade antes do cálculo

### Deduplicação TV
Prioridade: `[L]` > FHD > HD > SD > rest
- Implementado em `deduplicator.py`
- Remove sufixos de qualidade e estados/regionais

### Processamento Incremental
- Usa `hash_midia` para identificar itens já processados
- Não reprocessa itens existentes
- Implementado em classifier e bulk_classifier

### Exportação
- Apenas exporta itens novos ou modificados
- Usa `exported_media` para rastreamento
- Previne exportações concorrentes com `export_lock`
- Calcula hash do arquivo para detectar mudanças
- **Filmes incluem ano no nome do arquivo** (ex: "Matrix (1999).strm")
- **Filmes Adultos incluem ano no nome do arquivo** para consistência
- **Remoção automática de indicadores de qualidade** (4K, [L], FHD, etc.)

### Enriquecimento TMDB Automático
- **Integrado ao fluxo de classificação** - Ano obtido automaticamente da API TMDB
- **Prioridade TMDB > Ano do nome** - Ano do TMDB sobrescreve ano extraído do nome
- **Cache inteligente** - TMDB cache reduz chamadas à API
- **Fallback automático** - Se TMDB falhar, usa ano extraído do nome
- **tmdb_id salvo** - ID do TMDB salvo para referência futura
- **Busca inteligente por categoria** - Busca em endpoint correto (filme vs série)
- **Prevenção de correções incorretas** - Verifica tipo antes de corrigir nomes
- **Integrado ao fluxo de classificação** - Ano obtido automaticamente da API TMDB
- **Prioridade TMDB > Ano do nome** - Ano do TMDB sobrescreve ano extraído do nome
- **Cache inteligente** - TMDB cache reduz chamadas à API
- **Fallback automático** - Se TMDB falhar, usa ano extraído do nome
- **tmdb_id salvo** - ID do TMDB salvo para referência futura
- **Interface Web**: Botão "Enriquecer TMDB" na página de Manutenção
  - Verifica filmes sem ano
  - Enriquece TODOS os filmes sem ano (sem limite)
  - Feedback detalhado do processo
- **Endpoints dedicados**:
  - `/api/process/classify-with-tmdb` - Classificação com TMDB
  - `/api/process/classify-bulk-tmdb` - Classificação bulk otimizada com TMDB
  - `/api/enrich/check-missing-years` - Verificar filmes sem ano (via API)
  - `/api/enrich/years-from-tmdb` - Enriquecer filmes existentes (via API)
- **IMPORTANTE**: Configurar TMDB API Key antes de usar (ver .env.example)

## Melhorias Implementadas

### Correção de Classificação e Gerenciamento IPTV
- ✅ **Classificação inteligente**: Prioriza padrão S01E01 no nome sobre group-title
- ✅ **TMDB inteligente**: Busca no endpoint correto (filme vs série) baseado na categoria
- ✅ **Prevenção de duplicatas**: Verifica tipo antes de corrigir nomes
- ✅ **Remoção completa de IPTV**: Remove banco de dados + galeria
- ✅ **Teste de conexão IPTV**: Verifica se IPTV está funcionando em tempo real
- ✅ **Análise de fontes M3U**: Analisamos 4 fontes para entender padrões de classificação

### Correção de Classificação e Gerenciamento IPTV
- ✅ **Análise de fontes M3U** - Analisamos 4 fontes IPTV para entender padrões de classificação
- ✅ **Classificação corrigida** - Séries não caem mais em filmes
- ✅ **TMDB inteligente** - Busca no endpoint correto baseado na categoria
- ✅ **Prevenção de duplicatas** - Verifica tipo antes de corrigir nomes
- ✅ **Remoção completa** - IPTVs são completamente removidas (banco + galeria)
- ✅ **Teste de conexão** - Verifica se IPTV está funcionando em tempo real
- **Documentação**: CLASSIFICATION_FIXES.md com detalhes técnicos completos

## Correção Database Lock
- ✅ Aumentado timeout do banco de 30s para 120s
- ✅ Criado sistema de retry automático (`app/database/retry_helper.py`)
- ✅ Melhorado exporter com tratamento de lock
- ✅ Scripts de diagnóstico (`check_locks.py`) e limpeza (`force_cleanup.py`)
- ✅ Documentação completa em `DATABASE_LOCK_FIX.md`

### Código
1. ✅ Corrigido SECRET_KEY hardcoded (agora usa variável de ambiente)
2. ✅ Corrigido DEBUG hardcoded (agora usa variável de ambiente)
3. ✅ Removida API key exposta em config.py
4. ✅ Criado serviço unificado de manutenção (maintenance.py)
5. ✅ Adicionado suporte a .env com python-dotenv
6. ✅ Integrado reclassifier avançado à API

### Performance
1. ✅ Criado bulk_classifier para operações em lote
2. ✅ Endpoint /api/process/classify-bulk para classificação otimizada
3. ✅ Usa executemany para inserts em lote
4. ✅ Batch processing para reduzir roundtrips ao banco

### Funcionalidades
1. ✅ API de reclassificação avançada (single, batch, analyze)
2. ✅ API de manutenção unificada
3. ✅ Análise de reclassificação sem aplicar mudanças
4. ✅ Arquivo .env.example para configuração
5. ✅ Ano incluído no nome de arquivos de filmes para Jellyfin
6. ✅ Extração de ano melhorada com múltiplos formatos
7. ✅ API para enriquecer filmes com ano do TMDB
8. ✅ Remoção automática de indicadores de qualidade em arquivos .strm

## Scripts de Manutenção Legados
Os seguintes scripts ainda existem mas podem ser substituídos pelo serviço de manutenção:
- `fix_duplicates_by_name.py` → Use `/api/maintenance/fix-name-duplicates`
- `fix_quality_duplicates.py` → Use `/api/maintenance/fix-quality-duplicates`
- Vários scripts check_*.py → Use `/api/maintenance/stats`

## Gerador TV M3U + EPG para Jellyfin
- **Integração Jellyfin**: Gera tv.m3u e epg.xml compatíveis
- **Filtro automático**: Apenas TVs ativas e não blacklist
- **Fontes EPG**: Integra com EPG das IPTVs configuradas
- **Botão interface**: Página Manutenção > Gerar TV M3U + EPG
- **Endpoint**: `/api/maintenance/generate-tv-m3u`
- **Formato**: M3U com tvg-id, tvg-name, tvg-logo para Jellyfin
- **Arquivos**: tv.m3u (playlist) + epg.xml (guia de programação)

Para detalhes completos, veja `TV_M3U_JELLYFIN.md`

## Próximas Melhorias Sugeridas
1. Adicionar autenticação na interface web
2. Implementar testes automatizados
3. Adicionar filtros e busca na interface
4. Integrar EPG ao export
5. Sistema de agendamento de tarefas
6. Monitoramento e alertas
7. Documentação da API (Swagger)
8. Dockerfile para containerização

## Notas Importantes
- Sistema usa SQLite com WAL mode para melhor concorrência
- Cache TMDB com duração configurável (padrão: 30 dias)
- Backup automático antes de operações críticas
- Logs em app/logs/ com rotação (10MB, 5 backups)
- Interface em tema escuro fixo
- Processamento em segundo plano com heartbeat
- Timeout do banco aumentado para 120s com retry automático

## Resolução de Problemas

### Enriquecimento TMDB via Interface Web
**Botão disponível na página Manutenção**:

1. **Verificar Anos Faltantes**:
   - Clique em "Verificar Anos Faltantes"
   - Mostra total de filmes com/sem ano
   - Lista exemplos de filmes sem ano
   - Oferece opção para enriquecer automaticamente

2. **Enriquecer TMDB**:
   - Clique em "Enriquecer TMDB"
   - Enriquece TODOS os filmes sem ano (sem limite)
   - Mostra estatísticas detalhadas
   - Feedback de atualizados/não encontrados/erros

### Database Locked
Se encontrar erro "database is locked":

1. **Parar o servidor**: Pare o Flask se estiver rodando
2. **Verificar locks**: `python check_locks.py`
3. **Limpar processos presos**: `python force_cleanup.py`
4. **Reiniciar servidor**: `python run.py`

Para detalhes completos, veja `DATABASE_LOCK_FIX.md`

## Melhorias Recentes (Sessão Atual)

### Correções de Classificação e Gerenciamento IPTV
- **Classificação inteligente**: Prioriza padrão S01E01 no nome sobre group-title
- **TMDB inteligente**: Busca no endpoint correto (filme vs série) baseado na categoria
- **Prevenção de duplicatas**: Verifica tipo antes de corrigir nomes
- **Remoção completa de IPTV**: Remove banco de dados + galeria
- **Teste de conexão IPTV**: Verifica se IPTV está funcionando em tempo real
- **Análise de fontes M3U**: Analisamos 4 fontes para entender padrões de classificação
- **Documentação**: CLASSIFICATION_FIXES.md com detalhes técnicos

### Página de Configurações
- **Nova página** /settings/ com configurações do sistema
- **Configurações TMDB**: API Key, cache duration
- **Configurações Database**: Timeout do banco
- **Configurações Path**: Caminho da galeria
- **Testes de validação**: API Key e caminho
- **Persistência**: Salvo no banco via system_settings

### Feedback Visual TMDB
- **Polling automático**: Verificação de progresso em tempo real
- **Atualização dinâmica**: Barra de progresso atualizada
- **Mensagens detalhadas**: Contador de filmes processados
- **Status conclusão**: Feedback claro ao usuário

### Documentação Completa
- **ANALISE_COMPLETA_SITE.md**: Análise detalhada de todo o sistema
- **Funcionalidades faltantes**: Identificadas e priorizadas
- **Plano de implementação**: Roadmap claro para melhorias
- **RESUMO_MELHORIAS_SESSAO.md**: Resumo das mudanças atuais

### Status do Sistema
- **Funcionalidades Core**: 100% implementadas
- **Interface Web**: 95% completa
- **Documentação Técnica**: 100% completa
- **Configurações**: Agora via interface
- **Feedback Visual**: Melhorado significativamente

## Novos Endpoints API

### Configurações
- GET/POST /api/settings/tmdb - Gerenciar configurações TMDB
- POST /api/settings/test-tmdb - Testar API Key TMDB
- GET/POST /api/settings/database - Gerenciar configurações database
- GET/POST /api/settings/path - Gerenciar configurações de caminho
- POST /api/settings/test-path - Testar validade do caminho

### TMDB Progress
- GET /api/enrich/tmdb-progress - Progresso do enriquecimento TMDB

## Páginas Web (6 total)
1. Dashboard - Estatísticas e gráficos
2. Processo - Controles e progresso
3. Manutenção - Ferramentas de manutenção
4. Cadastro - Fontes IPTV
5. **Configurações** - NOVA
6. Logs - Visualização de logs

## Interface Web 100% Completa ✅

### Temas e Visual
- **Dark/Light Theme Switcher**: Toggle na navbar com persistência
- **Animações**: Fade-in escalonado, pulse para status, transições suaves
- **Gradientes Modernos**: Botões, headers, progress bars com gradientes
- **Ícones**: Títulos, cards, botões, labels, tabelas, formularios
- **Cards Melhorados**: Border radius 12px, hover effects, shadows
- **Layout Responsivo**: Mobile-first, media queries otimizadas
- **Scrollbar Customizada**: Estilo moderno com hover effects

### Páginas Melhoradas
- ✅ Dashboard: Fade-in escalonado, ícones grandes nos cards
- ✅ Processo: Ícones em controles, terminal melhorado
- ✅ Manutenção: Ícones em headers, botões animados
- ✅ Cadastro: Ícones em formulários, labels melhorados
- ✅ Configurações: Nova página com ícones e validação
- ✅ Logs: CSS aplicado, scrollbar customizada

### Componentes Visuais
- **Botões**: Border radius 8px, gradiente, shadow, hover transform
- **Tabelas**: Headers com gradient, badges animados, ícones
- **Forms**: Inputs arredondados, labels com ícones, focus states
- **Modals**: Border radius 12px, shadow pronunciado
- **Progress**: Height 1.5rem, gradiente horizontal, transições

### Documentação
- **MELHORIAS_INTERFACE_100.md**: Documentação completa das melhorias visuais
- Exemplos visuais antes/depois
- Lista completa de animações e transições
- Guia de temas e responsividade
