"""Maintenance routes."""

from flask import Blueprint, render_template

bp = Blueprint('maintenance', __name__, url_prefix='/maintenance')


@bp.route('/')
def index():
    """Maintenance page."""
    return render_template('maintenance.html')
