"""Mestre IPTV Manager - Flask Application Factory."""

from flask import Flask
from app.database import init_db, close_db
import os
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler

# Load environment variables from .env file if it exists
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)


class WindowsSafeRotatingFileHandler(RotatingFileHandler):
    """RotatingFileHandler that handles Windows permission errors gracefully."""
    
    def doRollover(self):
        """Override doRollover to handle permission errors on Windows."""
        try:
            super().doRollover()
        except (PermissionError, OSError) as e:
            # If we can't rotate due to permission error, just continue
            # This prevents the logging system from crashing
            pass


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Configuration
    import os
    debug_mode = os.environ.get('DEBUG', 'True') == 'True'
    
    if not debug_mode:
        # In production, SECRET_KEY is required
        secret_key = os.environ.get('SECRET_KEY')
        if not secret_key:
            raise ValueError('SECRET_KEY environment variable must be set in production mode')
        if secret_key == 'dev-secret-key-change-in-production':
            raise ValueError('SECRET_KEY must be changed from the default value in production')
        app.config['SECRET_KEY'] = secret_key
    else:
        # In development, use default if not set
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    app.config['DEBUG'] = debug_mode

    # Disable cache for development
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    # Register database close handler
    app.teardown_appcontext(close_db)

    # Initialize database
    with app.app_context():
        init_db()

    # Register blueprints
    from app.routes import dashboard, process, maintenance, registration, logs, api, settings
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(process.bp)
    app.register_blueprint(maintenance.bp)
    app.register_blueprint(registration.bp)
    app.register_blueprint(logs.bp)
    app.register_blueprint(api.bp)
    app.register_blueprint(settings.bp)

    # Initialize logging
    setup_logging()

    # Add after_request handler to disable cache
    @app.after_request
    def add_no_cache_headers(response):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    return app


def setup_logging():
    """Configure file-based logging with rotation."""
    import logging
    from pathlib import Path
    
    log_dir = Path(__file__).parent / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure process logger with rotation (10MB max, keep 5 backups)
    process_logger = logging.getLogger('process')
    process_logger.setLevel(logging.INFO)
    process_handler = WindowsSafeRotatingFileHandler(
        log_dir / 'process.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    process_handler.setLevel(logging.INFO)
    process_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    process_handler.setFormatter(process_formatter)
    process_logger.addHandler(process_handler)
    
    # Configure export logger with rotation (10MB max, keep 5 backups)
    export_logger = logging.getLogger('export')
    export_logger.setLevel(logging.INFO)
    export_handler = WindowsSafeRotatingFileHandler(
        log_dir / 'export.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    export_handler.setLevel(logging.INFO)
    export_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    export_handler.setFormatter(export_formatter)
    export_logger.addHandler(export_handler)
    
    # Configure error logger with rotation (10MB max, keep 5 backups)
    error_logger = logging.getLogger('error')
    error_logger.setLevel(logging.ERROR)
    error_handler = WindowsSafeRotatingFileHandler(
        log_dir / 'error.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    error_handler.setFormatter(error_formatter)
    error_logger.addHandler(error_handler)
