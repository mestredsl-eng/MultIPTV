# Análise de Capacidade do Projeto Mestre IPTV

## 📊 Visão Geral

Projeto de gerenciamento IPTV em Flask com SQLite, processamento incremental e exportação STRM para Jellyfin.

## 🏗️ Arquitetura Atual

### Banco de Dados (SQLite)

**Tabelas principais**:
- `iptvs`: Fontes IPTV configuradas
- `midias`: Mídias processadas (filmes, séries, TV, etc.)
- `tv_channels`: Canais TV específicos
- `tmdb_cache`: Cache TMDB (enriquecimento)
- `exported_media`: Rastreamento de exportações
- `export_lock`: Lock para evitar exportações concorrentes

**Índices existentes**:
- midias: categoria, tmdb_id, blacklist, status, nome_normalizado
- tv_channels: categoria, blacklist, status, nome_normalizado
- exported_media: hash_midia, arquivo
- tmdb_cache: titulo_normalizado, ultima_consulta

### Processamento

**Parser M3U** (`parser.py`):
- Processa linha a linha
- Calcula hash: categoria + nome_normalizado + ano
- Remove indicadores de qualidade

**Classificação** (`classifier.py`):
- Baseada em palavras-chave no nome
- Regex para filmes, séries, TV, novelas, etc.
- Sazonamento automático

**Bulk Classifier** (`bulk_classifier.py`):
- Batch size: 500 itens por operação
- Operações INSERT em lote (executemany)
- Cache TMDB para filmes

**Downloader** (`downloader.py`):
- Cache de 6 horas por padrão
- Timeout de 30 segundos por download
- Download sequencial (não paralelo)

**Exportação** (`exporter.py`):
- Lock export_lock para evitar conflitos
- Hash tracking (exported_media)
- Heartbeat cada 30 segundos
- Timeout do banco: 120s com retry automático
- Exportação incremental (não reprocessa)

## 🔍 Análise de Capacidade

### 1. Capacidade do SQLite (Teórica)

SQLite não tem limite de linhas, mas há limites práticos:
- **Tamanho máximo do arquivo**: 281 TB (teórico, mas não recomendado para produção)
- **Tamanho prático recomendado**: < 10 GB por banco
- **Performance ideal**: < 1 GB (50-100k linhas por tabela)

**Com 1 arquivo M3U gigante:**
- 100k itens = ~10 MB (SQLite)
- 500k itens = ~50 MB (SQLite)
- 1M itens = ~100 MB (SQLite)
- 10M itens = ~1 GB (SQLite)

**Estimativa por fonte IPTV "gigante":**
- Pequeno: 5k-10k itens = ~1-2 MB
- Médio: 50k-100k itens = ~10-20 MB
- Grande: 500k-1M itens = ~100-200 MB
- Gigante: 5M-10M itens = ~1-2 GB

### 2. Processamento M3U

**Bottleneck**: Download sequencial

Atualmente:
- Download 1 vez por vez (não paralelo)
- Timeout: 30 segundos por arquivo
- Cache: 6 horas

**Estimativa para fonte de 1M itens:**
- Tamanho do arquivo M3U: ~20-50 MB
- Download: 5-10 segundos (com cache: 0 segundos)
- Parsing: ~10-30 segundos
- Classificação bulk: ~1-2 minutos
- Total: ~2-3 minutos por fonte

**Para 10 fontes de 1M itens cada:**
- Total: 20-30 minutos (sequencial)

### 3. Classificação e TMDB

**Processamento TMDB:**
- Cache de 30 dias (2592000 segundos)
- 40 requisições/limite por key (TMDB Free Tier)
- 1000 requisições/dia (Free Tier)

**Para 1M filmes:**
- 1M chamadas TMDB → **PROBLEMA** (excederia limite Free)
- Solução: Usar cache extensivamente, reprocessar em lotes

### 4. Exportação STRM

**Performance atual:**
- 1 STRM = 1 linha de texto (bytes)
- 1M STRMs = ~50-100 MB
- Galeria: `D:/Galeria`

**Gargalo principal:**
- Write em disco (I/O bound)
- Sistema de arquivos Windows (NTFS)

### 5. Lock de Exportação

**Mecanismo atual:**
- Table lock export_lock (única linha)
- Timeout: 120s com retry
- Heartbeat: 30 segundos

**Problema:**
- Apenas 1 exportação por vez

## 🚫 Limitações Atuais Críticas

### 1. **TMDB Free Tier**
- 40 req/min
- 1000 req/dia
- **Bloqueia processamento massivo de filmes novos**

### 2. **Download Sequencial**
- Não paralelo
- 1 arquivo por vez
- Fontes gigantes = tempos longos

