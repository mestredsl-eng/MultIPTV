# Guia de Migração Segura para Grandes Volumes (600k+ Mídias)

## ⚠️ Aviso Importante

**NÃO delete grandes volumes de mídias sem seguir este guia passo a passo.**

Existem riscos conhecidos que podem causar perda de dados ou inconsistências em larga escala.

## Pré-Requisitos

### 1. Backup Completo
```bash
# Backup do banco de dados atual
copy database\iptv.db backup\iptv_pre_migration_600k.db

# Verificar tamanho do backup
dir backup\iptv_pre_migration_600k.db
```

### 2. Verificar Espaço em Disco
```bash
# Verificar espaço disponível em D:\
dir D:\

# Estimar espaço necessário para reexportação
# 600k arquivos .strm ≈ 100-200 MB (muito pequeno)
# Mas estrutura de diretórios pode ser grande
```

### 3. Parar Serviços
```bash
# Parar servidor Flask se estiver rodando
# Ctrl+C no terminal ou kill process
```

## Fase 1: Correção de Problemas Conhecidos

### 1.1 Corrigir Inconsistência de Qualidade
**RESOLVIDO**: Inconsistência corrigida em 27/07/2026

A inconsistência entre `sanitize_filename()` e `remove_quality_from_name()` foi corrigida:
- Criada função canônica `remove_quality_indicators()` em `parser.py`
- Ambas as funções agora usam a mesma lógica
- Hash e nome de arquivo são consistentes

Veja `QUALITY_INCONSISTENCY_ISSUE.md` para detalhes da correção.

```bash
# Opcional: Recalcular hashes se desejar garantir consistência
# python recalculate_all_hashes.py
```

### 1.2 Verificar Integridade do Banco
```bash
python check_db.py
python check_duplicates_blacklist.py
python check_table_structure.py
```

### 1.3 Limpar Locks
```bash
python check_locks.py
python force_cleanup.py  # Se necessário
```

## Fase 2: Teste em Pequena Escala

### 2.1 Exportar 100 Itens
```bash
# Via API
curl -X POST http://localhost:5000/api/process/export \
  -H "Content-Type: application/json" \
  -d '{"limit": 100}'

# Ou via interface web
# Menu > Processo > Exportar (com limite)
```

### 2.2 Verificar Resultados
```bash
# Verificar se arquivos foram criados
dir D:\Galeria\FILMES

# Verificar logs
type app\logs\export.log

# Verificar banco
python check_exported_vs_blacklist.py
```

### 2.3 Validar Hashes
```bash
python check_db_url_duplicates.py
python check_gallery_duplicates.py
```

### 2.4 Se Teste Falhar
**PARE** e investigue antes de continuar.

## Fase 3: Migração por Categorias

### 3.1 Ordem Recomendada de Categorias
1. **DOCUMENTARIOS** (menor volume, menor risco)
2. **EDUCACIONAL** (volume pequeno)
3. **ESPORTES** (volume pequeno)
4. **DESENHOS** (volume médio)
5. **NOVELAS** (volume médio)
6. **SERIES** (volume grande)
7. **FILMES** (maior volume)
8. **FILMES_XXX** (maior volume, verificar separadamente)

### 3.2 Procedimento por Categoria

#### Passo 1: Backup Antes da Categoria
```bash
copy database\iptv.db backup\iptv_before_FILMES.db
```

#### Passo 2: Limpar Exportados da Categoria
```bash
# Via SQL
sqlite3 database\iptv.db "DELETE FROM exported_media WHERE hash_midia IN (SELECT hash_midia FROM midias WHERE categoria = 'Movie');"

# Ou via API
curl -X POST http://localhost:5000/api/maintenance/reset-exported
```

#### Passo 3: Deletar Arquivos da Categoria
```bash
# CUIDADO: Isso é irreversível
rmdir /s /q D:\Galeria\FILMES
```

#### Passo 4: Reexportar Categoria
```bash
# Via API
curl -X POST http://localhost:5000/api/process/export \
  -H "Content-Type: application/json" \
  -d '{"categoria": "Movie"}'

# Ou via interface web
# Menu > Processo > Exportar
```

#### Passo 5: Verificar
```bash
# Contar arquivos exportados
dir /s /b D:\Galeria\FILMES\*.strm | find /c ".strm"

# Comparar com banco
python check_exported_count.py
```

#### Passo 6: Validar
```bash
# Verificar duplicatas
python check_gallery_duplicates.py

# Verificar orfãos
python check_gallery_orphans.py
```

### 3.3 Se Categoria Falhar
**PARE** e:
1. Restaurar backup da categoria
2. Investigar logs
3. Corrigir problema
4. Repetir teste com 100 itens

## Fase 4: Migração Completa

### 4.1 Apenas Após Sucesso em Todas Categorias
Se todas as categorias passaram nos testes:

```bash
# Backup final antes de deletar tudo
copy database\iptv.db backup\iptv_before_full_delete.db
```

### 4.2 Deletar Toda Galeria
```bash
# CUIDADO EXTREMO: Irreversível
rmdir /s /q D:\Galeria\FILMES
rmdir /s /q D:\Galeria\SERIES
rmdir /s /q D:\Galeria\NOVELAS
rmdir /s /q D:\Galeria\DESENHOS
rmdir /s /q D:\Galeria\DOCUMENTARIOS
rmdir /s /q D:\Galeria\EDUCACIONAL
rmdir /s /q D:\Galeria\ESPORTES
rmdir /s /q D:\Galeria\FILMES_XXX
```

