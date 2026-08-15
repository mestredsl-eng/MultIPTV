# Inconsistência na Remoção de Qualidade - Issue Crítico

## Status
✅ **RESOLVIDO** - Corrigido em 27/07/2026

## Resolução
Criada função canônica `remove_quality_indicators()` em `app/services/parser.py` que combina todos os padrões de ambas as funções. Ambas as funções agora usam a mesma lógica:
- `remove_quality_from_name()` agora delega para `remove_quality_indicators()`
- `sanitize_filename()` agora usa `remove_quality_indicators()` internamente

## Status de Implementação

- [x] Problema identificado
- [x] Documentação criada
- [x] Função padronizada criada (`remove_quality_indicators`)
- [x] `parser.py` atualizado
- [x] `exporter.py` atualizado
- [x] Backward compatibility mantida
- [x] Testes criados (`test_quality_fix.py`)
- [x] Migração segura habilitada

## Problema Identificado

Existem **duas funções diferentes** para remoção de indicadores de qualidade no código, com **padrões inconsistentes**:

### 1. `parser.py::remove_quality_from_name()`
**Uso**: Calcular hash para detecção de duplicatas

**Localização**: `app/services/parser.py` (linha 92)

**Padrões removidos**:
```python
# Em colchetes
r'\(cinema\)', r'\[l\]', r'\[h?\d+\]', r'\[hdr\]', r'\[dolby\]', r'\[atmos\]', 
r'\[dts\]', r'\[leg\]', r'\[legendado\]', r'\[dub\]', r'\[dublado\]', r'\[dual\]', 
r'\[alt\]', r'\[h265\]', r'\[hevc\]', r'\[hybrid\]', r'\[x265\]', r'\[x264\]', 
r'\[ac3\]', r'\[aac\]', r'\[mp4\]', r'\[mkv\]', r'\[web-dl\]', r'\[webdl\]', 
r'\[bluray\]', r'\[bdrip\]', r'\[brrip\]', r'\[dvdrip\]', r'\[dv\]', r'\[dvd\]', 
r'\[hdtv\]', r'\[sdtv\]'

# Sem colchetes (início/fim)
r'\s*(4k|fhd|hd|sd|hdr|dolby|atmos|dts|h265|hevc|hybrid|x265|x264|ac3|aac|web-dl|webdl|bluray|bdrip|brrip|dvdrip|dv|dvd|hdtv)\s*$'
r'^\s*(4k|fhd|hd|sd|hdr|dolby|atmos|dts|h265|hevc|hybrid|x265|x264|ac3|aac|web-dl|webdl|bluray|bdrip|brrip|dvdrip|dv|dvd|hdtv)\s*'

# Remove ano
r'\s*-\s*[\(\[]\d{4}[\)\]]\s*'
r'\s*[\(\[]\d{4}[\)\]]\s*'

# Remove idioma
r'\s(leg|legendado|dub|dublado|dual|alt)\s*$'
r'^(leg|legendado|dub|dublado|dual|alt)\s'
```

**Características**:
- Case-insensitive (`.lower()`)
- Remove idiomas (leg, dub, dual, alt)
- Remove ano entre parênteses/colchetes
- **NÃO remove**: `[FHD]`, `[4K]` (maiúsculas), `720p`, `1080p`, `2160p`, marcadores adulto

### 2. `exporter.py::sanitize_filename()`
**Uso**: Gerar nome de arquivo .strm

**Localização**: `app/services/exporter.py` (linha 14)

