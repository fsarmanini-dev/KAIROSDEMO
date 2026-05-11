"""Authentication routes."""
import secrets
from threading import Thread

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.models import db, User, AccessLog, utcnow
from app.utils.decorators import check_user_schedule
from app.utils.email import notify_admin_denied_access

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username', '').strip()).first()
        ip = request.remote_addr or ''

        if user and user.check_password(request.form.get('password', '')) and user.is_active_user:
            allowed, reason = check_user_schedule(user)
            if not allowed:
                log = AccessLog(user_id=user.id, username=user.username,
                                event='denied', ip_address=ip, reason=reason)
                db.session.add(log)
                db.session.commit()
                Thread(target=notify_admin_denied_access, args=(user, reason, ip)).start()
                flash(f'Acceso denegado: {reason}', 'error')
                return render_template('login.html')

            session_key = secrets.token_hex(16)
            log = AccessLog(user_id=user.id, username=user.username,
                            event='login', ip_address=ip, session_key=session_key)
            db.session.add(log)
            user.last_login = utcnow()
            db.session.commit()
            session['access_log_key'] = session_key
            login_user(user, remember=request.form.get('remember'))

            if user.must_change_password:
                flash('Por seguridad, debés cambiar tu contraseña antes de continuar.', 'warning')
                return redirect(url_for('auth.change_password'))

            return redirect(url_for('main.dashboard'))

        flash('Usuario o contraseña incorrectos.', 'error')
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    session_key = session.get('access_log_key', '')
    if session_key:
        login_log = AccessLog.query.filter_by(
            session_key=session_key, event='login'
        ).first()
        if login_log:
            duration = (utcnow() - login_log.timestamp).total_seconds() / 60
            log = AccessLog(
                user_id=current_user.id, username=current_user.username,
                event='logout', ip_address=request.remote_addr or '',
                session_key=session_key, duration_minutes=round(duration, 1)
            )
            db.session.add(log)
            db.session.commit()
    logout_user()
    return redirect(url_for('auth.login'))


@auth_bp.route('/cambiar-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_pw = request.form.get('current_password', '').strip()
        new_pw = request.form.get('password', '').strip()
        confirm = request.form.get('confirm', '').strip()
        if not current_user.check_password(current_pw):
            flash('La contraseña actual es incorrecta.', 'error')
        elif len(new_pw) < 8:
            flash('La nueva contraseña debe tener al menos 8 caracteres.', 'error')
        elif new_pw != confirm:
            flash('Las contraseñas no coinciden.', 'error')
        else:
            current_user.set_password(new_pw)
            current_user.must_change_password = False
            db.session.commit()
            flash('Contraseña actualizada correctamente.', 'success')
            return redirect(url_for('main.dashboard'))
    return render_template('change_password.html')
