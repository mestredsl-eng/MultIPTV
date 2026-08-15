"""Logs routes."""

from flask import Blueprint, render_template

bp = Blueprint('logs', __name__, url_prefix='/logs')


@bp.route('/')
def index():
    """Logs page."""
    return render_template('logs.html')
