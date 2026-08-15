# API Documentation - Mestre IPTV Manager

## Overview
REST API endpoints for the Mestre IPTV Manager web application. All endpoints return JSON responses.

**Base URL**: `http://localhost:5000/api`

**Content-Type**: `application/json`

---

## IPTV Sources Management

### Get All IPTV Sources
**GET** `/api/iptv/sources`

Retrieve all registered IPTV sources with media counts and formatted dates.

**Response**:
```json
[
  {
    "id": 1,
    "nome": "My IPTV",
    "url_m3u": "http://example.com/playlist.m3u",
    "url_epg": "http://example.com/epg.xml",
    "ativo": 1,
    "data_cadastro": "2024-01-01 10:00:00",
    "ultima_atualizacao": "01/01/2024 10:00",
    "media_count": 1500
  }
]
```

### Create IPTV Source
**POST** `/api/iptv/sources`

Register a new IPTV source.

**Request Body**:
```json
{
  "nome": "My IPTV",
  "url_m3u": "http://example.com/playlist.m3u",
  "url_epg": "http://example.com/epg.xml"
}
```

**Response**:
```json
{
  "success": true,
  "id": 1
}
```

### Delete IPTV Source
**DELETE** `/api/iptv/sources/<int:iptv_id>`

Soft delete an IPTV source (sets ativo=0 and blacklists associated media).

**Response**:
```json
{
  "success": true,
  "affected_media": 1500
}
```

### Toggle IPTV Source Status
**POST** `/api/iptv/sources/<int:iptv_id>/toggle-status`

Toggle the active status of an IPTV source.

**Response**:
```json
{
  "success": true,
  "new_status": 0
}
```

### Check Duplicate Name
**POST** `/api/iptv/check-duplicate`

Check if an IPTV source name already exists.

**Request Body**:
```json
{
  "nome": "My IPTV"
}
```

**Response**:
```json
{
  "exists": false
}
```

---

## Dashboard Statistics

### Get Dashboard Stats
**GET** `/api/iptv/stats`

Get comprehensive dashboard statistics.

**Response**:
```json
{
  "iptvs": 5,
  "midias": 15000,
  "filmes": 5000,
  "series": 3000,
  "series_unique": 250,
  "tv": 2000,
  "tv_channels": 2000,
  "duplicados": 150,
  "blacklist": 500,
  "adult": 200,
  "educational": 500,
  "educational_unique": 50,
  "documentary": 800,
  "documentary_unique": 80,
  "cartoon": 1200,
  "cartoon_unique": 120,
  "novela": 300,
  "novela_unique": 30,
  "sports": 1500,
  "exportados": 10000,
  "tmdb_cache": 4500,
  "not_exported": 5000
}
```

### Get Recent Activity
**GET** `/api/dashboard/activity`

Get recent processing activity.

**Query Parameters**:
- `limit` (optional): Number of entries to return (default: 10)

**Response**:
```json
[
  {
    "etapa": "download",
    "inicio": "2024-01-01 10:00:00",
    "fim": "2024-01-01 10:05:00",
    "status": "completed"
  }
]
```

### Get Category Data
**GET** `/api/dashboard/category`

Get media items by category.

**Query Parameters**:
- `category`: Category name (Movie, Series, TV, etc.)
- `black_list` (optional): Filter by blacklist status (0 or 1)
- `limit` (optional): Number of items to return (default: 100)

**Response**:
```json
[
  {
    "id": 1,
    "nome_da_midia": "Matrix",
    "categoria": "Movie",
    "ano": 1999,
    "black_list": 0
  }
]
```

---

## Process Management

### Get Process Status
**GET** `/api/process/status`

Get current process status.

**Response**:
```json
{
  "id": 1,
  "etapa": "download",
  "progresso": 50,
  "mensagem": "Baixando M3U...",
  "inicio": "2024-01-01 10:00:00",
  "fim": null,
  "status": "running"
}
```

