# Troubleshooting Guide - Mestre IPTV Manager

This guide helps you diagnose and resolve common issues with the Mestre IPTV Manager.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Database Issues](#database-issues)
- [Processing Issues](#processing-issues)
- [Export Issues](#export-issues)
- [TMDB Issues](#tmdb-issues)
- [Performance Issues](#performance-issues)
- [Web Interface Issues](#web-interface-issues)
- [File System Issues](#file-system-issues)
- [Network Issues](#network-issues)
- [Quality Indicator Issues](#quality-indicator-issues)

---

## Installation Issues

### Python Version Error

**Symptom**: `SyntaxError` or module import errors

**Solution**:
```bash
# Check Python version
python --version

# Must be Python 3.8 or higher
# If not, install newer Python from python.org
```

### Virtual Environment Issues

**Symptom**: Cannot activate virtual environment or import errors

**Solution**:
```bash
# Delete existing venv
rmdir /s .venv

# Recreate venv
python -m venv .venv

# Activate
.venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Missing Dependencies

**Symptom**: `ModuleNotFoundError` for Flask, requests, etc.

**Solution**:
```bash
# Ensure venv is activated
.venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt

# Upgrade pip
pip install --upgrade pip
```

### Port Already in Use

**Symptom**: `Address already in use` when starting server

**Solution**:
```bash
# Find process using port 5000
netstat -ano | findstr :5000

# Kill the process (replace <PID> with actual PID)
taskkill /PID <PID> /F

# Or use different port
python -m flask --app app.app run --port=5001
```

---

## Database Issues

### Database Locked Error

**Symptom**: `sqlite3.OperationalError: database is locked`

**Causes**:
- Multiple processes accessing database
- Stale lock from crashed process
- Long-running transaction

**Solutions**:

1. **Check locks**:
```bash
python check_locks.py
```

2. **Force cleanup**:
```bash
# Stop the server first
python force_cleanup.py
```

3. **Restart server**:
```bash
python run.py
```

4. **If persistent**, delete lock manually:
```bash
# Access database
sqlite3 database/iptv.db

# Check lock table
SELECT * FROM export_lock;

# Reset lock
UPDATE export_lock SET locked = 0, locked_since = NULL, locked_by = NULL WHERE id = 1;
```

**See also**: `DATABASE_LOCK_FIX.md` for detailed information.

### Database Corruption

**Symptom**: `database disk image is malformed`

**Solution**:
```bash
# Restore from backup
python restore_backup.py backup/iptv_backup_<timestamp>.db

# Or if no backup, try to recover
sqlite3 database/iptv.db ".recover" | sqlite3 database/iptv_recovered.db
```

### Migration Errors

**Symptom**: Table or column not found errors

**Solution**:
```bash
# Check database schema
sqlite3 database/iptv.db ".schema"

# Apply missing migrations
python apply_migration.py

# If still failing, recreate database
# WARNING: This deletes all data
del database\iptv.db
python -c "from app.database import init_db; init_db()"
```

### Slow Database Queries

**Symptom**: Queries taking long time

**Solution**:
```bash
# Check for missing indexes
sqlite3 database/iptv.db "PRAGMA index_list(midias);"

# Add indexes if missing
sqlite3 database/iptv.db "CREATE INDEX IF NOT EXISTS idx_midias_categoria ON midias(categoria);"
sqlite3 database/iptv.db "CREATE INDEX IF NOT EXISTS idx_midias_hash ON midias(hash_midia);"

# Analyze query plan
sqlite3 database/iptv.db "EXPLAIN QUERY PLAN SELECT * FROM midias WHERE categoria = 'Movie';"
```

---

## Processing Issues

### Processing Stuck

**Symptom**: Process shows "running" but no progress

**Solution**:
```bash
# Check process status
python check_locks.py

# Force cleanup if stale
python force_cleanup.py

# Restart server
python run.py
```

### No New Items Processed

**Symptom**: Process completes but 0 new items

**Causes**:
- All items already processed (incremental mode)
- Hash calculation issue
- M3U file empty or invalid

**Solutions**:

1. **Check if M3U was downloaded**:
```bash
dir cache\m3u\
```

2. **Test M3U parsing**:
```python
from app.services.parser import parse_m3u
entries = parse_m3u('cache/m3u/your_file.m3u')
print(f"Found {len(entries)} entries")
```

3. **Force full reprocessing**:
```bash
# Via CLI
python main.py --full

# Or via API
curl -X POST http://localhost:5000/api/maintenance/reset-exported
```

### Classification Errors

**Symptom**: Items classified incorrectly or not at all

**Solution**:
```bash
# Check classifier logs
type app\logs\process.log | findstr "classify"

# Test classification manually
python -c "from app.services.classifier import classify_media; print(classify_media({'name': 'Test Movie'}))"

# If needed, reclassify
curl -X POST http://localhost:5000/api/reclassify/batch -H "Content-Type: application/json" -d '{"media_ids": [1,2,3], "new_category": "Series"}'
```

### Memory Issues During Processing

**Symptom**: `MemoryError` or system becomes slow

**Solution**:
```bash
# Use bulk classification instead
curl -X POST http://localhost:5000/api/process/classify-bulk -H "Content-Type: application/json" -d '{"batch_size": 100}'

# Reduce batch size if needed
curl -X POST http://localhost:5000/api/process/classify-bulk -H "Content-Type: application/json" -d '{"batch_size": 50}'
```

---

## Export Issues

### Export Fails

**Symptom**: Export process fails or hangs

**Solution**:
```bash
# Check export lock
python check_locks.py

# Release lock if stuck
python force_cleanup.py

# Check gallery path exists
dir D:\Galeria

# Check permissions
# Ensure user has write access to gallery path
```

### STRM Files Not Generated

**Symptom**: Export completes but no STRM files

**Causes**:
- Gallery path incorrect
- Permission issues
- No media to export

**Solutions**:

1. **Check gallery path**:
```bash
# Via settings page
# Menu > Configurações > Caminho da Galeria

# Or check database
sqlite3 database/iptv.db "SELECT valor FROM system_settings WHERE chave = 'galeria_path';"
```

2. **Check if media exists**:
```bash
sqlite3 database/iptv.db "SELECT COUNT(*) FROM midias WHERE status = 1 AND black_list = 0;"
```

3. **Check export logs**:
```bash
type app\logs\export.log
```

### Duplicate STRM Files

**Symptom**: Multiple STRM files for same media

**Solution**:
```bash
# Clean gallery duplicates
curl -X POST http://localhost:5000/api/maintenance/clean-gallery-duplicates

# Reset and reexport
curl -X POST http://localhost:5000/api/maintenance/reset-exported
curl -X POST http://localhost:5000/api/process/create-void
```

### Year Not in Filename

**Symptom**: STRM files don't have year in name

**Solution**:
```bash
# Check if movies have year in database
sqlite3 database/iptv.db "SELECT COUNT(*) FROM midias WHERE categoria = 'Movie' AND ano IS NULL;"

# Enrich with TMDB
curl -X POST http://localhost:5000/api/enrich/years-from-tmdb-all -H "Content-Type: application/json" -d '{}'

# Reexport
curl -X POST http://localhost:5000/api/maintenance/reset-exported
curl -X POST http://localhost:5000/api/process/create-void
```

---

## TMDB Issues

### TMDB API Key Invalid

**Symptom**: `TMDB API key invalid` error

**Solution**:
```bash
# Get new key from https://www.themoviedb.org/settings/api

# Update via web interface
# Menu > Configurações > TMDB API Key

# Or update directly
sqlite3 database/iptv.db "UPDATE system_settings SET valor = 'your-new-key' WHERE chave = 'tmdb_api_key';"

# Test key
curl -X POST http://localhost:5000/api/settings/test-tmdb
```

### TMDB Rate Limit Exceeded

**Symptom**: `API limit reached` or 429 errors

**Causes**:
- Free tier limit: 1000 requests/day
- Too many requests in short time

**Solution**:
```bash
# Wait 24 hours for limit to reset
# Or upgrade to TMDB Pro tier

# Use cache more effectively
# Increase cache duration in settings
# Menu > Configurações > Tempo de Cache TMDB

# Process in smaller batches
curl -X POST http://localhost:5000/api/enrich/years-from-tmdb -H "Content-Type: application/json" -d '{"limit": 100}'
```

### TMDB Not Finding Movies

**Symptom**: Movies not found in TMDB

**Solution**:
```bash
# Check movie name normalization
python -c "from app.services.tmdb import normalize_title; print(normalize_title('Your Movie Name'))"

# Manual search on TMDB website
# https://www.themoviedb.org/search?query=Your+Movie

# Use year from name as fallback
# System automatically does this if TMDB fails
```

### TMDB Cache Issues

**Symptom**: Old data returned from cache

**Solution**:
```bash
# Clear TMDB cache
sqlite3 database/iptv.db "DELETE FROM tmdb_cache;"

# Or reduce cache duration temporarily
# Menu > Configurações > Tempo de Cache TMDB
# Set to 3600 (1 hour) for testing
```

---

## Performance Issues

### Slow Processing

**Symptom**: Processing takes very long time

**Causes**:
- Large M3U files
- Many IPTV sources
- No TMDB cache
- Slow disk I/O

**Solutions**:

1. **Use bulk operations**:
```bash
curl -X POST http://localhost:5000/api/process/classify-bulk -H "Content-Type: application/json" -d '{"batch_size": 500}'
```

2. **Check TMDB cache hit rate**:
```bash
sqlite3 database/iptv.db "SELECT COUNT(*) FROM tmdb_cache;"
```

3. **Reduce sources**:
```bash
# Deactivate some sources temporarily
# Via web interface: Menu > Cadastro
```

4. **Check system resources**:
```bash
# CPU usage
tasklist

# Disk I/O
# Check if gallery is on slow drive
```

### High Memory Usage

**Symptom**: System memory usage high

**Solution**:
```bash
# Reduce batch size
curl -X POST http://localhost:5000/api/process/classify-bulk -H "Content-Type: application/json" -d '{"batch_size": 100}'

# Restart server periodically
# Memory may accumulate over time

# Check for memory leaks
# Monitor with task manager
```

### Slow Web Interface

**Symptom**: Web pages load slowly

**Solution**:
```bash
# Check database size
dir database\iptv.db

# If database is large (>1GB), consider:
# - Archive old data
# - Clean up duplicates
# - Vacuum database

sqlite3 database/iptv.db "VACUUM;"

# Check for slow queries in logs
type app\logs\error.log | findstr "slow"
```

---

## Web Interface Issues

### Page Not Loading

**Symptom**: Browser shows connection error

**Solution**:
```bash
# Check if server is running
tasklist | findstr python

# Check port
netstat -ano | findstr :5000

# Restart server
python run.py

# Check firewall
# Ensure port 5000 is not blocked
```

### JavaScript Errors

**Symptom**: Buttons not working, console errors

**Solution**:
```bash
# Open browser developer tools (F12)
# Check Console tab for errors

# Clear browser cache
# Ctrl+Shift+Delete

# Try different browser
# Chrome, Firefox, Edge
```

### Real-time Updates Not Working

**Symptom**: Progress bar not updating

**Solution**:
```bash
# Check SSE endpoint
curl http://localhost:5000/api/process/stream

# Check if browser supports SSE
# Most modern browsers do

# Check for proxy/VPN interference
# May block SSE connections
```

### Theme Toggle Not Working

**Symptom**: Dark/light theme switch not persisting

**Solution**:
```bash
# Clear browser localStorage
# In browser console:
localStorage.clear()

# Refresh page
```

---

## File System Issues

### Gallery Path Not Accessible

**Symptom**: `Permission denied` or path not found

**Solution**:
```bash
# Check path exists
dir D:\Galeria

# Check permissions
# Right-click folder > Properties > Security
# Ensure user has write access

# Test path via settings
# Menu > Configurações > Caminho da Galeria > Testar
```

### Disk Space Full

**Symptom**: `No space left on device`

**Solution**:
```bash
# Check disk space
dir D:\

# Clean up old STRM files
# Manually delete or use maintenance tool
curl -X POST http://localhost:5000/api/maintenance/clean-gallery

# Clean cache
del cache\m3u\*.*
del cache\epg\*.*

# Clean old backups
# Keep only recent backups in backup/
```

### File Path Too Long

**Symptom**: `File name too long` error on Windows

**Solution**:
```bash
# Enable long path support in Windows
# Requires registry change
# Not recommended for casual users

# Or shorten gallery path
# Use shorter path like D:\G instead of D:\Galeria
```

---

## Network Issues

### M3U Download Fails

**Symptom**: `Failed to download M3U` error

**Causes**:
- Invalid URL
- Network connectivity
- Server down
- Timeout

**Solution**:
```bash
# Test URL manually
curl <your-m3u-url>

# Check network connection
ping google.com

# Check if URL is accessible
# Try in browser

# Increase timeout in settings
# Menu > Configurações > Timeout do Banco
```

### EPG Download Fails

**Symptom**: EPG download fails

**Solution**:
```bash
# Test EPG URL manually
curl <your-epg-url>

# Check if URL is valid
# Ensure it's XMLTV format

# Try different EPG source
# Add alternative EPG URL in IPTV source
```

### TMDB API Unreachable

**Symptom**: `Connection error` to TMDB

**Solution**:
```bash
# Test TMDB API
curl https://api.themoviedb.org/3/movie/550?api_key=your-key

# Check internet connection
ping api.themoviedb.org

# Check if TMDB is down
# https://status.themoviedb.org/

# Check firewall/proxy
# May block API calls
```

---

## Getting Help

### Before Asking for Help

1. **Check logs**:
```bash
type app\logs\error.log
type app\logs\process.log
type app\logs\export.log
```

2. **Check database status**:
```bash
python check_locks.py
```

3. **Gather information**:
- Python version
- Operating system
- Error messages
- Steps to reproduce

### Where to Get Help

1. **Documentation**: Check `docs/` folder
2. **Existing Issues**: Search project issues
3. **Create New Issue**: Include:
   - Clear description
   - Error messages
   - Steps to reproduce
   - System information

### Diagnostic Information

Provide this information when asking for help:

```bash
# System info
python --version
pip list

# Database info
python check_locks.py

# Recent errors
type app\logs\error.log | more

# Configuration
sqlite3 database/iptv.db "SELECT * FROM system_settings;"
```

---

## Common Error Messages

### `sqlite3.OperationalError: database is locked`
See [Database Locked Error](#database-locked-error)

### `ModuleNotFoundError: No module named 'flask'`
See [Missing Dependencies](#missing-dependencies)

### `Address already in use`
See [Port Already in Use](#port-already-in-use)

### `TMDB API key invalid`
See [TMDB API Key Invalid](#tmdb-api-key-invalid)

### `Permission denied`
See [Gallery Path Not Accessible](#gallery-path-not-accessible)

### `File name too long`
See [File Path Too Long](#file-path-too-long)

---

## Prevention Tips

### Regular Maintenance

```bash
# Weekly: Check locks
python check_locks.py

# Monthly: Clean cache
del cache\m3u\*.*
del cache\epg\*.*

# Monthly: Vacuum database
sqlite3 database/iptv.db "VACUUM;"

# Monthly: Backup database
python backup/create_backup.py
```

### Monitoring

```bash
# Monitor disk space
dir D:\

# Monitor database size
dir database\iptv.db

# Monitor log files
dir app\logs\
```

### Best Practices

1. **Keep backups** of database
2. **Test changes** in development first
3. **Monitor logs** regularly
4. **Update dependencies** periodically
5. **Keep documentation** up to date

---

## Quality Indicator Issues

### Quality Indicators Still in Filenames

**Symptom**: Files still have quality indicators like `[4K]`, `[FHD]`, etc.

**Cause**: 
- Previously: Inconsistency between `sanitize_filename()` and `remove_quality_from_name()`
- **RESOLVIDO**: Corrigido em 27/07/2026

**Solution**:
```bash
# Issue resolved - both functions now use canonical remove_quality_indicators()
# See QUALITY_INCONSISTENCY_ISSUE.md for details
```

**Impact**:
- ✅ Resolved: Hash calculations now match filenames
- ✅ Resolved: Safe for large-scale reexportation

**Reference**: `QUALITY_INCONSISTENCY_ISSUE.md`

### Duplicates After Reexport

**Symptom**: Multiple files for same media after reexport

**Cause**:
- Previously: Hash inconsistency between functions
- **RESOLVIDO**: Corrigido em 27/07/2026

**Solution**:
```bash
# 1. Check for duplicates
python check_gallery_duplicates.py

# 2. Quality inconsistency is now resolved
# See QUALITY_INCONSISTENCY_ISSUE.md

# 3. If duplicates exist from before fix:
sqlite3 database\iptv.db "DELETE FROM exported_media;"
# Reexport
```

### Files Not Found During Export

**Symptom**: Export fails with "file not found" errors

**Cause**:
- Previously: Hash calculated with different quality removal than filename
- **RESOLVIDO**: Corrigido em 27/07/2026

**Solution**:
```bash
# 1. Check exported_media integrity
python check_exported_vs_blacklist.py

# 2. Quality inconsistency is now resolved
# See QUALITY_INCONSISTENCY_ISSUE.md

# 3. Reset and reexport
python check_locks.py  # Reset exported via interface
```

### Large-Scale Migration Risks

**Symptom**: Planning to delete 600k+ media files

**Risk**: Previously HIGH - Quality inconsistency could cause mass duplication
**Current Risk**: LOW - Inconsistency resolved

**Solution**:
```bash
# Safe to proceed following:
# See SAFE_MIGRATION_GUIDE.md for complete migration guide

# Critical steps (quality issue resolved):
# 1. ✅ Quality inconsistency fixed
# 2. Test with 100 items
# 3. Migrate by category
# 4. Validate each step
```

**Reference**: `SAFE_MIGRATION_GUIDE.md`

---

## Recovery Procedures

### Complete System Recovery

If everything is broken:

1. **Stop server**:
```bash
# Ctrl+C in terminal or kill process
```

2. **Backup current state**:
```bash
copy database\iptv.db backup\iptv_broken.db
```

3. **Restore from last known good backup**:
```bash
copy backup\iptv_backup_<timestamp>.db database\iptv.db
```

4. **Clear locks**:
```bash
python force_cleanup.py
```

5. **Restart server**:
```bash
python run.py
```

### Data Recovery from STRM Files

If database is lost but STRM files exist:

1. **Scan gallery for STRM files**:
```bash
dir /s /b D:\Galeria\*.strm > strmlist.txt
```

2. **Parse STRM files to rebuild database** (custom script needed)
3. **Reprocess M3U to fill missing data**

---

## Contact and Support

For issues not covered in this guide:
- Check project documentation in `docs/`
- Search existing GitHub issues
- Create new issue with diagnostic information

Remember to include:
- Error messages
- Log files (sanitized)
- System information
- Steps to reproduce
