# Mestre IPTV Manager

Sistema web de gerenciamento MULT IPTV com interface moderna, processamento incremental, cache TMDB e exportação STRM para Jellyfin/Emby.

## 🚀 Características

### Core Features
- **Interface Web Moderna**: Tema dark/light com Bootstrap 5, responsiva e intuitiva
- **Dashboard em Tempo Real**: Estatísticas detalhadas, gráficos e atividade recente
- **Processamento Incremental**: Nunca reprocessa tudo - apenas itens novos/modificados
- **Cache TMDB Inteligente**: Reduz chamadas à API com cache de 30 dias
- **Deduplicação Avançada**: Sistema robusto para canais TV com prioridade de qualidade
- **Exportação STRM Incremental**: Apenas exporta itens novos ou modificados
- **Enriquecimento Automático**: Ano do TMDB incluído automaticamente em filmes
- **TV M3U + EPG**: Geração de playlist TV compatível com Jellyfin
- **Classificação Inteligente**: Prioriza padrão S01E01 no nome sobre group-title
- **Validação TMDB Completa**: Corrige nomes e previne duplicatas
- **Gerenciamento IPTV Avançado**: Teste de conexão e remoção completa

### Technical Features
- **Logs Baseados em Arquivo**: Rotação automática (10MB, 5 backups)
- **Estado Persistente**: Recupera automaticamente após travamentos
- **Backup Automático**: Criado antes de operações críticas
- **Lock Management**: Sistema de lock com heartbeat para evitar conflitos
- **Retry Automático**: Retry com exponential backoff para database locks
- **Bulk Operations**: Processamento em lote para melhor performance
- **API REST Completa**: Endpoints para todas as operações

## 📋 Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- Chave da API TMDB (opcional mas recomendado)
- Caminho da galeria (ex: D:/Galeria)

## 🛠️ Instalação

### 1. Clone o Repositório
```bash
cd c:\Users\mestr\OneDrive\Documentos\IPTV\mestre-IPTV
```

### 2. Crie um Ambiente Virtual
```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Instale as Dependências
```bash
pip install -r requirements.txt
```

### 4. Configure o Ambiente
```bash
# Copie o arquivo de exemplo
copy .env.example .env

# Edite o arquivo .env com suas configurações
# - SECRET_KEY: Chave secreta do Flask
# - TMDB_API_KEY: Sua chave da API TMDB
# - GALERIA_PATH: Caminho da galeria (D:/Galeria)
```

### 5. Configure a TMDB API Key (Opcional)
Obtenha sua chave gratuita em: https://www.themoviedb.org/settings/api

Configure via:
- Interface web: Menu > Configurações > TMDB API Key
- Ou diretamente no arquivo .env

## 🚀 Execução

### Via Script (Windows):
```bash
start_web.bat
```

### Via Python:
```bash
python run.py
```

### Via Flask:
```bash
python -m flask --app app.app run --host=0.0.0.0 --port=5000
```

### Via CLI (Script Principal):
```bash
# Modo automático (sem perguntas)
python main.py --auto

# Modo completo (reprocessa tudo)
python main.py --full

