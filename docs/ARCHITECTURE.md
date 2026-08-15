# Architecture Overview - Mestre IPTV Manager

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Web Interface (Flask)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │Dashboard │ │ Process  │ │Maintenance│ │Settings  │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                    │
│  │Registration│ │   Logs   │ │   API    │                    │
│  └──────────┘ └──────────┘ └──────────┘                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │   Routes    │ │  Services   │ │ Background  │           │
│  │  (Blueprint)│ │  (Business) │ │   Thread    │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Access Layer                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │   Models    │ │   Queries   │ │ Retry Helper│           │
│  │  (Dataclass)│ │  (SQL)      │ │  (Lock Mgmt)│           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Database Layer (SQLite)                    │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐            │
│  │  iptvs  │ │ midias  │ │tv_channels│ │tmdb_cache│            │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘            │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐            │
│  │exported  │ │export_  │ │process_ │ │system_  │            │
│  │ _media   │ │  lock   │ │  status │ │settings │            │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    External Services                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                    │
│  │   TMDB   │ │ IPTV Src │ │  EPG Src │                    │
│  │   API    │ │  (M3U)   │ │  (XMLTV) │                    │
│  └──────────┘ └──────────┘ └──────────┘                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    File System                                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                    │
│  │ Gallery  │ │  Cache   │ │  Backup  │                    │
│  │ (STRM)   │ │  (M3U)   │ │  (DB)    │                    │
│  └──────────┘ └──────────┘ └──────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

## Component Overview

### 1. Web Interface Layer

**Framework**: Flask 3.0.0 with Bootstrap 5

**Templates**:
- `base.html` - Base template with navigation and theme
- `dashboard.html` - Statistics and activity overview
- `process.html` - Process controls and real-time progress
- `maintenance.html` - Maintenance tools and utilities
- `registration.html` - IPTV source management
- `settings.html` - System configuration
- `logs.html` - Log viewer

**Static Assets**:
- Custom CSS with dark/light themes
- Bootstrap Icons
- Chart.js for visualizations
- JavaScript for real-time updates

### 2. Application Layer

#### Routes (Blueprints)
- `dashboard.py` - Dashboard endpoints
- `process.py` - Process control endpoints
- `maintenance.py` - Maintenance endpoints
- `registration.py` - IPTV registration endpoints
- `logs.py` - Log viewing endpoints
- `api.py` - REST API endpoints
- `settings.py` - Settings management endpoints

#### Services (Business Logic)
- `parser.py` - M3U parsing and hash calculation
- `classifier.py` - Media classification by category
- `reclassifier.py` - Advanced reclassification with scoring
- `deduplicator.py` - TV channel deduplication
- `tmdb.py` - TMDB API integration with cache
- `tmdb_validator.py` - TMDB validation with priority processing and automatic deduplication
- `exporter.py` - STRM file generation with incremental tracking
- `downloader.py` - M3U file downloading with cache
- `bulk_classifier.py` - Optimized batch classification
- `maintenance.py` - Unified maintenance operations
- `tv_m3u_generator.py` - TV M3U and EPG generation
- `epg.py` - Basic EPG service
- `epg_fetcher.py` - Advanced EPG fetching
- `config.py` - Centralized configuration
- `logo_enricher.py` - Logo enrichment for channels

#### Background Processing
- Background thread for long-running operations
- Heartbeat mechanism for process monitoring
- SSE (Server-Sent Events) for real-time updates

### 3. Data Access Layer

#### Models (Dataclasses)
- `Iptv` - IPTV source configuration
- `Midia` - Media entry (movies, series, etc.)
- `TvChannel` - TV channel entry
- `TmdbCache` - TMDB API cache
- `ExportedMedia` - Export tracking
- `ExportLock` - Export concurrency control
- `ProcessStatus` - Process status tracking
- `FilaProcessamento` - Processing queue
- `ExecutionStats` - Execution statistics
- `SystemSetting` - System configuration

#### Queries
- Common database operations
- Dashboard statistics
- Media counts by category
- Duplicate detection
- Export tracking

#### Retry Helper
- Automatic retry for database locks
- Exponential backoff
- Lock timeout management

### 4. Database Layer (SQLite)

**Database**: SQLite with WAL mode for better concurrency

**Tables**:

#### iptvs
- IPTV source configurations
- M3U and EPG URLs
- Active status tracking

#### midias
- All processed media entries
- Categories: Movie, Series, TV, Sports, etc.
- Hash-based deduplication
- TMDB integration fields

#### tv_channels
- TV channel specific entries
- Logo URLs
- TVG-ID mapping

#### tmdb_cache
- TMDB API response cache
- 30-day cache duration (configurable)
- Normalized title indexing