**Padrões removidos**:
```python
# Em colchetes (maiúsculas)
r'\[L\]', r'\[4K\]', r'\[FHD\]', r'\[HD\]', r'\[SD\]', r'\[WEB-DL\]', r'\[WEBDL\]', 
r'\[BLURAY\]', r'\[BDRIP\]', r'\[BRIP\]', r'\[DVDRIP\]', r'\[DVRIP\]', r'\[HDTV\]', r'\[SDTV\]'

# Sem colchetes (maiúsculas/minúsculas)
r'\s*4K\s*', r'\s*FHD\s*', r'\s*HD\s*', r'\s*SD\s*', r'\s*WEB-DL\s*', r'\s*WEBDL\s*', 
r'\s*BLURAY\s*', r'\s*BDRIP\s*', r'\s*BRIP\s*', r'\s*DVDRIP\s*', r'\s*DVRIP\s*', 
r'\s*HDTV\s*', r'\s*SDTV\s*', r'\s*HDR\s*', r'\s*DOLBY\s*', r'\s*ATMOS\s*', r'\s*DTS\s*', 
r'\s*H265\s*', r'\s*HEVC\s*', r'\s*HYBRID\s*', r'\s*X265\s*', r'\s*X264\s*', 
r'\s*AC3\s*', r'\s*AAC\s*'

# Resolução
r'\s*\d+p\s*',  # 720p, 1080p, 2160p
r'\s*\d+K\s*',  # 4K, 8K

# Marcadores adulto
r'\[adulto?\]', r'\[xxx\]', r'\[porn\]', r'\bxxx\b', r'\bporn\b', r'\badulto?\b'
r'\s*-\s*(?!19\d{2}|20\d{2})\d+'
```

**Características**:
- Case-insensitive (`re.IGNORECASE`)
- Remove resolução (720p, 1080p, 2160p)
- Remove marcadores adulto
- Remove números trailing (exceto anos)
- Trunca nome para 200 caracteres
- **NÃO remove**: `[cinema]`, `[mp4]`, `[mkv]`, idiomas (leg, dub, dual, alt)

## Impacto

### 1. Duplicatas Incorretas
```python
# Exemplo: "Matrix [FHD] (1999)"

# Hash calculado (remove_quality_from_name):
nome_limpo = "matrix [fhd] (1999)"  # [FHD] não é removido (maiúsculas)
hash = sha256("Movie|matrix [fhd] (1999)")

# Nome arquivo (sanitize_filename):
nome_arquivo = "Matrix (1999)"  # [FHD] é removido (case-insensitive)

# Resultado: Hash ≠ Nome do arquivo
# Pode causar duplicatas ou arquivos não encontrados
```

### 2. Arquivos Não Encontrados
- Sistema busca arquivo com nome sanitizado
- Hash foi calculado com nome diferente
- `exported_media` pode ter hash que não bate com arquivo atual

### 3. Problemas em Grande Escala
- Com 600k mídias, pequenas inconsistências se multiplicam
- Dificuldade de identificar quais arquivos estão problemáticos
- Reexportação pode criar duplicatas em massa

## Soluções Propostas

### Solução 1: Padronizar Funções (Recomendado)
Criar uma função única compartilhada:

