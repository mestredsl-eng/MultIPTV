# Gerador TV M3U + EPG para Jellyfin

## Visão Geral
Sistema para gerar playlists TV M3U e guias EPG XMLTV compatíveis com Jellyfin usando as TVs da database que não estão na blacklist.

## Funcionalidade

### Botão na Página de Manutenção
**Localização**: Menu > Manutenção > Botão "Gerar TV M3U + EPG"

**Função**:
- Gera arquivo `tv.m3u` com todas as TVs ativas e não blacklist
- Gera arquivo `epg.xml` com guia de programação
- Formato compatível com Jellyfin
- Integra com fontes EPG das IPTVs configuradas

## Formato de Saída

### TV M3U (tv.m3u)
Formato M3U compatível com Jellyfin:

```m3u
#EXTM3U
#EXTINF:0,Mestre IPTV TV Channels

#EXTINF:-1 tvg-id="Globo" tvg-logo="http://example.com/logo.png" tvg-name="Globo",Globo
http://example.com/globo.m3u8

#EXTINF:-1 tvg-id="Record" tvg-logo="http://example.com/record.png" tvg-name="Record",Record
http://example.com/record.m3u8
```

**Características**:
- Formato `#EXTINF:-1` compatível com Jellyfin
- `tvg-id`: Identificador do canal (usa tvg_id ou nome)
- `tvg-logo`: URL do logotipo do canal
- `tvg-name`: Nome do canal para Jellyfin
- URL de streaming na linha seguinte

### EPG XMLTV (epg.xml)
Formato XMLTV padrão:

```xml
<?xml version="1.0" encoding="utf-8"?>
<tv generator-info-name="Mestre IPTV Manager" generator-info-url="https://github.com">
  <channel id="Globo">
    <display-name>Globo</display-name>
  </channel>
  <programme channel="Globo" start="20240101000000 +0000" stop="20240101010000 +0000">
    <title>Jornal Nacional</title>
    <desc>Jornal noticioso</desc>
  </programme>
</tv>
```

## Como Usar

### Via Interface Web
1. Acessar página Manutenção
2. Clicar em "Gerar TV M3U + EPG" (botão verde)
3. Confirmar operação
4. Aguardar conclusão
5. Ver estatísticas e caminhos dos arquivos

### Via API
```bash
curl -X POST http://localhost:5000/api/maintenance/generate-tv-m3u \
  -H "Content-Type: application/json" \
  -d '{"output_dir": "jellyfin_package"}'
```

**Response**:
```json
{
  "success": true,
  "message": "Pacote Jellyfin gerado em 3s",
  "stats": {
    "total_channels": 150,
    "m3u_path": "/path/to/jellyfin_package/tv.m3u",
    "epg_path": "/path/to/jellyfin_package/epg.xml",
    "m3u_success": true,
    "epg_success": true,
    "duration": 3
  }
}
```

## Configuração no Jellyfin

### 1. Adicionar Fonte de TV
1. Abrir Jellyfin
2. Ir para Settings > Live TV & DVR
3. Clicar em "+ Add TV Source"
4. Selecionar "M3U Tuner"

### 2. Configurar Arquivos
**M3U Playlist URL**:
- URL local: `file:///path/to/jellyfin_package/tv.m3u`
- Ou copiar arquivo para pasta acessível pelo Jellyfin

**EPG URL**:
- URL local: `file:///path/to/jellyfin_package/epg.xml`
- Ou copiar arquivo para pasta acessível pelo Jellyfin

### 3. Mapeamento de Canais
O sistema inclui automaticamente:
- `tvg-id`: Para matching com EPG
- `tvg-name`: Nome do canal para Jellyfin
- `tvg-logo`: Logotipo do canal

## Integração com Sistema Existente

### Fontes de Dados
- **Database**: Usa tabela `tv_channels`
- **Filtro**: Apenas `status = 1` e `black_list = 0`
- **EPG Sources**: Usa `url_epg` das fontes IPTV

### Caches EPG
- Localização: `cache/epg/`
- Duração: 6 horas
- Formato: XML (suporta .gz)

## Estrutura de Arquivos

```
mestre-IPTV/
├── jellyfin_package/
│   ├── tv.m3u          # Playlist de canais TV
│   └── epg.xml         # Guia de programação
├── app/
│   └── services/
│       ├── tv_m3u_generator.py    # Serviço de geração
│       ├── epg.py                 # Serviço EPG básico
│       └── epg_fetcher.py         # Fetcher EPG avançado
└── database/
    └── iptv.db                    # Database com TVs
```

## Filtragem de Canais

