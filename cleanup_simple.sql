-- Limpar processos antigos presos (mais de 2 horas)
-- Marcar como 'failed'

-- Processos em execução antigos
UPDATE process_status
SET fim = CURRENT_TIMESTAMP, status = 'failed'
WHERE status = 'running'
AND datetime(inicio) < datetime('now', '-2 hours');

-- Itens na fila antigos
UPDATE fila_processamento
SET fim = CURRENT_TIMESTAMP, status = 'failed'
WHERE status = 'running'
AND datetime(inicio) < datetime('now', '-2 hours');

-- Execuções antigas
UPDATE execution_stats
SET fim = CURRENT_TIMESTAMP, status = 'failed'
WHERE status = 'running'
AND datetime(inicio) < datetime('now', '-2 hours');

-- Verificar resultado
SELECT 'process_status' as tabela, COUNT(*) as running_count FROM process_status WHERE status = 'running'
UNION ALL
SELECT 'fila_processamento', COUNT(*) FROM fila_processamento WHERE status = 'running'
UNION ALL
SELECT 'execution_stats', COUNT(*) FROM execution_stats WHERE status = 'running';
