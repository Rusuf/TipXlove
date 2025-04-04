# Routes package
from .auth import auth_bp
from .dashboard import dashboard_bp
from .payments import payments_bp
from .withdrawals import withdrawals_bp

from functools import wraps
from flask import g, redirect, url_for, session
from ..models.user import Creator

def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if not g.creator and not g.user:
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view

# Export blueprints
__all__ = ['auth_bp', 'dashboard_bp', 'payments_bp', 'withdrawals_bp', 'login_required'] 