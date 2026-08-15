"""Run a specific migration by name."""

import sys
from app.app import create_app

if len(sys.argv) < 2:
    print("Usage: python run_migration.py <migration_name>")
    sys.exit(1)

migration_name = sys.argv[1]

# Create app context
app = create_app()
with app.app_context():
    from app.database import get_db
    from pathlib import Path
    
    db = get_db()
    
    # Import and run migration
    try:
        migration_module = __import__(f'app.database.migrations.{migration_name}', fromlist=['upgrade', 'downgrade'])
        
        print(f"Running migration: {migration_name}")
        migration_module.upgrade(db)
        print(f"Migration {migration_name} completed successfully!")
        
    except ImportError as e:
        print(f"Error importing migration {migration_name}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error running migration {migration_name}: {e}")
        sys.exit(1)