```python
# app/services/parser.py
def remove_quality_indicators(nome):
    """
    Remove quality indicators from name for both hash calculation and filename sanitization.
    This is the canonical function - all quality removal should use this.
    """
    if not nome:
        return ''

    normalized = nome.lower()

    # Remove quality indicators in brackets (case-insensitive)
    patterns_brackets = [
        r'\(cinema\)', r'\[l\]', r'\[4k\]', r'\[fhd\]', r'\[hd\]', r'\[sd\]',
        r'\[hdr\]', r'\[dolby\]', r'\[atmos\]', r'\[dts\]', r'\[leg\]', r'\[legendado\]',
        r'\[dub\]', r'\[dublado\]', r'\[dual\]', r'\[alt\]', r'\[h265\]', r'\[hevc\]',
        r'\[hybrid\]', r'\[x265\]', r'\[x264\]', r'\[ac3\]', r'\[aac\]', r'\[mp4\]',
        r'\[mkv\]', r'\[web-dl\]', r'\[webdl\]', r'\[bluray\]', r'\[bdrip\]', r'\[brrip\]',
        r'\[dvdrip\]', r'\[dv\]', r'\[dvd\]', r'\[hdtv\]', r'\[sdtv\]', r'\[webrip\]',
        r'\[bdscr\]', r'\[bdr\]', r'\[br\]'
    ]

    for pattern in patterns_brackets:
        normalized = re.sub(pattern, '', normalized)

    # Remove quality indicators without brackets
    patterns_no_brackets = [
        r'\s*(4k|fhd|hd|sd|hdr|dolby|atmos|dts|h265|hevc|hybrid|x265|x264|ac3|aac|web-dl|webdl|bluray|bdrip|brrip|dvdrip|dv|dvd|hdtv|sdtv|webrip|bdscr|bdr|br)\s*$',
        r'^\s*(4k|fhd|hd|sd|hdr|dolby|atmos|dts|h265|hevc|hybrid|x265|x264|ac3|aac|web-dl|webdl|bluray|bdrip|brrip|dvdrip|dv|dvd|hdtv|sdtv|webrip|bdscr|bdr|br)\s*'
    ]

    for pattern in patterns_no_brackets:
        normalized = re.sub(pattern, '', normalized)

    # Remove resolution patterns
    normalized = re.sub(r'\s*\d+p\s*', '', normalized)  # 720p, 1080p, 2160p
    normalized = re.sub(r'\s*\d+K\s*', '', normalized)  # 4K, 8K

    # Remove year patterns
    normalized = re.sub(r'\s*-\s*[\(\[]\d{4}[\)\]]\s*', '', normalized)
    normalized = re.sub(r'\s*[\(\[]\d{4}[\)\]]\s*', '', normalized)

    # Remove language indicators
    normalized = re.sub(r'\s(leg|legendado|dub|dublado|dual|alt)\s*$', '', normalized)
    normalized = re.sub(r'^(leg|legendado|dub|dublado|dual|alt)\s', '', normalized)

    # Remove adult content markers
    normalized = re.sub(r'\[adulto?\]', '', normalized)
    normalized = re.sub(r'\[xxx\]', '', normalized)
    normalized = re.sub(r'\[porn\]', '', normalized)
    normalized = re.sub(r'\bxxx\b', '', normalized)
    normalized = re.sub(r'\bporn\b', '', normalized)
    normalized = re.sub(r'\badulto?\b', '', normalized)

    # Remove extra spaces
    normalized = ' '.join(normalized.split())

    return normalized


# Funções wrapper para compatibilidade
def remove_quality_from_name(nome):
    """DEPRECATED: Use remove_quality_indicators instead."""
    return remove_quality_indicators(nome)
```

### Solução 2: Recalcular Hashes
Se não for possível padronizar, recalcular hashes existentes:

```python
# Script para recalcular hashes
def recalculate_all_hashes():
    """Recalculate all hashes using standardized quality removal."""
    db = get_db()
    
    media_items = db.execute('SELECT id, categoria, nome_normalizado, ano FROM midias').fetchall()
    
    for item in media_items:
        new_hash = calculate_hash_midia(item['categoria'], item['nome_normalizado'], item['ano'])
        db.execute('UPDATE midias SET hash_midia = ? WHERE id = ?', (new_hash, item['id']))
    
    db.commit()
```

## Plano de Ação

### Imediato
1. ✅ Documentar problema (este arquivo)
2. ⏳ Criar função padronizada
3. ⏳ Atualizar `parser.py` e `exporter.py` para usar função única
4. ⏳ Testar com 100 itens

### Curto Prazo
5. ⏳ Recalcular hashes existentes (se necessário)
6. ⏳ Limpar tabela `exported_media`
7. ⏳ Testar exportação incremental

### Longo Prazo
8. ⏳ Implementar validação de hash vs nome de arquivo
9. ⏳ Adicionar testes unitários para remoção de qualidade
10. ⏳ Documentar padrões suportados

## Riscos de Não Corrigir

- **Alto**: Duplicatas em massa ao reexportar 600k itens
- **Alto**: Arquivos não encontrados durante exportação
- **Médio**: Inconsistência entre banco de dados e sistema de arquivos
- **Médio**: Dificuldade de troubleshooting em problemas futuros

## Status de Implementação

- [x] Problema identificado
- [x] Documentação criada
- [ ] Função padronizada criada
- [ ] Testes unitários escritos
- [ ] Migração de hashes existentes
- [ ] Validação em produção

## Referências

- `app/services/parser.py::remove_quality_from_name()` (linha 92)
- `app/services/exporter.py::sanitize_filename()` (linha 14)
- `docs/QUALITY_REMOVAL.md` - Documentação existente (incompleta)