### 4.3 Limpar Tabela exported_media
```bash
sqlite3 database\iptv.db "DELETE FROM exported_media;"
```

### 4.4 Reexportar Tudo
```bash
# Via API
curl -X POST http://localhost:5000/api/process/export

# Ou via interface web
# Menu > Processo > Exportar (sem limite)
```

### 4.5 Monitorar Progresso
```bash
# Verificar logs em tempo real
type app\logs\export.log

# Verificar progresso via API
curl http://localhost:5000/api/process/status
```

## Fase 5: Validação Final

### 5.1 Contar Arquivos
```bash
# Contar total de .strm
dir /s /b D:\Galeria\*.strm | find /c ".strm"

# Deve bater com total de mídias não blacklist
python check_exported_count.py
```

### 5.2 Verificar Duplicatas
```bash
python check_gallery_duplicates.py
python check_db_url_duplicates.py
```

### 5.3 Verificar Orfãos
```bash
python check_gallery_orphans.py
```

### 5.4 Verificar Integridade
```bash
python check_db.py
python check_table_structure.py
```

### 5.5 Testar no Jellyfin
1. Abrir Jellyfin
2. Verificar se bibliotecas escanearam
3. Verificar se filmes aparecem corretamente
4. Verificar se não há duplicatas
5. Verificar se nomes estão limpos

## Plano de Rollback

### Se Algo Der Errado

#### Opção 1: Restaurar Backup do Banco
```bash
# Parar servidor
# Restaurar backup
copy backup\iptv_pre_migration_600k.db database\iptv.db
# Reiniciar servidor
```

#### Opção 2: Restaurar Backup por Categoria
```bash
# Se apenas uma categoria falhou
copy backup\iptv_before_FILMES.db database\iptv.db
# Reexportar apenas outras categorias
```

#### Opção 3: Restaurar Galeria Completa
```bash
# Se você tem backup da galeria (recomendado ter)
# Restaurar de backup externo
```

## Riscos e Mitigações

### Risco 1: Inconsistência de Hash
**Probabilidade**: Alta
**Impacto**: Duplicatas em massa
**Mitigação**: Corrigir antes de migrar (Fase 1)

### Risco 2: Database Lock
**Probabilidade**: Média
**Impacto**: Exportação falha
**Mitigação**: Sistema de retry implementado, scripts de diagnóstico

### Risco 3: Espaço em Disco
**Probabilidade**: Baixa
**Impacto**: Exportação falha
**Mitigação**: Verificar antes (Pré-Requisitos)

### Risco 4: Performance Lenta
**Probabilidade**: Alta
**Impacto**: Processamento demorado
**Mitigação**: Processamento em lotes, monitoramento de progresso

### Risco 5: Perda de Dados
**Probabilidade**: Baixa (com backup)
**Impacto**: Catastrófico
**Mitigação**: Múltiplos backups, rollback planejado

## Tempo Estimado

### Por Categoria (600k total)
- DOCUMENTARIOS: ~10-20 minutos
- EDUCACIONAL: ~5-10 minutos
- ESPORTES: ~5-10 minutos
- DESENHOS: ~30-60 minutos
- NOVELAS: ~30-60 minutos
- SERIES: ~2-4 horas
- FILMES: ~2-4 horas
- FILMES_XXX: ~2-4 horas

**Total**: ~8-12 horas (sem contar validação)

## Checklist de Validação

### Antes de Começar
- [ ] Backup completo criado
- [ ] Espaço verificado
- [ ] Serviços parados
- [ ] Inconsistência de qualidade corrigida
- [ ] Integridade do banco verificada
- [ ] Locks limpos

### Durante Migração por Categoria
- [ ] Backup antes da categoria
- [ ] Categoria deletada
- [ ] Categoria reexportada
- [ ] Arquivos contados
- [ ] Duplicatas verificadas
- [ ] Orfãos verificados

### Após Migração Completa
- [ ] Total de arquivos bate com banco
- [ ] Sem duplicatas
- [ ] Sem orfãos
- [ ] Integridade do banco ok
- [ ] Jellyfin escaneou corretamente
- [ ] Nomes limpos visíveis

## Suporte e Troubleshooting

### Logs Importantes
- `app/logs/export.log` - Exportação
- `app/logs/process.log` - Processamento
- `app/logs/error.log` - Erros

### Scripts de Diagnóstico
- `check_locks.py` - Verificar locks
- `check_db.py` - Verificar banco
- `check_exported_count.py` - Contar exportados
- `check_gallery_duplicates.py` - Verificar duplicatas
- `check_gallery_orphans.py` - Verificar orfãos

### Documentação Relacionada
- `QUALITY_INCONSISTENCY_ISSUE.md` - Inconsistência crítica
- `QUALITY_REMOVAL.md` - Remoção de qualidade
- `DATABASE_LOCK_FIX.md` - Problemas de lock
- `TROUBLESHOOTING.md` - Solução de problemas

## Recomendação Final

**NÃO pule fases.** Cada fase existe para mitigar riscos específicos.

Se você não tem certeza sobre qualquer passo, **PARE** e pergunte antes de continuar.

É melhor levar mais tempo e fazer corretamente do que apressar e causar problemas em 600k mídias.