### Download M3U
**POST** `/api/process/download`

Download M3U files from all active IPTV sources.

**Response**:
```json
{
  "success": true,
  "message": "Download concluído: 5 arquivos baixados"
}
```

### Classify Media
**POST** `/api/process/classify`

Classify parsed media entries into categories.

**Response**:
```json
{
  "success": true,
  "message": "Classificação concluída: 150 novas mídias, 200 ignoradas"
}
```

### Classify with TMDB
**POST** `/api/process/classify-with-tmdb`

Classify media with automatic TMDB enrichment for movies.

**Response**:
```json
{
  "success": true,
  "message": "Classificação concluída: 150 novas mídias, 200 ignoradas, 120 enriquecidas com TMDB"
}
```

### Classify Bulk
**POST** `/api/process/classify-bulk`

Optimized bulk classification with batch processing.

**Request Body**:
```json
{
  "batch_size": 500
}
```

**Response**:
```json
{
  "success": true,
  "message": "Classificação concluída: 150 novas mídias, 200 ignoradas"
}
```

### Classify Bulk with TMDB
**POST** `/api/process/classify-bulk-tmdb`

Optimized bulk classification with TMDB enrichment.

**Request Body**:
```json
{
  "batch_size": 500,
  "enable_tmdb": true
}
```

**Response**:
```json
{
  "success": true,
  "message": "Classificação concluída com enriquecimento TMDB: 150 novas mídias, 200 ignoradas"
}
```

### Create Void (Export)
**POST** `/api/process/create-void`

Export media to STRM files in the gallery.

**Response**:
```json
{
  "success": true,
  "message": "Exportação concluída: 500 arquivos STRM gerados"
}
```

---

## Maintenance Operations

### Get Maintenance Stats
**GET** `/api/maintenance/stats`

Get maintenance statistics.

**Response**:
```json
{
  "total_midias": 15000,
  "duplicates": 150,
  "orphans": 50,
  "blacklisted": 500
}
```

### Fix Name Duplicates
**POST** `/api/maintenance/fix-name-duplicates`

Fix duplicate media entries by name.

**Response**:
```json
{
  "success": true,
  "fixed": 100
}
```

### Fix Quality Duplicates
**POST** `/api/maintenance/fix-quality-duplicates`

Fix duplicate media entries by quality indicators.

**Response**:
```json
{
  "success": true,
  "fixed": 50
}
```

### Cleanup Orphans
**POST** `/api/maintenance/cleanup-orphans`

Clean up orphaned database records.

**Response**:
```json
{
  "success": true,
  "cleaned": 30
}
```

### Reset Exported
**POST** `/api/maintenance/reset-exported`

Reset the exported media tracking table.

**Response**:
```json
{
  "success": true,
  "message": "Tabela exported_media resetada com sucesso"
}
```

### Fix Duplicates
**POST** `/api/maintenance/fix-duplicates`

Fix all duplicate media entries.

**Response**:
```json
{
  "success": true,
  "fixed": 200
}
```

### Clean Gallery
**POST** `/api/maintenance/clean-gallery`

Clean up the gallery directory.

**Response**:
```json
{
  "success": true,
  "cleaned": 100
}
```

### Clean Gallery Duplicates
**POST** `/api/maintenance/clean-gallery-duplicates`

Clean up duplicate files in the gallery.

**Response**:
```json
{
  "success": true,
  "cleaned": 50
}
```

### Clean URL Duplicates
**POST** `/api/maintenance/clean-url-duplicates`

Clean up duplicate URLs in the database.

**Response**:
```json
{
  "success": true,
  "cleaned": 75
}
```

### Download EPG
**POST** `/api/maintenance/download-epg`

Download EPG files from configured sources.

**Response**:
```json
{
  "success": true,
  "message": "EPG baixado com sucesso"
}
```

### Generate TV M3U
**POST** `/api/maintenance/generate-tv-m3u`

