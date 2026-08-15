# Developer Guide - Mestre IPTV Manager

## Overview

This guide is for developers who want to contribute to or extend the Mestre IPTV Manager project. It covers the development environment, code structure, best practices, and contribution guidelines.

## Development Environment Setup

### Prerequisites
- Python 3.8 or higher
- Git
- IDE (VS Code, PyCharm, or similar)
- SQLite browser (optional, for database inspection)

### Setup Steps

1. **Clone the repository**
```bash
cd c:\Users\mestr\OneDrive\Documentos\IPTV\mestre-IPTV
```

2. **Create virtual environment**
```bash
python -m venv .venv
.venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Install development dependencies** (optional but recommended)
```bash
pip install pytest pytest-cov black flake8 mypy
```

5. **Configure environment**
```bash
copy .env.example .env
# Edit .env with your settings
```

6. **Initialize database**
```bash
python -c "from app.database import init_db; init_db()"
```

## Project Structure

### Directory Layout

```
mestre-IPTV/
├── app/                      # Main application package
│   ├── routes/              # Flask blueprints (HTTP endpoints)
│   ├── services/            # Business logic services
│   ├── database/            # Database layer
│   ├── templates/           # HTML templates
│   ├── static/              # Static assets (CSS, JS)
│   ├── logs/                # Log files
│   ├── background/          # Background processing
│   ├── app.py               # Flask application factory
│   └── __init__.py          # Package initialization
├── backup/                  # Database backups
├── cache/                   # M3U and EPG cache
├── database/                # SQLite database files
├── docs/                    # Documentation
├── main.py                  # CLI script
├── run.py                   # Web entry point
├── requirements.txt         # Python dependencies
└── .env.example             # Environment variables template
```

### Key Components

#### Routes (`app/routes/`)
Flask blueprints that handle HTTP requests:
- `api.py` - REST API endpoints
- `dashboard.py` - Dashboard page
- `process.py` - Process control
- `maintenance.py` - Maintenance operations
- `registration.py` - IPTV source management
- `logs.py` - Log viewing
- `settings.py` - Settings management

#### Services (`app/services/`)
Business logic layer:
- `parser.py` - M3U parsing and hash calculation
- `classifier.py` - Media classification
- `reclassifier.py` - Advanced reclassification
- `deduplicator.py` - TV channel deduplication
- `tmdb.py` - TMDB API integration
- `exporter.py` - STRM file generation
- `downloader.py` - M3U downloading
- `bulk_classifier.py` - Batch classification
- `maintenance.py` - Maintenance operations
- `tv_m3u_generator.py` - TV M3U generation
- `epg.py` - EPG service
- `config.py` - Configuration management

#### Database (`app/database/`)
Data access layer:
- `models.py` - Dataclass models
- `queries.py` - Common database queries
- `migrations/` - Database schema migrations
- `retry_helper.py` - Lock retry mechanism

## Code Style and Conventions

### Python Style Guide
Follow PEP 8 guidelines:
- Use 4 spaces for indentation
- Maximum line length: 100 characters
- Use snake_case for variables and functions
- Use PascalCase for classes
- Add docstrings to all functions and classes

### Example Function
```python
def classify_media(entry: dict) -> str:
    """
    Classify media entry into category.
    
    Args:
        entry: Dictionary containing media metadata
        
    Returns:
        Category string (Movie, Series, TV, etc.)
        
    Raises:
        ValueError: If entry is invalid
    """
    name = entry.get('name', '').lower()
    # Implementation here
    return 'Movie'
```

### Database Queries
Use parameterized queries to prevent SQL injection:
```python
# Good
db.execute('SELECT * FROM midias WHERE id = ?', (media_id,))

# Bad
db.execute(f"SELECT * FROM midias WHERE id = {media_id}")
```

### Error Handling
Use specific exception handling:
```python
try:
    result = tmdb.get_movie_info(name)
except requests.Timeout:
    logger.error(f"TMDB timeout for {name}")
    return None
except requests.RequestException as e:
    logger.error(f"TMDB request failed: {e}")
    return None
```

## Adding New Features

### Adding a New API Endpoint

1. **Add route in appropriate blueprint** (`app/routes/api.py`):
```python
@bp.route('/new-endpoint', methods=['POST'])
def new_endpoint():
    """Handle new feature."""
    from app.services.new_service import new_function
    
    data = request.get_json()
    result = new_function(data)
    
    return jsonify({'success': True, 'data': result})
```

2. **Create service function** (`app/services/new_service.py`):
```python
def new_function(data: dict) -> dict:
    """
    Implement new feature logic.
    
    Args:
        data: Input data
        
    Returns:
        Result dictionary
    """
    # Implementation
    return result
```

3. **Add database query if needed** (`app/database/queries.py`):
```python
def get_new_data():
    """Get new data from database."""
    db = get_db()
    result = db.execute('SELECT * FROM table').fetchall()
    return [dict(row) for row in result]
