"""Process routes."""

from flask import Blueprint, render_template

bp = Blueprint('process', __name__, url_prefix='/process')


@bp.route('/')
def index():
    """Process page."""
    return render_template('process.html')
