from functools import wraps
from flask import g, redirect, url_for, flash

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.user and not g.school:
            flash("You need to login first.", "error")
            # Redirect to appropriate login page
            if 'school' in request.path:
                return redirect(url_for("auth.school_login"))
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function