Generate TV M3U playlist and EPG XML for Jellyfin.

**Request Body**:
```json
{
  "output_dir": "jellyfin_package"
}
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

### Enrich TMDB
**POST** `/api/maintenance/enrich-tmdb`

Enrich movies with TMDB data (legacy endpoint).

**Response**:
```json
{
  "success": true,
  "enriched": 100
}
```

---

## Reclassification

### Reclassify Single Item
**POST** `/api/reclassify/single`

Reclassify a single media item.

**Request Body**:
```json
{
  "media_id": 1,
  "new_category": "Series"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Mídia reclassificada com sucesso"
}
```

### Reclassify Batch
**POST** `/api/reclassify/batch`

Reclassify multiple media items in batch.

**Request Body**:
```json
{
  "media_ids": [1, 2, 3],
  "new_category": "Series"
}
```

**Response**:
```json
{
  "success": true,
  "reclassified": 3
}
```

### Analyze Reclassifications
**POST** `/api/reclassify/analyze`

Analyze potential reclassifications without applying changes.

**Request Body**:
```json
{
  "category": "Movie",
  "target_category": "Series"
}
```

**Response**:
```json
{
  "success": true,
  "potential_changes": 50,
  "examples": [
    {"id": 1, "name": "Example Movie", "current": "Movie", "suggested": "Series"}
  ]
}
```

---

## TMDB Enrichment

### Check Missing Years
**GET** `/api/enrich/check-missing-years`

Check how many movies are missing year information.

**Response**:
```json
{
  "total_movies": 1500,
  "with_year": 1200,
  "without_year": 300,
  "examples": ["Frozen", "Avatar", "Titanic"]
}
```

### Enrich Years from TMDB
**POST** `/api/enrich/years-from-tmdb`

Enrich movies with year data from TMDB.

**Request Body**:
```json
{
  "limit": 100
}
```

**Response**:
```json
{
  "success": true,
  "updated": 95,
  "not_found": 5,
  "errors": 0
}
```

### Enrich All Years from TMDB
**POST** `/api/enrich/years-from-tmdb-all`

Enrich ALL movies with year data from TMDB (no limit).

**Response**:
```json
{
  "success": true,
  "updated": 285,
  "not_found": 15,
  "errors": 0,
  "duration": 120
}
```

### Get TMDB Progress
**GET** `/api/enrich/tmdb-progress`

Get progress of ongoing TMDB enrichment.

**Response**:
```json
{
  "total": 300,
  "processed": 150,
  "updated": 140,
  "not_found": 10,
  "percentage": 50
}
```

---

## Settings Management

### Get TMDB Settings
**GET** `/api/settings/tmdb`

Get TMDB configuration settings.

**Response**:
```json
{
  "tmdb_api_key": "your-api-key",
  "tmdb_cache_duration": 2592000
}
```

### Update TMDB Settings
**POST** `/api/settings/tmdb`

Update TMDB configuration settings.

**Request Body**:
```json
{
  "tmdb_api_key": "new-api-key",
  "tmdb_cache_duration": 2592000
}
```

**Response**:
```json
{
  "success": true,
  "message": "Configurações TMDB atualizadas"
}
```

### Test TMDB API Key
**POST** `/api/settings/test-tmdb`

Test if the TMDB API key is valid.

**Response**:
```json
{
  "success": true,
  "valid": true,
  "message": "API Key válida"
}
```

### Get Database Settings
**GET** `/api/settings/database`

Get database configuration settings.

**Response**:
```json
{
  "database_timeout": 120
}
```

### Update Database Settings
**POST** `/api/settings/database`

Update database configuration settings.

**Request Body**:
```json
{
  "database_timeout": 120
}
```

**Response**:
```json
{
  "success": true,
  "message": "Configurações de banco atualizadas"
}
```

### Get Path Settings
**GET** `/api/settings/path`

Get path configuration settings.

**Response**:
```json
{
  "galeria_path": "D:/Galeria"
}
```

### Update Path Settings
**POST** `/api/settings/path`

Update path configuration settings.

**Request Body**:
```json
{
  "galeria_path": "D:/Galeria"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Configurações de caminho atualizadas"
}
```

### Test Path
**POST** `/api/settings/test-path`

Test if a path is valid and accessible.

**Request Body**:
```json
{
  "path": "D:/Galeria"
}
```

**Response**:
```json
{
  "success": true,
  "valid": true,
  "writable": true,
  "message": "Caminho válido e acessível"
}
```

---

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "success": false,
  "error": "Error message description"
}
```