#### exported_media
- Export tracking with file hashes
- Incremental export support
- Change detection

#### export_lock
- Single export lock mechanism
- Heartbeat tracking
- Stale lock detection

#### process_status
- Real-time process status
- Progress tracking
- Stage management

#### fila_processamento
- Processing queue
- Stage sequencing
- Status tracking

#### execution_stats
- Execution statistics
- Performance metrics
- Item counts

#### system_settings
- System configuration
- TMDB API key
- Path settings
- Timeout values

### 5. External Services

#### TMDB API
- Movie metadata enrichment
- Year extraction
- Poster/backdrop images
- Adult content detection

#### IPTV Sources
- M3U playlist downloads
- 6-hour cache (configurable)
- Multiple source support

#### EPG Sources
- XMLTV format support
- Gzip compression support
- Channel mapping

### 6. File System

#### Gallery (D:/Galeria)
- STRM file output
- Organized by category
- Year-based folder structure for movies

#### Cache
- M3U file cache
- EPG file cache
- Temporary processing files

#### Backup
- Automatic database backups
- Pre-operation snapshots
- Manual backup support

## Data Flow

### Processing Pipeline

```
1. Download M3U
   ↓
2. Parse M3U
   - Extract metadata
   - Calculate hash
   - Normalize names
   ↓
3. Classify Media
   - Category detection
   - Season/episode extraction
   - Year extraction
   ↓
4. TMDB Enrichment (Movies)
   - API lookup
   - Cache check
   - Year update
   ↓
5. Deduplication
   - Hash-based
   - Quality priority
   - TV channel dedup
   ↓
6. Database Insert
   - Batch operations
   - Incremental processing
   ↓
7. Export to Gallery
   - STRM generation
   - Quality removal
   - Year in filename
   - Incremental export
```

### Export Pipeline

```
1. Acquire Lock
   - Check existing lock
   - Stale lock detection
   ↓
2. Query New/Modified Media
   - Hash comparison
   - Exported_media table
   ↓
3. Generate STRM Files
   - Sanitize filenames
   - Remove quality indicators
   - Add year for movies
   ↓
4. Update Export Tracking
   - File hash calculation
   - Exported_media update
   ↓
5. Release Lock
   - Heartbeat stop
   - Lock release
```

## Key Design Patterns

### 1. Incremental Processing
- Hash-based change detection
- Only process new/modified items
- Export tracking prevents re-export

### 2. Caching Strategy
- M3U cache: 6 hours
- TMDB cache: 30 days
- EPG cache: 6 hours
- Reduces external API calls

### 3. Lock Management
- Single export lock
- Heartbeat mechanism
- Automatic stale lock cleanup
- Retry with exponential backoff

### 4. Batch Processing
- Bulk classifier: 500 items/batch
- executemany for database operations
- Reduces database roundtrips

### 5. Service Layer Pattern
- Business logic in services
- Routes handle HTTP only
- Database layer handles persistence
- Clear separation of concerns

## Security Considerations

### Current State
- ⚠️ No authentication implemented
- ⚠️ SECRET_KEY uses default in dev
- ⚠️ DEBUG=True in dev mode
- ⚠️ No rate limiting
- ⚠️ No input validation on some endpoints

### Recommendations
1. Implement authentication (Flask-Login or JWT)
2. Set strong SECRET_KEY via environment
3. Disable DEBUG in production
4. Add rate limiting (Flask-Limiter)
5. Add input validation (Pydantic/FValid)
6. Add CSRF protection
7. Use HTTPS in production
8. Implement RBAC for sensitive operations

## Performance Characteristics

### Database
- SQLite with WAL mode
- Timeout: 120 seconds
- Busy timeout: 120 seconds
- Indexes on frequently queried fields
- Batch operations for bulk inserts

### Caching
- TMDB cache reduces API calls by >90%
- M3U cache reduces downloads
- In-memory caching for frequent queries

### Processing
- Incremental processing reduces workload
- Batch operations reduce database overhead
- Background thread prevents blocking
- SSE for real-time updates without polling

### Capacity
- Safe: 1-2 sources of 50k-100k items each
- With risk: 3-5 sources of 100k-500k items each
- Critical: 10+ sources of 500k-1M items each (needs redesign)

See `CAPACIDADE_IPTV.md` for detailed capacity analysis.

## Scalability Limitations

### Current Limitations
1. SQLite single-writer limitation
2. No horizontal scaling
3. Sequential download (no parallel)
4. Single export lock
5. TMDB Free Tier limits (1000 req/day)

