"""Dashboard routes."""

from flask import Blueprint, render_template
from app.database.queries import get_dashboard_stats, get_last_execution_stats, get_recent_activity

bp = Blueprint('dashboard', __name__, url_prefix='/')


@bp.route('/')
def index():
    """Dashboard home page."""
    stats = get_dashboard_stats()
    last_execution = get_last_execution_stats()
    recent_activity = get_recent_activity(limit=10)
    
    return render_template(
        'dashboard.html',
        stats=stats,
        last_execution=last_execution,
        recent_activity=recent_activity
    )