```

4. **Update documentation** (`docs/API_DOCUMENTATION.md`):
```markdown
### New Endpoint
**POST** `/api/new-endpoint`

Description of the endpoint.

**Request Body**:
```json
{
  "param": "value"
}
```

**Response**:
```json
{
  "success": true,
  "data": {}
}
```
```

### Adding a New Page

1. **Create route** (`app/routes/new_page.py`):
```python
from flask import Blueprint, render_template

bp = Blueprint('new_page', __name__, url_prefix='/new-page')

@bp.route('/')
def index():
    """Render new page."""
    return render_template('new_page.html')
```

2. **Register blueprint** (`app/app.py`):
```python
from app.routes import new_page
app.register_blueprint(new_page.bp)
```

3. **Create template** (`app/templates/new_page.html`):
```html
{% extends 'base.html' %}

{% block content %}
<div class="container">
    <h1>New Page</h1>
    <!-- Content here -->
</div>
{% endblock %}
```

4. **Add navigation link** (`app/templates/base.html`):
```html
<a class="nav-link" href="/new-page/">New Page</a>
```

### Adding a New Service

1. **Create service file** (`app/services/new_service.py`):
```python
"""New service description."""

import logging
from app.database import get_db

logger = logging.getLogger(__name__)

def new_service_function(param):
    """
    Implement new service logic.
    
    Args:
        param: Input parameter
        
    Returns:
        Result
    """
    db = get_db()
    # Implementation
    return result
```

2. **Import and use in routes**:
```python
from app.services.new_service import new_service_function

@bp.route('/use-service', methods=['POST'])
def use_service():
    result = new_service_function(data)
    return jsonify({'success': True, 'result': result})