# Apenas estatísticas
python main.py --stats-only
```

A aplicação estará disponível em: http://localhost:5000

## 📁 Estrutura do Projeto

```
mestre-IPTV/
├── app/
│   ├── routes/              # Rotas Flask (Blueprints)
│   │   ├── api.py           # API REST endpoints
│   │   ├── dashboard.py     # Dashboard endpoints
│   │   ├── process.py       # Process control endpoints
│   │   ├── maintenance.py   # Maintenance endpoints
│   │   ├── registration.py  # IPTV registration endpoints
│   │   ├── logs.py          # Log viewing endpoints
│   │   └── settings.py      # Settings management endpoints
│   ├── services/            # Serviços de processamento
│   │   ├── parser.py        # M3U parsing e hash calculation
│   │   ├── classifier.py    # Media classification
│   │   ├── reclassifier.py  # Advanced reclassification
│   │   ├── deduplicator.py  # TV channel deduplication
│   │   ├── tmdb.py          # TMDB API integration
│   │   ├── exporter.py      # STRM file generation
│   │   ├── downloader.py    # M3U downloading
│   │   ├── bulk_classifier.py  # Batch classification
│   │   ├── maintenance.py   # Maintenance operations
│   │   ├── tv_m3u_generator.py  # TV M3U generation
│   │   ├── epg.py           # EPG service
│   │   ├── epg_fetcher.py   # EPG fetching
│   │   ├── config.py        # Configuration
│   │   └── logo_enricher.py # Logo enrichment
│   ├── database/            # Módulo de banco de dados
│   │   ├── models.py        # Dataclass models
│   │   ├── queries.py       # Database queries
│   │   ├── migrations/      # Database migrations
│   │   └── retry_helper.py  # Lock retry helper
│   ├── background/          # Background processing
│   ├── templates/           # Templates HTML
│   │   ├── base.html        # Base template
│   │   ├── dashboard.html   # Dashboard page
│   │   ├── process.html     # Process page
│   │   ├── maintenance.html # Maintenance page
│   │   ├── registration.html # Registration page
│   │   ├── settings.html    # Settings page
│   │   └── logs.html        # Logs page
│   ├── static/              # Arquivos estáticos
│   │   ├── css/             # Custom CSS
│   │   └── js/              # Custom JavaScript
│   ├── logs/                # Arquivos de log
│   │   ├── process.log      # Process logs
│   │   ├── export.log       # Export logs
│   │   └── error.log        # Error logs
│   ├── app.py               # Flask application factory
│   └── __init__.py          # Package initialization
├── backup/                  # Backups automáticos do banco
├── cache/                   # Cache de M3U e EPG
├── database/                # Banco de dados SQLite
├── docs/                    # Documentação
│   ├── README.md            # Este arquivo
│   ├── API_DOCUMENTATION.md # Documentação completa da API
│   ├── ARCHITECTURE.md      # Visão geral da arquitetura
│   ├── ANALISE_PROJETO.md   # Análise do projeto
│   ├── ANALISE_COMPLETA_SITE.md # Análise completa do site
│   ├── AGENTS.md            # Guia para agentes
│   ├── MELHORIAS_INTERFACE_100.md # Melhorias da interface
│   ├── RESUMO_MELHORIAS_SESSAO.md # Resumo de melhorias
│   ├── DATABASE_LOCK_FIX.md # Correção de database lock
│   ├── TMDB_AUTO_ENRICHMENT.md # Enriquecimento TMDB
│   ├── TMDB_INTERFACE_BUTTON.md # Interface TMDB
│   ├── TMDB_VALIDATION.md # Sistema de validação TMDB completo
│   ├── CLASSIFICATION_FIXES.md # Correções de classificação e gerenciamento IPTV
│   ├── IPTV_MANAGEMENT_IMPROVEMENTS.md # Melhorias no gerenciamento de IPTV
│   ├── TV_M3U_JELLYFIN.md   # TV M3U para Jellyfin
│   ├── YEAR_IN_FILENAME.md  # Ano em nomes de arquivo
│   ├── QUALITY_REMOVAL.md   # Remoção de qualidade
│   └── CAPACIDADE_IPTV.md   # Análise de capacidade
├── main.py                  # Script CLI principal
├── run.py                   # Ponto de entrada web
├── requirements.txt         # Dependências Python
├── .env.example             # Exemplo de configuração
└── start_web.bat            # Script de inicialização Windows
```

## 🎯 Uso

### Interface Web

1. **Dashboard** (`/`)
   - Visualize estatísticas em tempo real
   - Monitorize atividade recente
   - Acesse gráficos de distribuição

2. **Processo** (`/process/`)
   - Baixe listas M3U
   - Processe mídias
   - Exporte para galeria
   - Acompanhe progresso em tempo real

3. **Manutenção** (`/maintenance/`)
   - Enriqueça filmes com TMDB
   - **Valide Nomes Curtos (TMDB)**: Valida filmes com ≤2 palavras, corrige nomes automaticamente e remove duplicatas
   - **Blacklist Não Validados**: Envia para blacklist filmes não encontrados no TMDB
   - Gere TV M3U + EPG
   - Corrija duplicatas
   - Limpe galeria
   - Baixe EPG

4. **Cadastro** (`/registration/`)
   - Adicione fontes IPTV
   - Gerencie fontes existentes
   - Teste URLs

5. **Configurações** (`/settings/`)
   - Configure TMDB API Key
   - Configure caminhos
   - Configure timeouts
   - Teste configurações

6. **Logs** (`/logs/`)
   - Visualize logs do sistema
   - Filtre por nível
   - Acompanhe em tempo real

### CLI Script

```bash
# Execução padrão (interativa)
python main.py

# Modo automático
python main.py --auto

# Modo completo (reprocessa tudo)
python main.py --full

# Apenas estatísticas
python main.py --stats-only

# Limpar histórico de processados
python main.py --clear-processed
```

## 📊 Regras Principais

### Processamento Incremental
- Nunca reprocessa tudo
- Apenas processa novos itens
- Usa hash para detectar mudanças
- TV channels são sempre reprocessados (para tv.m3u completo)

### Hash da Mídia
- Calculado: `categoria + nome_normalizado + ano`
- Remove indicadores de qualidade antes do cálculo
- Não inclui URL no hash
- Permite detecção de duplicatas por conteúdo

### Deduplicação TV
- Prioridade: `[L]` > FHD > HD > SD > rest
- Remove sufixos de qualidade
- Remove estados/regionais
- Mantém apenas a melhor qualidade

### Exportação STRM
- Apenas exporta itens novos ou modificados
- Usa `exported_media` para rastreamento
- Calcula hash do arquivo para detectar mudanças
- Filmes incluem ano no nome: `Nome (Ano).strm`
- Remove indicadores de qualidade dos nomes
- Previne exportações concorrentes com lock

### Enriquecimento TMDB
- Prioridade: TMDB Year > Ano do Nome > null
- Cache de 30 dias (configurável)
- Consulta automática durante classificação
- Salva tmdb_id para referência
- Fallback para ano extraído do nome

### Validação TMDB Obrigatória
- **Regra**: Filmes com ≤2 palavras no nome precisam de validação TMDB
- **Exportação**: Bloqueia exportação de filmes não validados (mantém ativo no banco)
- **Validação**: Corrige nomes automaticamente para nome oficial do TMDB
- **Deduplicação**: Remove duplicatas mantendo melhor qualidade ([L] > 4K > FHD > HD > SD)
- **Blacklist**: Envia para blacklist filmes não encontrados no TMDB após tentativas múltiplas
- **Priorização**: Valida filmes com 1 palavra primeiro, depois 2 palavras
- **Apenas categoria Movie**: Outras categorias não são afetadas pela regra

## ⚙️ Configuração

### Variáveis de Ambiente (.env)
```env
# Security
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=False

