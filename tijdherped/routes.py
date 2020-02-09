""" Default routes """

from flask import redirect, url_for
from flask_login import current_user

from tijdherped import app


@app.route('/')
def index():
    if not current_user or current_user.is_anonymous:
        return redirect(url_for('auth.login'))

    if current_user.role == 'student':
        return redirect(url_for('students.index'))
    elif current_user.role == 'teacher':
        return redirect(url_for('teachers.index'))

    return 'account not configured'
