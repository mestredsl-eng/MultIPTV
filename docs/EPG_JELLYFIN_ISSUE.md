# Problema EPG no Jellyfin - Análise e Soluções

## Problema Identificado

O EPG não está funcionando no Jellyfin devido a **mismatch entre os IDs dos canais** no arquivo M3U e no arquivo EPG XML.

## Análise Detalhada

### 1. EPG Original (cache/epg/16d66a1ebf794c1facb951fb62b3e961.xml)
```xml
<channel id="Ae.br">
    <display-name>A&amp;E FHD</display-name>
</channel>
```
- **Channel ID**: `Ae.br` (sem & codificado)
- **Display Name**: `A&amp;E FHD` (com & codificado como &amp;)

### 2. EPG Gerado (d:\Galeria\TV\epg.xml)
```xml
<channel id="a&amp;e-4k">
    <display-name>A&amp;E 4K</display-name>
</channel>
```
- **Channel ID**: `a&amp;e-4k` (com & codificado como &amp;)
- **Display Name**: `A&amp;E 4K` (com & codificado como &amp;)

### 3. TV M3U Gerado (d:\Galeria\TV\tv.m3u)
```m3u
#EXTINF:-1 tvg-id="a&e-4k" tvg-name="A&E 4K",A&E 4K
http://185.66.90.136:80/a90049896/112233Aa/90647.ts
```
- **tvg-id**: `a&e-4k` (com & NÃO codificado)
- **tvg-name**: `A&E 4K` (com & NÃO codificado)

## Causa Raiz

### Problema Principal: Mismatch de Codificação
- **EPG XML**: `a&amp;e-4k` (ElementTree codifica & como &amp; automaticamente)
- **M3U**: `a&e-4k` (sem codificação)

O Jellyfin precisa que o `tvg-id` no M3U corresponda **EXATAMENTE** ao `channel id` no EPG XML. Como um tem `&amp;` e o outro tem `&`, o matching falha.

### Problemas Secundários

1. **IDs Não Preservados**: O sistema não está preservando o channel ID original do EPG (`Ae.br`), está gerando novos IDs baseados no nome do canal

2. **Matching por Substring**: O matching entre canais do EPG original e do banco é baseado em substring do nome, o que pode causar falsos positivos

3. **Geração de ID Própria**: O sistema está criando seus próprios IDs em vez de usar os IDs do EPG original

## Soluções Propostas

### Solução 1: Normalizar IDs no M3U (Recomendada)

Modificar `app/services/tv_m3u_generator.py` para codificar caracteres especiais no tvg-id:

```python
import html

def generate_tv_m3u(db, output_path: Path, epg_path: Path = None) -> dict:
    # ... código existente ...
    
    for channel in channels:
        # ... código existente ...
        
        # Normalizar tvg_id para XML (codificar & como &amp;)
        if tvg_id:
            tvg_id = html.escape(tvg_id)
        else:
            tvg_id = html.escape(channel_name)
        
        # ... resto do código ...
```

**Vantagens**:
- Mudança mínima
- Compatível com XML
- Padrão XMLTV

**Desvantagens**:
- Pode quebrar compatibilidade com outros players que esperam & não codificado

### Solução 2: Usar IDs do EPG Original (Melhor Solução)

Modificar o sistema para:
1. Extrair e armazenar o channel ID original do EPG na tabela `tv_channels`
2. Usar esse ID tanto no M3U quanto no EPG gerado

Passos:

1. **Adicionar coluna `epg_channel_id` na tabela `tv_channels`**:
```sql
ALTER TABLE tv_channels ADD COLUMN epg_channel_id TEXT;
```

2. **Modificar o parser para extrair o tvg-id do M3U original**:
```python
# Em app/services/parser.py
def parse_extinf(line):
    # ... código existente ...
    
    # Extract tvg-id
    match = re.search(r'tvg-id="([^"]*)"', line)
    if match:
        entry['tvg_id'] = match.group(1)
    
    return entry
```

3. **Modificar `tv_m3u_generator.py` para usar epg_channel_id**:
```python
def generate_tv_m3u(db, output_path: Path, epg_path: Path = None) -> dict:
    channels = db.execute('''
        SELECT id, nome_canal, url, logo_url, categoria, tvg_id, epg_channel_id
        FROM tv_channels
        WHERE status = 1 AND black_list = 0
        ORDER BY nome_canal
    ''').fetchall()
    
    for channel in channels:
        # Usar epg_channel_id se disponível, senão tvg_id, senão nome
        channel_id = channel['epg_channel_id'] or channel['tvg_id'] or channel['nome_canal']
        # ... resto do código ...
```

4. **Modificar `generate_epg_xmltv` para usar epg_channel_id**:
```python
def generate_epg_xmltv(db, output_path: Path, epg_sources: list = None) -> dict:
    channels = db.execute('''
        SELECT id, nome_canal, tvg_id, epg_channel_id, url
        FROM tv_channels
        WHERE status = 1 AND black_list = 0
        ORDER BY nome_canal
    ''').fetchall()
    
    for channel in channels:
        # Usar epg_channel_id se disponível
        channel_id = channel['epg_channel_id'] or channel['tvg_id'] or str(channel['id'])
        # ... resto do código ...
```

**Vantagens**:
- Preserva IDs originais do EPG
- Melhor matching com fontes EPG
- Mais robusto

**Desvantagens**:
- Requer migração de banco de dados
- Requer reprocessamento de M3U para extrair tvg-id

### Solução 3: Desabilitar Codificação Automática do ElementTree

Modificar `generate_epg_xmltv` para escrever XML sem codificação automática:

```python
def generate_epg_xmltv(db, output_path: Path, epg_sources: list = None) -> dict:
    # ... código existente ...
    
    # Escrever XML manualmente para evitar codificação automática
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="utf-8"?>\n')
        f.write('<tv generator-info-name="Mestre IPTV Manager" generator-info-url="https://github.com">\n')
        
        for channel in channels:
            channel_id = channel['tvg_id'] if channel['tvg_id'] else str(channel['id'])
            f.write(f'  <channel id="{channel_id}">\n')
            f.write(f'    <display-name>{channel_name}</display-name>\n')
            f.write('  </channel>\n')
            # ... programas ...
        
        f.write('</tv>\n')
```

**Vantagens**:
- IDs consistentes entre M3U e EPG
- Mudança simples

**Desvantagens**:
- XML pode não ser válido se tiver caracteres especiais
- Perde benefícios do ElementTree

### Solução 4: Usar Apenas Nome do Canal como ID (Solução Rápida)

Usar apenas o nome do canal normalizado como ID em ambos os arquivos:

```python
def normalize_channel_id(name):
    """Normaliza nome do canal para usar como ID."""
    import re
    # Remove espaços, caracteres especiais, converte para minúsculas
    return re.sub(r'[^a-z0-9]', '', name.lower())

# No M3U
channel_id = normalize_channel_id(channel_name)

# No EPG
channel_id = normalize_channel_id(channel_name)
```

**Vantagens**:
- Simples
- Consistente
- Funciona mesmo sem tvg-id

**Desvantagens**:
- Perde informação do EPG original
- Pode ter colisões se nomes forem similares

## Recomendação

**Solução 2 (Usar IDs do EPG Original)** é a melhor solução a longo prazo, pois:
1. Preserva a integridade dos dados originais
2. Melhora o matching com fontes EPG
3. É mais robusto e escalável

**Solução 1 (Normalizar IDs no M3U)** é a solução mais rápida para implementar agora, pois:
1. Requer mudança mínima
2. Resolve o problema imediato
3. Não requer migração de banco

## Implementação Imediata (Solução 1)

Modificar `app/services/tv_m3u_generator.py`:

```python
import html

def generate_tv_m3u(db, output_path: Path, epg_path: Path = None) -> dict:
    try:
        channels = db.execute('''
            SELECT id, nome_canal, url, logo_url, categoria, tvg_id
            FROM tv_channels
            WHERE status = 1 AND black_list = 0
            ORDER BY nome_canal
        ''').fetchall()

        total_channels = len(channels)
        if total_channels == 0:
            logger.warning("Nenhum canal TV encontrado no banco")
            return {
                'success': False,
                'total_channels': 0,
                'error': 'Nenhum canal TV encontrado'
            }

        logger.info(f"Gerando tv.m3u com {total_channels} canais")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('#EXTM3U\n')
            f.write('#EXTINF:0,Mestre IPTV TV Channels\n\n')

            for channel in channels:
                channel_id_db = channel['id']
                channel_name = channel['nome_canal']
                url = channel['url']
                logo_url = channel['logo_url'] if 'logo_url' in channel.keys() else ''
                categoria = channel['categoria'] if 'categoria' in channel.keys() else ''
                tvg_id = channel['tvg_id'] if 'tvg_id' in channel.keys() else ''

                # Normalizar tvg_id para XML (codificar & como &amp;)
                if tvg_id:
                    tvg_id_normalized = html.escape(tvg_id)
                else:
                    tvg_id_normalized = html.escape(channel_name)

                extinf_line = '#EXTINF:-1'
                extinf_line += f' tvg-id="{tvg_id_normalized}"'

                if logo_url:
                    extinf_line += f' tvg-logo="{logo_url}"'

                extinf_line += f' tvg-name="{channel_name}"'
                extinf_line += f',{channel_name}'

                f.write(extinf_line + '\n')
                f.write(url + '\n\n')

        logger.info(f"tv.m3u gerado com sucesso: {total_channels} canais")

        return {
            'success': True,
            'total_channels': total_channels,
            'output_path': str(output_path)
        }

    except Exception as e:
        logger.error(f"Erro ao gerar tv.m3u: {e}")
        return {
            'success': False,
            'error': str(e)
        }
```

## Teste Após Implementação

1. Regenerar TV M3U e EPG:
   - Via interface: Menu > Manutenção > Gerar TV M3U + EPG
   - Ou via API: `POST /api/maintenance/generate-tv-m3u`

2. Verificar se os IDs correspondem:
   ```bash
   # Verificar M3U
   type d:\Galeria\TV\tv.m3u | findstr "tvg-id"
   
   # Verificar EPG
   type d:\Galeria\TV\epg.xml | findstr "channel id="
   ```

3. Testar no Jellyfin:
   - Adicionar fonte de TV no Jellyfin
   - Apontar para o novo tv.m3u
   - Apontar para o novo epg.xml
   - Verificar se o guia de programação aparece

## Informações Adicionais

### Por que o ElementTree codifica & como &amp;?

Isso é um requisito do padrão XML. O caractere `&` é reservado em XML e deve ser codificado como `&amp;`. O ElementTree faz isso automaticamente para garantir XML válido.

### Por que o M3U não codifica?

O formato M3U é baseado em texto simples e não tem os mesmos requisitos de codificação que XML. Caracteres especiais como `&` podem ser usados diretamente.

### Outros caracteres que podem causar problemas

- `<` → `&lt;`
- `>` → `&gt;`
- `"` → `&quot;`
- `'` → `&apos;`

## Conclusão

O problema é um mismatch de codificação entre o M3U e o EPG XML. A solução mais rápida é normalizar os IDs no M3U para usar a mesma codificação que o XML. A solução mais robusta a longo prazo é preservar os IDs originais do EPG e usá-los consistentemente.