# TMDB Configuration
TMDB_API_KEY=your-tmdb-api-key-here

# Gallery Path
GALERIA_PATH=D:/Galeria

# Cache Settings
M3U_REFRESH_INTERVAL=21600  # 6 hours in seconds
TMDB_CACHE_DURATION=2592000  # 30 days in seconds

# Server Configuration
HOST=0.0.0.0
PORT=5000
```

### Configurações via Banco (system_settings)
- `tmdb_api_key`: Chave da API TMDB
- `tmdb_cache_duration`: Duração do cache TMDB em segundos
- `galeria_path`: Caminho da galeria (padrão: D:/Galeria)
- `database_timeout`: Timeout do banco em segundos
- `m3u_refresh_interval`: Intervalo de refresh do M3U em segundos
- `ultima_execucao`: Timestamp da última execução completa

## 📚 Documentação Adicional

- **[API Documentation](API_DOCUMENTATION.md)** - Referência completa da API REST
- **[Architecture](ARCHITECTURE.md)** - Visão detalhada da arquitetura do sistema
- **[Project Analysis](ANALISE_PROJETO.md)** - Análise técnica do projeto
- **[Complete Site Analysis](ANALISE_COMPLETA_SITE.md)** - Análise completa do site
- **[Interface Improvements](MELHORIAS_INTERFACE_100.md)** - Melhorias da interface web
- **[TMDB Enrichment](TMDB_AUTO_ENRICHMENT.md)** - Enriquecimento automático com TMDB
- **[TV M3U for Jellyfin](TV_M3U_JELLYFIN.md)** - Geração de TV M3U + EPG
- **[Year in Filename](YEAR_IN_FILENAME.md)** - Inclusão de ano em arquivos
- **[Quality Removal](QUALITY_REMOVAL.md)** - Remoção de indicadores de qualidade
- **[Quality Inconsistency Issue](QUALITY_INCONSISTENCY_ISSUE.md)** - ✅ Resolvido: inconsistência na remoção de qualidade
- **[Safe Migration Guide](SAFE_MIGRATION_GUIDE.md)** - Guia para migração segura de grandes volumes (600k+ mídias)
- **[Capacity Analysis](CAPACIDADE_IPTV.md)** - Análise de capacidade e escalabilidade
- **[Database Lock Fix](DATABASE_LOCK_FIX.md)** - Correção de problemas de lock

## 🔧 Troubleshooting

### Database Locked
Se encontrar erro "database is locked":
1. Pare o servidor
2. Execute `python check_locks.py`
3. Execute `python force_cleanup.py`
4. Reinicie o servidor

Veja `DATABASE_LOCK_FIX.md` para detalhes completos.

### TMDB API Errors
Se encontrar erros de TMDB:
1. Verifique se a API Key está configurada
2. Verifique se a API Key é válida
3. Verifique o limite de requisições (1000/dia free tier)
4. Limpe o cache se necessário

### Performance Lenta
Se o processamento estiver lento:
1. Verifique se há muitas fontes IPTV
2. Verifique o tamanho dos arquivos M3U
3. Use classificação em lote (bulk)
4. Verifique o cache TMDB

Veja `CAPACIDADE_IPTV.md` para análise de capacidade.

## 🚧 Limitações

- **SQLite**: Single-writer limitation (WAL mode ajuda mas não resolve tudo)
- **TMDB Free Tier**: 1000 requisições/dia (pode ser limitante para grandes bibliotecas)
- **Download Sequencial**: Não paralelo (pode ser lento para muitas fontes)
- **Single Export Lock**: Apenas uma exportação por vez
- **Sem Autenticação**: Interface web aberta (recomendado para uso local)

## 🔐 Segurança

⚠️ **Aviso Importante**: Este projeto atualmente não possui autenticação. Recomendado para uso local/pessoal apenas.

Para produção:
- Implementar autenticação (Flask-Login ou JWT)
- Usar HTTPS
- Configurar SECRET_KEY forte
- Desabilitar DEBUG
- Adicionar rate limiting
- Implementar RBAC

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto é para uso pessoal e local.

## 🙏 Agradecimentos

- Flask - Web framework
- Bootstrap - UI framework
- TMDB - Movie database API
- Chart.js - Visualização de dados
- Bootstrap Icons - Ícones

## 📞 Suporte

Para suporte, consulte a documentação na pasta `docs/` ou abra uma issue no repositório.
