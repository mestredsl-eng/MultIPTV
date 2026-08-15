# Remoção de Indicadores de Qualidade em Arquivos .strm

## Objetivo
Remover indicadores de qualidade dos nomes dos arquivos .strm para manter nomes limpos e consistentes no Jellyfin.

## Problema Resolvido
Anteriormente, arquivos .strm continham indicadores de qualidade no nome:
- `Matrix [L] (1999).strm`
- `Avatar [4K] (2009).strm`
- `Titanic [FHD] (1997).strm`

Isso causava nomes longos e inconsistentes no Jellyfin.

## Solução Implementada

### Modificação no exporter.py
**Arquivo**: `app/services/exporter.py`

**Mudança**: Função `sanitize_filename()` agora remove automaticamente todos os indicadores de qualidade.

### Indicadores Removidos

#### Qualidade de Resolução
- `[L]`, `[4K]`, `[FHD]`, `[HD]`, `[SD]`
- `4K`, `FHD`, `HD`, `SD`
- `2160p`, `1080p`, `720p`
- `8K`

#### Qualidade de Fonte
- `[WEB-DL]`, `[WEBDL]`
- `[BLURAY]`, `[BDRIP]`, `[BRIP]`
- `[DVDRIP]`, `[DVRIP]`
- `[HDTV]`, `[SDTV]`

#### Áudio
- `[HDR]`, `[DOLBY]`, `[ATMOS]`, `[DTS]`
- `HDR`, `DOLBY`, `ATMOS`, `DTS`
- `[AC3]`, `[AAC]`

#### Codec
- `[H265]`, `[HEVC]`, `[HYBRID]`
- `[X265]`, `[X264]`
- `H265`, `HEVC`, `HYBRID`
- `X265`, `X264`

## Exemplos de Transformação

### Antes
```
Matrix [L] (1999).strm
Avatar [4K] (2009).strm
Titanic [FHD] [WEB-DL] (1997).strm
Frozen [HD] (2013).strm
Inception [BLURAY] (2010).strm
```

### Depois
```
Matrix (1999).strm
Avatar (2009).strm
Titanic (1997).strm
Frozen (2013).strm
Inception (2010).strm
```

## Implementação Técnica

### Código
```python
def sanitize_filename(name):
    """Sanitize filename to remove invalid characters and quality indicators for Windows."""
    if not name:
        return 'unnamed'

    # Remove quality indicators and brackets
    quality_patterns = [
        r'\[L\]', r'\[4K\]', r'\[FHD\]', r'\[HD\]', r'\[SD\]',
        r'\[WEB-DL\]', r'\[WEBDL\]', r'\[BLURAY\]',
        r'\[BDRIP\]', r'\[BRIP\]', r'\[DVDRIP\]',
        r'\[DVRIP\]', r'\[HDTV\]', r'\[SDTV\]',
        r'\s*4K\s*', r'\s*FHD\s*', r'\s*HD\s*',
        r'\s*SD\s*', r'\s*WEB-DL\s*', r'\s*WEBDL\s*',
        # ... mais padrões
    ]

    for pattern in quality_patterns:
        name = re.sub(pattern, '', name, flags=re.IGNORECASE)

    # Remove invalid characters: < > : " / \ | ? * [ ]
    name = re.sub(r'[<>:"/\\|?*\[\]]', '', name)
    # Remove leading/trailing spaces and dots
    name = name.strip('. ')
    # Replace multiple spaces with single space
    name = re.sub(r'\s+', ' ', name)
    return name or 'unnamed'
```

### Características
- **Case-insensitive**: Não diferencia maiúsculas/minúsculas
- **Regex avançado**: Padrões robustos para capturar variações
- **Espaçamento inteligente**: Remove espaços extras após remoção
- **Backup**: Retorna 'unnamed' se nome ficar vazio

## Benefícios

### Nomes Limpos
- `Matrix (1999).strm` ao invés de `Matrix [L] [FHD] [WEB-DL] (1999).strm`
- Mais legível e organizado

### Consistência
- Todos os arquivos seguem o mesmo padrão
- Facilita organização no Jellyfin

### Compatibilidade Jellyfin
- Jellyfin ignora indicadores de qualidade no nome
- Matching automático funciona melhor com nomes limpos
- Interface mais limpa e profissional