### Common Error Codes
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

---

## Rate Limiting

Currently, there is no rate limiting implemented. Consider implementing rate limiting for production use.

---

## Authentication

**Note**: The API currently does not require authentication. This is a security concern for production deployments. Implement authentication before deploying to production.

---

## WebSocket/SSE Endpoints

### Process Progress Stream
**Endpoint**: `/api/process/stream`

Server-Sent Events (SSE) endpoint for real-time process progress updates.

**Usage**:
```javascript
const eventSource = new EventSource('/api/process/stream');
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Progress:', data);
};
```

**Event Data**:
```json
{
  "etapa": "download",
  "progresso": 50,
  "mensagem": "Baixando M3U...",
  "status": "running"
}
```

---

## TMDB Validation

### Validate Short Names
**POST** `/api/validation/validate-short-names`

Validate Movie items with ≤2 words using TMDB with automatic name correction and deduplication.

**Response**:
```json
{
  "success": true,
  "message": "Validação concluída: 150 validados, 12 não encontrados, 5 duplicatas removidas",
  "stats": {
    "total": 167,
    "validated": 150,
    "not_found": 12,
    "errors": 0,
    "corrected": 45,
    "deduplicated": 5
  }
}
```

### Get Validation Progress
**GET** `/api/validation/progress`

Get current TMDB validation progress.

**Response**:
```json
{
  "success": true,
  "progress": 65,
  "message": "Validando 108/167 itens...",
  "status": "running"
}
```

### Blacklist Unvalidated
**POST** `/api/validation/blacklist-unvalidated`

Send non-validated Movie items to blacklist.

**Response**:
```json
{
  "success": true,
  "message": "12 itens enviados para blacklist",
  "blacklisted": 12
}
```

### Get Validation Stats
**GET** `/api/validation/stats`

Get TMDB validation statistics.

**Response**:
```json
{
  "success": true,
  "stats": {
    "movies_total": 5000,
    "movies_needing_validation": 150,
    "movies_validated": 4850,
    "movies_not_found": 12
  }
}
```

---

### Complete Workflow Example

```bash
# 1. Add IPTV source
curl -X POST http://localhost:5000/api/iptv/sources \
  -H "Content-Type: application/json" \
  -d '{"nome": "My IPTV", "url_m3u": "http://example.com/playlist.m3u", "url_epg": "http://example.com/epg.xml"}'

# 2. Download M3U
curl -X POST http://localhost:5000/api/process/download

# 3. Classify with TMDB
curl -X POST http://localhost:5000/api/process/classify-with-tmdb

# 4. Export to gallery
curl -X POST http://localhost:5000/api/process/create-void

# 5. Check stats
curl http://localhost:5000/api/iptv/stats
```

### TMDB Enrichment Example

```bash
# Check missing years
curl http://localhost:5000/api/enrich/check-missing-years

# Enrich all movies
curl -X POST http://localhost:5000/api/enrich/years-from-tmdb-all \
  -H "Content-Type: application/json" \
  -d '{}'

# Monitor progress
curl http://localhost:5000/api/enrich/tmdb-progress
```

---

## Version Information

**API Version**: 1.0.0

**Last Updated**: 2024

**Compatibility**: Flask 3.0.0, Python 3.8+