### Canais Incluídos
```sql
WHERE status = 1           -- Ativo
AND black_list = 0        -- Não blacklist
```

### Canais Excluídos
- Status = 0 (inativos)
- Black_list = 1 (blacklist)
- Sem URL

## Características do EPG

### Download Automático
- Baixa EPG de todas as fontes IPTV configuradas
- Usa cache de 6 horas
- Suporta arquivos .gz comprimidos

### Matching Inteligente
- Usa nome do canal para matching
- Case-insensitive
- Substring matching (busca parcial)

### Mesclagem de Fontes
- Combina EPG de múltiplas fontes
- Remove duplicados por tvg-id
- Prioriza fontes com melhor matching

## Troubleshooting

### Nenhum Canal Encontrado
**Causa**: Nenhuma TV ativa na database

**Solução**:
1. Verificar se há canais TV processados
2. Verificar se não estão na blacklist
3. Verificar status = 1

### EPG Vazio
**Causa**: Nenhuma fonte EPG configurada

**Solução**:
1. Adicionar URL EPG nas fontes IPTV
2. Verificar se URLs são acessíveis
3. Baixar EPG manualmente via "Baixar EPG"

### Jellyfin Não Reconhece Canais
**Causa**: Formato M3U incompatível

**Solução**:
1. Verificar se arquivo tv.m3u foi gerado corretamente
2. Validar formato M3U
3. Verificar tvg-id está correto
4. Tentar importar manualmente no Jellyfin

### EPG Não Funciona
**Causa**: tvg-id não bate com EPG

**Solução**:
1. Verificar se tvg-id está preenchido no banco
2. Verificar se EPG foi gerado corretamente
3. Validar arquivo epg.xml
4. Usar nome do canal como tvg-id alternativo

## Performance

### Tempos Estimados
- **Geração TV M3U**: ~1-2 segundos
- **Download EPG**: ~10-30 segundos (depende das fontes)
- **Parsing EPG**: ~5-10 segundos
- **Total**: ~15-45 segundos

### Fatores que Afetam
- Quantidade de canais TV
- Número de fontes EPG
- Tamanho dos arquivos EPG
- Velocidade da internet
- Cache EPG disponível

## Boas Práticas

1. **Verificar Canais**: Antes de gerar, verificar se há canais TV ativos
2. **Limpar Blacklist**: Remover canais indesejados da blacklist
3. **Configurar EPG**: Ter fontes EPG confiáveis
4. **Testar Importação**: Importar manualmente no Jellyfin primeiro
5. **Monitorar Logs**: Verificar erros durante geração

## Logs e Monitoramento

### Logs do Sistema
Processo é logado em `app/logs/process.log`:
```
INFO - Gerando tv.m3u com 150 canais
INFO - TV M3U gerado com sucesso: 150 canais
INFO - EPG sources encontradas: 3
INFO - Baixando EPG de http://example.com/epg.xml
INFO - EPG XMLTV gerado com sucesso
INFO - Pacote Jellyfin gerado com sucesso
```

### Logs via Interface
Acessar página de Logs para acompanhar em tempo real.

## Exemplos de Uso

### Geração Completa
```bash
# Via API
curl -X POST http://localhost:5000/api/maintenance/generate-tv-m3u \
  -H "Content-Type": application/json" \
  -d '{"output_dir": "jellyfin_package"}'

# Via interface
# Menu > Manutenção > Gerar TV M3U + EPG
```

### Diretório Personalizado
```bash
curl -X POST http://localhost:5000/api/maintenance/generate-tv-m3u \
  -H "Content-Type": application/json" \
  -d '{"output_dir": "custom_folder"}'
```

## Compatibilidade

### Jellyfin
- ✅ Compatível com Live TV & DVR
- ✅ Suporta tvg-id, tvg-name, tvg-logo
- ✅ Formato M3U padrão
- ✅ EPG XMLTV padrão

### Outros Players
- ✅ Kodi
- ✅ VLC
- ✅ Emby
- ✅ Plex (limitado)

## Limitações

### Fontes EPG
- Deve ser configurado manualmente nas IPTVs
- Nem todas as fontes são confiáveis
- Dados podem estar desatualizados

### Matching de Canais
- Baseado em nome (pode ter erros)
- Case-insensitive pode causar falsos positivos
- Nem todos os canais têm EPG

## Status

✅ Serviço de geração implementado
✅ Endpoint API criado
✅ Botão na interface web
✅ Formato compatível com Jellyfin
✅ Integração com EPG existente
✅ Filtragem de blacklist
✅ Cache inteligente
