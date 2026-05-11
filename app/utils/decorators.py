"""Auth decorators and schedule enforcement."""
from functools import wraps
from datetime import datetime
from flask import redirect, url_for, flash
from flask_login import current_user


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_admin():
            flash('Acceso denegado. Se requieren permisos de administrador.', 'error')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated


def editor_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.can_edit():
            flash('Acceso denegado. Se requieren permisos de editor.', 'error')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated


def check_user_schedule(user):
    """
    Return (allowed: bool, reason: str).
    Admins always pass. Users with NO schedules defined always pass.
    """
    if user.role == 'admin':
        return True, ''
    schedules = [s for s in user.schedules if s.enabled]
    if not schedules:
        return True, ''
    now = datetime.now()
    today = now.weekday()
    time_now = now.strftime('%H:%M')
    for s in schedules:
        if s.day_of_week == today and s.time_start <= time_now <= s.time_end:
            return True, ''
    from app.models import UserSchedule
    day_name = UserSchedule.DAY_NAMES[today]
    return False, f'Acceso no permitido el {day_name} a las {time_now}.'