### Scaling Recommendations
For larger deployments:
1. Migrate to PostgreSQL
2. Implement Redis for caching
3. Add Celery for background tasks
4. Implement parallel downloads
5. Use TMDB Premium or alternative
6. Add load balancer
7. Implement microservices architecture

## Monitoring and Logging

### Logging
- File-based logging with rotation
- Three log files: process.log, export.log, error.log
- 10MB max size, 5 backups
- Structured logging format

### Monitoring
- Process status tracking
- Execution statistics
- Heartbeat monitoring
- Lock status monitoring

### Recommendations
1. Add Prometheus metrics
2. Implement health check endpoint
3. Add alerting (email/Telegram)
4. Centralized logging (ELK stack)
5. Performance monitoring (APM)

## Deployment Architecture

### Development
```bash
python run.py
# Runs on http://localhost:5000
```

### Production (Recommended)
```
┌─────────────┐
│   Nginx     │ (Reverse Proxy)
│   (SSL/TLS) │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Gunicorn  │ (WSGI Server)
│  (Workers)  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Flask     │ (Application)
│   App       │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   SQLite    │ (Database)
└─────────────┘
```

### Docker Deployment (Future)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "run:app"]
```

## Technology Stack

### Backend
- **Framework**: Flask 3.0.0
- **Database**: SQLite 3
- **Python**: 3.8+
- **HTTP Client**: requests 2.31.0
- **Environment**: python-dotenv 1.0.0

### Frontend
- **UI Framework**: Bootstrap 5
- **Icons**: Bootstrap Icons
- **Charts**: Chart.js
- **Theme**: Custom CSS with dark/light toggle

### External APIs
- **TMDB**: The Movie Database API
- **IPTV Sources**: M3U playlists
- **EPG Sources**: XMLTV format

## Configuration Management

### Environment Variables (.env)
```
SECRET_KEY=your-secret-key
DEBUG=False
TMDB_API_KEY=your-tmdb-key
GALERIA_PATH=D:/Galeria
M3U_REFRESH_INTERVAL=21600
TMDB_CACHE_DURATION=2592000
HOST=0.0.0.0
PORT=5000
```

### Database Settings
- Stored in `system_settings` table
- Configurable via web interface
- Runtime updates without restart

## Backup and Recovery

### Automatic Backups
- Created before critical operations
- Stored in `backup/` directory
- Timestamp-based naming

### Manual Backup
```bash
# Backup database
python backup/create_backup.py

# Restore backup
python backup/restore_backup.py <backup_file>
```

### Recovery Procedures
1. Stop application
2. Restore database from backup
3. Verify data integrity
4. Restart application
5. Run maintenance checks

## Testing Strategy

### Current State
- ❌ No automated tests
- ❌ No integration tests
- ❌ No E2E tests

### Recommendations
1. Add unit tests for services
2. Add integration tests for API
3. Add E2E tests with Selenium/Playwright
4. Implement CI/CD pipeline
5. Add performance tests

## Documentation Structure

```
docs/
├── README.md                      # Project overview
├── API_DOCUMENTATION.md           # Complete API reference
├── ARCHITECTURE.md                # This file
├── ANALISE_PROJETO.md             # Project analysis
├── ANALISE_COMPLETA_SITE.md       # Complete site analysis
├── AGENTS.md                      # Agent guide
├── MELHORIAS_INTERFACE_100.md     # Interface improvements
├── RESUMO_MELHORIAS_SESSAO.md     # Session improvements
├── DATABASE_LOCK_FIX.md           # Database lock fix
├── TMDB_AUTO_ENRICHMENT.md        # TMDB enrichment
├── TMDB_INTERFACE_BUTTON.md       # TMDB interface
├── TV_M3U_JELLYFIN.md             # TV M3U for Jellyfin
├── YEAR_IN_FILENAME.md             # Year in filename
├── QUALITY_REMOVAL.md             # Quality indicator removal
└── CAPACIDADE_IPTV.md             # Capacity analysis
```

## Future Enhancements

### Short Term
1. Authentication system
2. Advanced search and filters
3. Media details page
4. TV channel management UI
5. Automated scheduling

### Medium Term
1. PostgreSQL migration
2. Redis caching
3. Celery background tasks
4. API documentation (Swagger)
5. Docker deployment

### Long Term
1. Microservices architecture
2. Multi-user support
3. Plugin system
4. Mobile app
5. Cloud deployment

## Conclusion

The Mestre IPTV Manager follows a clean layered architecture with clear separation of concerns. The system is designed for personal/small business use with incremental processing, intelligent caching, and robust export tracking. While the current architecture is solid for its intended scale, larger deployments would require architectural changes including database migration, distributed processing, and enhanced security measures.