### 3. **Concorrência**
- Apenas 1 exportação por vez
- Lock export_lock compartilhado
- Sem filas para processamento

### 4. **SQLite Single Writer**
- SQLite padrão: 1 escrita por vez (WAL mode ajuda mas não resolve tudo)
- Para 10 fontes gigantes: pode ter locks frequentes

### 5. **Memória RAM**
- Flask carrega tudo em memória?
- Processamento em lotes de 500 ajuda, mas ainda pode ser problema para fontes gigantes

## 📈 Capacidade Estimada

### Cenário 1: Fontes Pequenas (5k-10k itens)

**5 fontes de 10k itens = 50k itens total**
- SQLite: ~5 MB ✅
- Processamento: ~10-15 minutos ✅
- Exportação: ~5-10 minutos ✅
- TMDB: 50k filmes = **PROBLEMA** (limite diário)

**Conclusão**: **VIÁVEL** mas precisa de estratégia TMDB

### Cenário 2: Fontes Médias (50k-100k itens)

**3 fontes de 50k itens = 150k itens total**
- SQLite: ~15 MB ✅
- Processamento: ~15-30 minutos ✅
- Exportação: ~15-30 minutos ✅
- TMDB: 150k filmes = **PROBLEMA CRÍTICO** (excede 3 dias Free Tier)

**Conclusão**: **LIMITADO** sem mudar estratégia TMDB

### Cenário 3: Fontes Grandes (500k-1M itens)

**1 fonte de 500k itens**
- SQLite: ~50 MB ✅
- Processamento: ~1-2 horas ✅
- Exportação: ~1-2 horas ✅
- TMDB: 500k filmes = **PROBLEMA CRÍTICO**

**Conclusão**: **VIÁVEL** sem TMDB, mas demorado

### Cenário 4: Fontes Gigantes (5M+ itens)

**1 fonte de 5M itens**
- SQLite: ~500 MB ✅ (mas lento)
- Download: M3U 100-200 MB = 10-30 minutos
- Processamento: 10-20 horas (s downloads)
- Classificação: 10-20 horas
- Exportação: 10-20 horas
- **TOTAL**: 30-60 horas

**Conclusão**: **POSSÍVEL MAS MUITO LENTO**

## 🎯 Resumo

### Capacidade "Segura" (Sem Problemas)

✅ **1-2 fontes médias (50k-100k cada)**
- Total: 100k-200k itens
- Tempo: 30-60 minutos
- ✅ SQLite: ~15-20 MB

### Capacidade "Com Risco" (Precisa Ajustes)

⚠️ **3-5 fontes grandes (100k-500k cada)**
- Total: 300k-2.5M itens
- Tempo: 2-8 horas
- ⚠️ SQLite: ~50-250 MB
- ❌ **TMDB**: Excede limite Free Tier

### Capacidade "Crítica" (Precisa Redesenho)

❌ **10+ fontes gigantes (500k-1M cada)**
- Total: 5M-10M itens
- Tempo: 30-60 horas por operação
- ❌ SQLite: ~500 MB-1 GB (operações lentas)
- ❌ Download sequencial: muito lento
- ❌ TMDB: Impossível (Free Tier)
- ❌ Lock export_lock: concorrência inexistente

## 🔧 Recomendações

### Para 1-2 Fontes Médias (50k-100k)

1. **Usar TMDB Premium** ou cache extensivo
2. **Aumentar batch size** para 1000-2000
3. **Download paralelo** (3-5 threads)
4. **SQLite → PostgreSQL** (se necessário no futuro)

### Para 3-5 Fontes Grandes (100k-500k)

1. **Migrar para PostgreSQL**
2. **Download paralelo** (5-10 threads)
3. **TMDB por batch** (estratégia de cache)
4. **Sistema de filas de processamento**
5. **Exportação assíncrona** (celery/rq)

### Para 10+ Fontes Gigantes (500k-1M)

1. **PostgreSQL + Redis Cache**
2. **Download paralelo massivo** (20+ threads)
3. **Classificação por microserviços**
4. **Exportação distribuída**
5. **Redis Queue para filas**
6. **Grafana + Prometheus** para monitoramento
7. **Load balancer** se for web

## ✅ Conclusão

**Capacidade atual segura:**
- **1-2 fontes de 50k-100k itens** cada
- **Ou 1 fonte gigante de 500k-1M itens** (sem TMDB)

**Para mais que isso:**
- Precisa de arquitetura de microserviços
- Banco de dados distribuído
- Sistema de filas (RabbitMQ, Redis, Celery)
- Download paralelo em massa
- TMDB Premium ou estratégia própria

**Sistema atual é perfeito para uso pessoal/small business mas tem limites para escala enterprise.**