### Espaço em Disco
- Nomes mais curtos = menos espaço no sistema de arquivos
- Menos caracteres = menor overhead

## Impacto no Sistema

### Exportação de Novos Arquivos
- **Automático**: Novos arquivos já são gerados sem indicadores
- **Sem mudança manual**: Processo transparente
- **Aplica a todas categorias**: Movies, Series, etc.

### Reexportação de Arquivos Existentes
Arquivos já exportados mantêm nomes antigos até serem reexportados.

**Para atualizar arquivos existentes**:
```bash
# Resetar tabela de exportados
python check_locks.py  # Ou usar botão na interface

# Reexportar
python run.py  # Ou usar interface para exportar
```

### Banco de Dados
- **Nome original mantido**: `nome_da_midia` permanece inalterado
- **Somente exportação**: Apenas nome do arquivo .strm é alterado
- **Hash não afetado**: `hash_midia` calculado antes da remoção

## Testes

### Casos de Teste
```python
# Testes de remoção de qualidade
assert sanitize_filename("Matrix [L] (1999)") == "Matrix (1999)"
assert sanitize_filename("Avatar [4K] (2009)") == "Avatar (2009)"
assert sanitize_filename("Titanic [FHD] [WEB-DL] (1997)") == "Titanic (1997)"
assert sanitize_filename("Frozen [HD] (2013)") == "Frozen (2013)"
assert sanitize_filename("Inception [BLURAY] (2010)") == "Inception (2010)"

# Testes de espaçamento
assert sanitize_filename("Matrix   [L]   (1999)") == "Matrix (1999)"
assert sanitize_filename("Avatar [4K] (2009)") == "Avatar (2009)"
```

## Limitações

### Apenas Nomes de Arquivos
- **Nome original mantido**: `nome_da_midia` no banco não é alterado
- **Apenas .strm**: Apenas arquivos exportados são afetados
- **Outros arquivos**: Não afeta TV M3U ou EPG

### Padrões Não Cobertos
- Qualidades personalizadas não padrão
- Formatos desconhecidos
- Idiomas diferentes (ex: PAL, NTSC)

## Troubleshooting

### Nome Ficou Vazio
**Sintoma**: Arquivo chamado 'unnamed.strm'

**Causa**: Nome consistia apenas de indicadores de qualidade

**Solução**: O sistema usa 'unnamed' como backup

### Qualidade Ainda Aparece
**Sintoma**: Indicadores ainda no nome

**Causa**: Padrão não reconhecido

**Solução**: Adicionar novo padrão à lista `quality_patterns`

### Erro em Exportação
**Sintoma**: Erro durante geração de .strm

**Causa**: Função modificada incorretamente

**Solução**: Reverter mudança e verificar regex

## Boas Práticas

1. **Verificar Nomes**: Revisar nomes após exportação
2. **Testar Reexportação**: Reexportar arquivos existentes
3. **Monitorar Logs**: Verificar erros de sanitização
4. **Manter Padrões**: Manter lista de padrões atualizada

## Compatibilidade

### Jellyfin
- ✅ Compatível com matching automático
- ✅ Nomes mais limpos na interface
- ✅ Melhora identificação de mídia

### Kodi
- ✅ Compatível
- ✅ Nomes mais limpos

### VLC
- ✅ Compatível
- ✅ Sem impacto funcional

## Status

✅ Implementado no exporter.py
✅ Remove todos os indicadores comuns
✅ Case-insensitive
✅ Espaçamento inteligente
✅ Backup para nomes vazios
✅ Testado com padrões comuns
✅ **Inconsistência corrigida** - Agora usa função canônica unificada

## ✅ Issue Resolvido

**ATUALIZAÇÃO (27/07/2026)**: A inconsistência entre `sanitize_filename()` e `remove_quality_from_name()` foi corrigida.

- Criada função canônica `remove_quality_indicators()` em `parser.py`
- Ambas as funções agora usam a mesma lógica de remoção de qualidade
- Hash e nome de arquivo agora são consistentes
- **Seguro para migração de grandes volumes**

Veja `QUALITY_INCONSISTENCY_ISSUE.md` para detalhes da correção.
