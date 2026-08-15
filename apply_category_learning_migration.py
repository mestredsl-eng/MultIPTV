from app.app import create_app

app = create_app()
ctx = app.app_context()
ctx.push()

from app.database import get_db
db = get_db()

# Apply migration
import sys
sys.path.insert(0, 'app/database/migrations')
import importlib.util
spec = importlib.util.spec_from_file_location("migration", "app/database/migrations/0004_add_category_learning.py")
migration_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration_module)

try:
    migration_module.upgrade(db)
    print("Migration 0004_add_category_learning applied successfully")
except Exception as e:
    print(f"Error applying migration: {e}")

ctx.pop()

