from functools import wraps
from flask import g, redirect, url_for

def login_required(view):
    """Decorator to check if user is logged in"""
    @wraps(view)
    def wrapped_view(**kwargs):
        if not g.creator and not g.user:
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view 