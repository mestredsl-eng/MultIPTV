# Inclusão de Ano em Nomes de Arquivos de Filmes

## Objetivo
Facilitar a identificação de filmes no Jellyfin, especialmente para filmes com nomes curtos ou comuns, incluindo o ano no nome do arquivo.

## Enriquecimento TMDB Automático
**NOVO**: O sistema agora integra automaticamente o enriquecimento TMDB no fluxo de processamento principal.

- **Ano do TMDB tem prioridade**: Se a API TMDB retornar um ano, ele sobrescreve o ano extraído do nome
- **Consulta automática**: Filmes são automaticamente enriquecidos durante a classificação
- **Cache inteligente**: Resultados TMDB são cacheados para reduzir chamadas à API
- **Endpoints dedicados**:
  - `/api/process/classify-with-tmdb` - Classificação com TMDB
  - `/api/process/classify-bulk-tmdb` - Classificação bulk otimizada com TMDB

Para detalhes completos, veja `TMDB_AUTO_ENRICHMENT.md`

## Problema Resolvido
Filmes como "Frozen", "Avatar", "Titanic", etc., têm múltiplas versões em diferentes anos. Sem o ano no nome do arquivo, o Jellyfin pode ter dificuldade em identificar corretamente qual versão é.

## Solução Implementada

### 1. Modificação no Exporter
**Arquivo**: `app/services/exporter.py`

**Mudança**: Para filmes e filmes adultos, o ano agora é incluído no nome do arquivo `.strm`:

```python
# Antes:
arquivo = folder / f"{nome}.strm"

# Depois (com ano):
arquivo = folder / f"{nome} ({ano}).strm"
```

**Resultado**:
- Pasta: `D:/Galeria/FILMES/Matrix (1999)/`
- Arquivo: `D:/Galeria/FILMES/Matrix (1999)/Matrix (1999).strm`

### 2. Melhoria na Extração de Ano
**Arquivos**: `app/services/parser.py` e `app/services/classifier.py`

**Mudança**: Função `extract_year()` agora suporta múltiplos formatos:

```python
patterns = [
    r'\((\d{4})\)',  # (2024)
    r'\[(\d{4})\]',  # [2024]
    r'\s(\d{4})\s',  # 2024 between spaces
    r'(\d{4})$',     # 2024 at end
    r'[-._](\d{4})[-._]',  # 2024 with separators
]
```

**Validação**: Apenas anos entre 1900 e 2030 são considerados válidos.

### 3. Endpoint para Enriquecer Ano via TMDB
**Novos endpoints**:
- `GET /api/enrich/check-missing-years` - Verificar filmes sem ano
- `POST /api/enrich/years-from-tmdb` - Enriquecer filmes usando API TMDB

**Uso**:
```bash
# Verificar quantos filmes não têm ano
curl http://localhost:5000/api/enrich/check-missing-years

# Enriquecer 100 filmes sem ano
curl -X POST http://localhost:5000/api/enrich/years-from-tmdb \
  -H "Content-Type: application/json" \
  -d '{"limit": 100}'
```

### 4. Script de Reexportação
**Arquivo**: `reexport_movies_with_year.py`

**Função**: Reexportar filmes já exportados para atualizar nomes de arquivos com ano.

**Uso**:
```bash
python reexport_movies_with_year.py
```

## Exemplos Práticos

### Antes
```
D:/Galeria/FILMES/Frozen/Frozen.strm
D:/Galeria/FILMES/Avatar/Avatar.strm
D:/Galeria/FILMES/Titanic/Titanic.strm
```

### Depois
```
D:/Galeria/FILMES/Frozen (2013)/Frozen (2013).strm
D:/Galeria/FILMES/Avatar (2009)/Avatar (2009).strm
D:/Galeria/FILMES/Titanic (1997)/Titanic (1997).strm
```

## Benefícios

1. **Identificação Clara**: Jellyfin pode facilmente distinguir entre diferentes versões
2. **Matching Automático**: Melhora na identificação automática de metadados
3. **Organização Visual**: Mais fácil identificar filmes visualmente
4. **Compatibilidade**: Formato padrão usado por bibliotecas de mídia

## Categorias Afetadas

- **Movie**: Inclui ano no nome do arquivo e pasta
- **Adult**: Inclui ano no nome do arquivo e pasta (para consistência)

## Categorias Não Afetadas

- **Series**: Já usam formato S##E## que inclui informação de temporada
- **Novela**: Já usam formato S##E##
- **Cartoon**: Já usam formato S##E##
- **Documentary**: Já usam formato S##E##
- **Educational**: Já usam formato S##E##
- **Sports**: Geralmente são eventos únicos, ano não crítico
- **TV**: Canais ao vivo, não aplicável

## Compatibilidade com Jellyfin

O formato `Nome (Ano).ext` é o padrão recomendado pelo Jellyfin para identificação de filmes. Isso permite:

- Matching automático com TMDB
- Evita conflitos entre filmes com mesmo nome
- Facilita a organização da biblioteca

## Processo de Migração

### Para Filmes Novos
Basta exportar normalmente. O sistema automaticamente incluirá o ano no nome.

### Para Filmes Já Exportados
1. Use o script `reexport_movies_with_year.py`
2. Ou enriqueça com ano do TMDB via API
3. Reexporte via interface web

## Considerações

### Filmes Sem Ano
Se um filme não tiver ano no nome e o TMDB não encontrar, o arquivo será exportado sem ano. Neste caso:

- O arquivo ainda funcionará no Jellyfin
- A identificação pode ser menos precisa
- Pode-se enriquecer posteriormente quando mais informações estiverem disponíveis

### Performance
- A inclusão de ano não afeta a performance
- O cálculo de hash já considera o ano
- A exportação incremental funciona normalmente

## Troubleshooting

### Arquivo Não Tem Ano
1. Verifique se o ano foi extraído do nome original
2. Use `GET /api/enrich/check-missing-years` para verificar
3. Enriqueça com TMDB via `POST /api/enrich/years-from-tmdb`
4. Reexporte o filme

### Conflito de Nomes
Se houver conflito (ex: dois filmes com mesmo nome e ano), o sistema:
- Mantém o primeiro exportado
- Marca duplicados com base no hash
- Permite seleção manual via interface

## Status

✅ Implementado e testado
✅ Compatível com Jellyfin
✅ Retroativo (pode reexportar filmes existentes)
✅ Não afeta performance
