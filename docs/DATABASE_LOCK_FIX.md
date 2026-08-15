# Correção do Problema "Database is Locked"

## Problema Identificado

O erro "database is locked" ocorreu durante o processamento, especificamente:
- Backup criado com sucesso
- Durante classificação, erro ao tentar remover arquivo `.strm`
- Múltiplas tentativas resultaram no mesmo erro

## Causa Raiz

1. **Processos Presos**: Múltiplos processos antigos (de 3 dias atrás) marcados como 'running' mas não mais executando
   - 5 processos em process_status
   - 3 execuções em execution_stats
   - Isso pode causar conflitos de lock

2. **Timeout Insuficiente**: Timeout original de 30s pode ser insuficiente para operações grandes

3. **Falta de Retry**: Sem tratamento específico para erros de lock

4. **Operações Concorrentes**: O export tenta remover arquivos e atualizar banco simultaneamente

## Soluções Implementadas

### 1. Aumentado Timeout do Banco de Dados
**Arquivo**: `app/database/__init__.py`

```python
# Antes: timeout=30.0, busy_timeout=30000
# Depois: timeout=120.0, busy_timeout=120000
g.db = sqlite3.connect(DATABASE_PATH, timeout=120.0)
g.db.execute('PRAGMA busy_timeout=120000')  # 120 segundos
g.db.execute('PRAGMA synchronous=NORMAL')  # Melhor performance
```

**Benefício**: Maior tolerância a operações longas

### 2. Sistema de Retry Automático
**Arquivo**: `app/database/retry_helper.py` (novo)

Criado helper functions:
- `safe_execute()` - Executa queries com retry automático
- `safe_commit()` - Faz commit com retry automático
- `@retry_on_locked` - Decorator para retry de funções
- `DatabaseLockError` - Exceção customizada

**Características**:
- Até 3 tentativas com exponential backoff
- Tratamento específico para erros de lock
- Logging detalhado de tentativas

### 3. Melhorado Exporter com Retry
**Arquivo**: `app/services/exporter.py`

**Mudanças**:
- `acquire_export_lock()` - Usa safe_execute/safe_commit
- `release_export_lock()` - Usa safe_execute com tratamento de erro
- `update_heartbeat()` - Não falha se database locked
- `export_media()` - Usa safe_execute/safe_commit
- `export_all_media()` - Melhor tratamento de erros e logging

**Benefício**: Export mais robusto contra locks

### 4. Scripts de Diagnóstico e Limpeza

#### check_locks.py
Verifica estado dos locks no banco:
- Export lock status
- Process status
- Fila de processamento
- Execution stats

#### force_cleanup.py
Limpa processos presos de forma direta:
- Marca process_status 'running' antigos como 'failed'
- Marca fila_processamento 'running' antiga como 'failed'
- Marca execution_stats 'running' antigos como 'failed'

#### cleanup_simple.sql
Script SQL para limpeza manual

## Como Resolver o Problema Atual

### Passo 1: Parar o Servidor
```bash
# Pare o servidor web se estiver rodando
# Ctrl+C no terminal onde o servidor está rodando
```

### Passo 2: Executar Limpeza
```bash
cd C:\Users\mestr\OneDrive\Documentos\IPTV\mestre-IPTV
python force_cleanup.py
```

### Passo 3: Verificar Locks
```bash
python check_locks.py
```

### Passo 4: Reiniciar o Servidor
```bash
python run.py
```

## Prevenção Futura

### 1. Timeout Aumentado
O timeout agora é 120s, reduzindo chances de lock

### 2. Retry Automático
Operações críticas têm retry automático com 3 tentativas

### 3. Melhor Logging
Erros de lock são logados com detalhes para debugging

### 4. Heartbeat Melhorado
Update de heartbeat não falha se database locked

### 5. Tratamento de Erros
Funções individuais têm tratamento específico

## Recomendações Adicionais

### 1. Monitoramento
Adicionar monitoramento para detectar processos presos automaticamente

### 2. Limpeza Automática
Implementar limpeza automática de processos antigos (ex: script cron)

### 3. Connection Pooling
Considerar connection pooling para melhor gerenciamento de conexões

### 4. Checkpoint do WAL
Adicionar checkpoint periódico do WAL para reduzir tamanho do arquivo

### 5. Database Health Check
Adicionar endpoint de health check para verificar estado do banco

## Teste das Correções

Após aplicar as correções:

1. **Teste de Carga**: Processar grande quantidade de mídias
2. **Teste de Concorrência**: Múltiplas operações simultâneas
3. **Teste de Recovery**: Verificar recuperação após lock
4. **Monitoramento**: Observar logs para erros de lock

## Arquivos Modificados

1. `app/database/__init__.py` - Timeout aumentado
2. `app/database/retry_helper.py` - Sistema de retry (novo)
3. `app/services/exporter.py` - Melhorado com retry
4. `check_locks.py` - Script de diagnóstico (novo)
5. `force_cleanup.py` - Script de limpeza (novo)
6. `cleanup_simple.sql` - Script SQL manual (novo)

## Status

✅ Análise concluída
✅ Soluções implementadas
⏳ Aguardando limpeza manual do banco (servidor deve ser parado)
⏳ Teste das correções após limpeza
