"""Registration routes."""

from flask import Blueprint, render_template

bp = Blueprint('registration', __name__, url_prefix='/registration')


@bp.route('/')
def index():
    """Registration page."""
    return render_template('registration.html')
