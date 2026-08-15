"""Settings route for Mestre IPTV Manager."""

from flask import Blueprint, render_template

bp = Blueprint('settings', __name__)

@bp.route('/settings/', methods=['GET'])
def settings():
    """Settings page."""
    return render_template('settings.html')
