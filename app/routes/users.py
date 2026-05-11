"""User management, email config, staff monitoring routes."""
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.models import db, User, UserSchedule, AccessLog, utcnow
from app.utils.decorators import admin_required
from app.utils.email import send_email, email_template, send_whatsapp

users_bp = Blueprint('users', __name__)


# ─── USERS ────────────────────────────────────────────────────────────────────

@users_bp.route('/usuarios')
@login_required
@admin_required
def users():
    all_users = User.query.all()
    return render_template('users.html', users=all_users)


@users_bp.route('/usuarios/nuevo', methods=['POST'])
@login_required
@admin_required
def new_user():
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    role = request.form.get('role', 'viewer')

    if not username or not email or not password:
        flash('Todos los campos son obligatorios.', 'error')
        return redirect(url_for('users.users'))
    if len(password) < 8:
        flash('La contraseña debe tener al menos 8 caracteres.', 'error')
        return redirect(url_for('users.users'))
    if User.query.filter_by(username=username).first():
        flash('El nombre de usuario ya existe.', 'error')
        return redirect(url_for('users.users'))
    if User.query.filter_by(email=email).first():
        flash('El email ya está en uso.', 'error')
        return redirect(url_for('users.users'))

    user = User(username=username, email=email, role=role, must_change_password=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    flash(f'Usuario {username} creado. Deberá cambiar su contraseña en el primer inicio de sesión.', 'success')
    return redirect(url_for('users.users'))


@users_bp.route('/usuarios/<int:id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user(id):
    user = User.query.get_or_404(id)
    if user.id != current_user.id:
        user.is_active_user = not user.is_active_user
        db.session.commit()
        state = 'activado' if user.is_active_user else 'desactivado'
        flash(f'Usuario {user.username} {state}.', 'success')
    else:
        flash('No podés desactivar tu propia cuenta.', 'error')
    return redirect(url_for('users.users'))


@users_bp.route('/usuarios/<int:id>/editar', methods=['POST'])
@login_required
@admin_required
def edit_user(id):
    user = User.query.get_or_404(id)
    new_username = request.form.get('username', '').strip()
    new_email = request.form.get('email', '').strip()
    new_role = request.form.get('role', user.role)
    new_password = request.form.get('password', '').strip()
    new_avatar = request.form.get('avatar_url', '').strip()

    if new_username != user.username and User.query.filter_by(username=new_username).first():
        flash('Ese nombre de usuario ya existe.', 'error')
        return redirect(url_for('users.users'))
    if new_email != user.email and User.query.filter_by(email=new_email).first():
        flash('Ese email ya está en uso.', 'error')
        return redirect(url_for('users.users'))
    if new_password and len(new_password) < 8:
        flash('La nueva contraseña debe tener al menos 8 caracteres.', 'error')
        return redirect(url_for('users.users'))

    user.username = new_username or user.username
    user.email = new_email or user.email
    user.role = new_role
    user.avatar_url = new_avatar
    if new_password:
        user.set_password(new_password)
        user.must_change_password = False
    db.session.commit()
    flash(f'Usuario {user.username} actualizado.', 'success')
    return redirect(url_for('users.users'))


@users_bp.route('/usuarios/<int:id>/eliminar', methods=['POST'])
@login_required
@admin_required
def delete_user(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('No podés eliminar tu propia cuenta.', 'error')
        return redirect(url_for('users.users'))
    username = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f'Usuario {username} eliminado.', 'success')
    return redirect(url_for('users.users'))


# ─── EMAIL & NOTIFICATIONS CONFIG ─────────────────────────────────────────────

@users_bp.route('/configuracion/email', methods=['GET', 'POST'])
@login_required
@admin_required
def email_settings():
    from app import flask_app
    if request.method == 'POST':
        # Persist to environment at runtime — on next restart from .env these need to be set
        # For platforms like Railway, changes must be done via the Variables panel.
        # Here we update the live app config so the session picks them up immediately.
        mail_server = request.form.get('mail_server', '').strip()
        mail_port = request.form.get('mail_port', '587').strip()
        mail_username = request.form.get('mail_username', '').strip()
        mail_password = request.form.get('mail_password', '').strip()
        mail_tls = 'mail_use_tls' in request.form

        flask_app.config['MAIL_SERVER'] = mail_server
        flask_app.config['MAIL_PORT'] = int(mail_port) if mail_port.isdigit() else 587
        flask_app.config['MAIL_USERNAME'] = mail_username
        flask_app.config['MAIL_USE_TLS'] = mail_tls
        flask_app.config['MAIL_ENABLED'] = bool(mail_username)
        if mail_password:
            flask_app.config['MAIL_PASSWORD'] = mail_password
        if mail_username:
            flask_app.config['MAIL_DEFAULT_SENDER'] = mail_username

        # Reinitialise Flask-Mail with new config
        from app import mail
        mail.init_app(flask_app)

        flash('Configuración de email actualizada. Los cambios están activos en esta sesión. '
              'Para que persistan tras un reinicio, actualizá las variables de entorno en Railway.', 'info')
        return redirect(url_for('users.email_settings'))

    import os
    whatsapp_phone = os.environ.get('WHATSAPP_PHONE', '')
    whatsapp_enabled = bool(whatsapp_phone and os.environ.get('CALLMEBOT_APIKEY', ''))
    return render_template('email_settings.html',
        mail_server=flask_app.config.get('MAIL_SERVER', ''),
        mail_port=flask_app.config.get('MAIL_PORT', 587),
        mail_username=flask_app.config.get('MAIL_USERNAME', ''),
        mail_use_tls=flask_app.config.get('MAIL_USE_TLS', True),
        mail_enabled=flask_app.config.get('MAIL_ENABLED', False),
        whatsapp_phone=whatsapp_phone,
        whatsapp_enabled=whatsapp_enabled
    )


@users_bp.route('/configuracion/email/test', methods=['POST'])
@login_required
@admin_required
def test_email():
    content = """
    <div style="background:#d1fae5;border:1px solid #6ee7b7;border-radius:8px;padding:20px;margin-bottom:16px">
      <div style="font-size:24px;margin-bottom:8px">✅</div>
      <div style="font-size:16px;font-weight:600;color:#065f46">¡Email de prueba exitoso!</div>
    </div>
    <p style="font-size:14px;color:#64748b">Si recibiste este email, la configuración de correo está funcionando correctamente.</p>
    """
    send_email(
        subject="✅ Kairos Stock — Email de prueba",
        recipients=[current_user.email],
        html_body=email_template("Email de prueba", content, '#10b981')
    )
    flash(f'Email de prueba enviado a {current_user.email}.', 'success')
    return redirect(url_for('users.email_settings'))


@users_bp.route('/configuracion/whatsapp/test', methods=['POST'])
@login_required
@admin_required
def test_whatsapp():
    import os
    phone = os.environ.get('WHATSAPP_PHONE', '')
    if not phone:
        flash('WhatsApp no configurado. Agregá WHATSAPP_PHONE y CALLMEBOT_APIKEY en las variables de entorno.', 'error')
        return redirect(url_for('users.email_settings'))
    message = "✅ *Kairos Stock — Prueba exitosa*\n\nSi recibís este mensaje, las notificaciones de WhatsApp están funcionando."
    ok = send_whatsapp(phone, message)
    if ok:
        flash(f'Mensaje de prueba enviado a WhatsApp ({phone}).', 'success')
    else:
        flash('No se pudo enviar el mensaje. Verificá WHATSAPP_PHONE y CALLMEBOT_APIKEY.', 'error')
    return redirect(url_for('users.email_settings'))


@users_bp.route('/configuracion/notificaciones', methods=['POST'])
@login_required
def update_notifications():
    current_user.notify_low_stock = 'notify_low_stock' in request.form
    current_user.notify_new_budget = 'notify_new_budget' in request.form
    db.session.commit()
    flash('Preferencias de notificación actualizadas.', 'success')
    return redirect(url_for('users.email_settings') if current_user.is_admin() else url_for('main.dashboard'))


# ─── STAFF MONITOR ────────────────────────────────────────────────────────────

@users_bp.route('/admin/staff')
@login_required
@admin_required
def staff_monitor():
    all_users = User.query.filter(User.role != 'admin').all()
    cutoff = utcnow() - timedelta(hours=8)
    online_users = []
    for u in User.query.all():
        login_log = AccessLog.query.filter(
            AccessLog.user_id == u.id,
            AccessLog.event == 'login',
            AccessLog.timestamp >= cutoff
        ).order_by(AccessLog.timestamp.desc()).first()
        if login_log:
            logout_log = AccessLog.query.filter_by(
                session_key=login_log.session_key, event='logout'
            ).first()
            if not logout_log:
                online_users.append({'user': u, 'since': login_log.timestamp, 'ip': login_log.ip_address})

    recent_logs = AccessLog.query.order_by(AccessLog.timestamp.desc()).limit(100).all()
    denied_logs = AccessLog.query.filter_by(event='denied').order_by(AccessLog.timestamp.desc()).limit(50).all()

    session_stats = []
    for u in User.query.all():
        logout_logs = AccessLog.query.filter_by(user_id=u.id, event='logout').all()
        total_min = sum(l.duration_minutes or 0 for l in logout_logs)
        session_count = len(logout_logs)
        session_stats.append({
            'user': u,
            'total_hours': round(total_min / 60, 1),
            'sessions': session_count,
            'avg_min': round(total_min / session_count, 0) if session_count else 0
        })

    return render_template('staff_monitor.html',
        users=all_users,
        online_users=online_users,
        recent_logs=recent_logs,
        denied_logs=denied_logs,
        session_stats=session_stats
    )


@users_bp.route('/admin/staff/<int:id>/horarios', methods=['GET', 'POST'])
@login_required
@admin_required
def staff_schedules(id):
    user = User.query.get_or_404(id)
    if request.method == 'POST':
        UserSchedule.query.filter_by(user_id=id).delete()
        for day in range(7):
            enabled = f'day_{day}_enabled' in request.form
            time_start = request.form.get(f'day_{day}_start', '08:00')
            time_end = request.form.get(f'day_{day}_end', '18:00')
            db.session.add(UserSchedule(
                user_id=id, day_of_week=day,
                time_start=time_start, time_end=time_end, enabled=enabled
            ))
        db.session.commit()
        flash(f'Horarios de {user.username} guardados.', 'success')
        return redirect(url_for('users.staff_monitor'))

    existing = {s.day_of_week: s for s in user.schedules}
    schedule_map = [{
        'day': day,
        'name': UserSchedule.DAY_NAMES[day],
        'enabled': existing[day].enabled if day in existing else False,
        'start': existing[day].time_start if day in existing else '08:00',
        'end': existing[day].time_end if day in existing else '18:00',
    } for day in range(7)]
    return render_template('staff_schedules.html', user=user, schedule_map=schedule_map)


@users_bp.route('/admin/staff/logs/clear', methods=['POST'])
@login_required
@admin_required
def clear_access_logs():
    days = int(request.form.get('days', 30))
    cutoff = utcnow() - timedelta(days=days)
    deleted = AccessLog.query.filter(AccessLog.timestamp < cutoff).delete()
    db.session.commit()
    flash(f'{deleted} registros eliminados (más de {days} días).', 'success')
    return redirect(url_for('users.staff_monitor'))