```

## Database Migrations

### Creating a Migration

1. **Create migration file** (`app/database/migrations/001_add_new_table.sql`):
```sql
CREATE TABLE IF NOT EXISTS new_table (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_new_table_name ON new_table(name);
```

2. **Apply migration**:
```python
from app.database import get_db

def apply_migration():
    db = get_db()
    with open('app/database/migrations/001_add_new_table.sql', 'r') as f:
        migration_sql = f.read()
    db.executescript(migration_sql)
    db.commit()
```

3. **Update model** (`app/database/models.py`):
```python
@dataclass
class NewTable:
    id: int
    name: str
    created_at: datetime
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_parser.py

# Run specific test
pytest tests/test_parser.py::test_parse_m3u
```

### Writing Tests

Create test file (`tests/test_parser.py`):
```python
import pytest
from app.services.parser import parse_m3u, calculate_hash

def test_parse_m3u():
    """Test M3U parsing."""
    result = parse_m3u('test.m3u')
    assert len(result) > 0
    assert result[0]['name'] == 'Test Channel'

def test_calculate_hash():
    """Test hash calculation."""
    hash1 = calculate_hash('http://test.com', 'Test')
    hash2 = calculate_hash('http://test.com', 'Test')
    assert hash1 == hash2
```

## Debugging

### Enabling Debug Mode

Set in `.env`:
```env
DEBUG=True
```

Or in `app/app.py`:
```python
app.config['DEBUG'] = True
```

### Using Debugger

Add breakpoint in code:
```python
import pdb; pdb.set_trace()
```

Or use IDE debugger (VS Code, PyCharm).

### Viewing Logs

Logs are in `app/logs/`:
- `process.log` - Processing logs
- `export.log` - Export logs
- `error.log` - Error logs

### Database Inspection

Use SQLite browser or command line:
```bash
sqlite3 database/iptv.db
.tables
.schema midias
SELECT * FROM midias LIMIT 10;
```

## Performance Optimization

### Database Optimization

1. **Use indexes**:
```sql
CREATE INDEX idx_midias_categoria ON midias(categoria);
CREATE INDEX idx_midias_hash ON midias(hash_midia);
```

2. **Use batch operations**:
```python
# Instead of multiple inserts
for item in items:
    db.execute('INSERT INTO table VALUES (?)', (item,))

# Use executemany
db.executemany('INSERT INTO table VALUES (?)', [(item,) for item in items])
```

3. **Use transactions**:
```python
db.execute('BEGIN TRANSACTION')
# Multiple operations
db.commit()
```

### Caching

1. **TMDB cache** is automatic (30 days)
2. **M3U cache** is automatic (6 hours)
3. **Add custom cache** if needed:
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def expensive_function(param):
    # Expensive operation
    return result
```

## Security Best Practices

### Input Validation
```python
from flask import request

# Validate input
data = request.get_json()
if not data or 'required_field' not in data:
    return jsonify({'error': 'Invalid input'}), 400
```

### SQL Injection Prevention
Always use parameterized queries:
```python
# Good
db.execute('SELECT * FROM table WHERE id = ?', (user_id,))

# Bad
db.execute(f"SELECT * FROM table WHERE id = {user_id}")
```

### Secret Management
Never commit secrets:
- Use `.env` file (add to `.gitignore`)
- Use environment variables
- Never hardcode API keys

### Authentication (Future)
Plan to implement:
- Flask-Login for session auth
- JWT for API auth
- RBAC for authorization

## Common Tasks

### Adding a New Media Category

1. **Update classifier** (`app/services/classifier.py`):
```python
def is_new_category(name, group_title):
    """Check if content is new category."""
    keywords = ['keyword1', 'keyword2']
    return any(keyword in name or keyword in group_title for keyword in keywords)
```

2. **Add to classify_media**:
```python
if is_new_category(name, group_title):
    return 'NewCategory'
```

3. **Update dashboard stats** (`app/database/queries.py`):
```python
def get_new_category_count():
    """Get new category count."""
    db = get_db()
    result = db.execute(
        'SELECT COUNT(*) as count FROM midias WHERE categoria = ?',
        ('NewCategory',)
    ).fetchone()
    return result['count'] if result else 0
```

### Modifying Export Format

Edit `app/services/exporter.py`:
```python
def generate_strm_filename(media):
    """Generate STRM filename."""
    # Modify format here
    return f"{media['name']}.strm"
```

### Adding New Configuration

1. **Add to system_settings**:
```python
# In settings route
@bp.route('/settings/new-setting', methods=['POST'])
def update_new_setting():
    value = request.json.get('value')
    db.execute('INSERT OR REPLACE INTO system_settings (chave, valor) VALUES (?, ?)',
               ('new_setting', value))
    db.commit()
    return jsonify({'success': True})
```

2. **Add to config service** (`app/services/config.py`):
```python
def get_new_setting():
    """Get new setting value."""
    db = get_db()
    result = db.execute('SELECT valor FROM system_settings WHERE chave = ?', 
                      ('new_setting',)).fetchone()
    return result['valor'] if result else 'default_value'
```

## Contribution Guidelines

### Before Contributing

1. **Read existing code** to understand patterns
2. **Check existing issues** for similar work
3. **Discuss major changes** in an issue first

### Making Changes

1. **Create a branch**:
```bash
git checkout -b feature/your-feature-name
```

2. **Make changes** following code style
3. **Add tests** for new features
4. **Update documentation**
5. **Commit with clear messages**:
```bash
git commit -m "Add new feature: description"
```

### Pull Request Process

1. **Push to branch**:
```bash
git push origin feature/your-feature-name
```

2. **Create pull request** with:
   - Clear description
   - Related issues
   - Testing instructions
   - Documentation updates

3. **Address review feedback**

## Documentation

### Updating Documentation

- **API changes**: Update `docs/API_DOCUMENTATION.md`
- **Architecture changes**: Update `docs/ARCHITECTURE.md`
- **New features**: Update `docs/README.md`
- **Bug fixes**: Update relevant docs or create new doc

### Code Comments

Add docstrings to all functions:
```python
def function_name(param1: type, param2: type) -> return_type:
    """
    Brief description.
    
    Detailed description if needed.
    
    Args:
        param1: Description
        param2: Description
        
    Returns:
        Description of return value
        
    Raises:
        ExceptionType: Description
    """
    pass
```

## Troubleshooting Development Issues

### Import Errors
```bash
# Ensure you're in the project root
cd c:\Users\mestr\OneDrive\Documentos\IPTV\mestre-IPTV

# Ensure virtual environment is activated
.venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Database Locks
```bash
# Check locks
python check_locks.py

# Force cleanup
python force_cleanup.py
```

### Port Already in Use
```bash
# Find process using port 5000
netstat -ano | findstr :5000

# Kill process
taskkill /PID <PID> /F
```

## Resources

### Documentation
- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [TMDB API Documentation](https://developers.themoviedb.org/3)
- [Bootstrap Documentation](https://getbootstrap.com/docs/)

### Project Documentation
- `docs/README.md` - Project overview
- `docs/API_DOCUMENTATION.md` - API reference
- `docs/ARCHITECTURE.md` - Architecture overview
- `docs/ANALISE_PROJETO.md` - Project analysis

## Getting Help

1. **Check documentation** in `docs/` folder
2. **Search existing issues**
3. **Create new issue** with:
   - Clear description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details

## Best Practices Summary

- **Follow PEP 8** for code style
- **Write docstrings** for all functions
- **Use parameterized queries** for database
- **Handle exceptions** specifically
- **Log errors** appropriately
- **Write tests** for new features
- **Update documentation** with changes
- **Use meaningful commit messages**
- **Keep functions small** and focused
- **DRY principle** - Don't Repeat Yourself
- **SOLID principles** where applicable

## Future Development Areas

### High Priority
- Add authentication system
- Implement automated testing
- Add input validation
- Improve error handling

### Medium Priority
- Add search functionality
- Implement pagination
- Add filtering options
- Improve performance

### Low Priority
- Add API documentation (Swagger)
- Implement caching layer (Redis)
- Add monitoring/metrics
- Docker deployment

## Conclusion

This guide provides the foundation for contributing to the Mestre IPTV Manager project. Follow these guidelines to maintain code quality and consistency. For questions or clarifications, refer to the existing documentation or create an issue.
