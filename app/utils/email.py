"""Email and WhatsApp notification helpers."""
from threading import Thread
import os


# ─── ASYNC EMAIL ──────────────────────────────────────────────────────────────

def send_async_email(flask_app, msg):
    with flask_app.app_context():
        try:
            from app import mail
            mail.send(msg)
        except Exception as e:
            flask_app.logger.error(f"[EMAIL ERROR] {e}")


def send_email(subject, recipients, html_body, attachments=None):
    from app import flask_app, mail
    if not flask_app.config.get('MAIL_ENABLED'):
        flask_app.logger.info(f"[EMAIL DISABLED] To: {recipients} | Subject: {subject}")
        return
    if not recipients:
        return
    from flask_mail import Message
    msg = Message(subject=subject, recipients=recipients, html=html_body)
    if attachments:
        for name, data, mime in attachments:
            msg.attach(name, mime, data)
    Thread(target=send_async_email, args=(flask_app, msg)).start()


def email_template(title, content, color='#6366f1', brand_name='Kairos Stock'):
    """Wrap content in a clean branded HTML email template."""
    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:'Segoe UI',Arial,sans-serif">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f1f5f9;padding:32px 16px">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%">
        <tr><td style="background:{color};border-radius:12px 12px 0 0;padding:28px 32px">
          <div style="font-size:22px;font-weight:700;color:white;letter-spacing:-0.5px">
            📦 {brand_name}
          </div>
          <div style="font-size:13px;color:rgba(255,255,255,0.75);margin-top:4px">Sistema de Gestión de Inventario</div>
        </td></tr>
        <tr><td style="background:#ffffff;padding:32px;border-left:1px solid #e2e8f0;border-right:1px solid #e2e8f0">
          <h2 style="margin:0 0 16px;font-size:20px;color:#1e293b;font-weight:700">{title}</h2>
          {content}
        </td></tr>
        <tr><td style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:0 0 12px 12px;padding:20px 32px;text-align:center">
          <p style="margin:0;font-size:12px;color:#94a3b8">
            Este email fue enviado automáticamente por {brand_name}.<br>
            Por favor no respondas este mensaje.
          </p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


# ─── WHATSAPP (CallMeBot) ─────────────────────────────────────────────────────

def send_whatsapp(phone, message):
    """Send WhatsApp message via CallMeBot API."""
    import urllib.request
    import urllib.parse
    apikey = os.environ.get('CALLMEBOT_APIKEY', '')
    if not apikey or not phone:
        print(f"[WHATSAPP DISABLED] {message}")
        return False
    try:
        encoded = urllib.parse.quote(message)
        url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={encoded}&apikey={apikey}"
        req = urllib.request.Request(url, headers={"User-Agent": "KairosStock/1.0"})
        urllib.request.urlopen(req, timeout=10)
        print(f"[WHATSAPP OK] To: {phone}")
        return True
    except Exception as e:
        print(f"[WHATSAPP ERROR] {e}")
        return False


# ─── NOTIFICATIONS ────────────────────────────────────────────────────────────

def notify_low_stock_alert(product):
    from app.models import User
    recipients = [
        u.email for u in User.query.filter(
            User.is_active_user == True,
            User.role.in_(['admin', 'editor']),
            User.notify_low_stock == True
        ).all()
        if u.email
    ]
    content = f"""
    <div style="background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;padding:20px;margin-bottom:20px">
      <div style="font-size:28px;margin-bottom:8px">⚠️</div>
      <div style="font-size:16px;font-weight:600;color:#c2410c;margin-bottom:4px">Stock bajo detectado</div>
      <div style="font-size:14px;color:#92400e">El producto llegó al nivel mínimo de stock</div>
    </div>
    <table style="width:100%;border-collapse:collapse;margin-bottom:20px">
      <tr style="background:#f8fafc"><td style="padding:10px 14px;font-size:12px;font-weight:600;text-transform:uppercase;color:#64748b;border-bottom:1px solid #e2e8f0">Producto</td><td style="padding:10px 14px;font-size:14px;color:#1e293b;font-weight:600;border-bottom:1px solid #e2e8f0">{product.name}</td></tr>
      <tr><td style="padding:10px 14px;font-size:12px;font-weight:600;text-transform:uppercase;color:#64748b;border-bottom:1px solid #e2e8f0">SKU</td><td style="padding:10px 14px;font-size:14px;color:#1e293b;border-bottom:1px solid #e2e8f0">{product.sku or '—'}</td></tr>
      <tr style="background:#f8fafc"><td style="padding:10px 14px;font-size:12px;font-weight:600;text-transform:uppercase;color:#64748b;border-bottom:1px solid #e2e8f0">Stock actual</td><td style="padding:10px 14px;font-size:18px;font-weight:700;color:#ef4444;border-bottom:1px solid #e2e8f0">{product.stock} {product.unit}</td></tr>
      <tr><td style="padding:10px 14px;font-size:12px;font-weight:600;text-transform:uppercase;color:#64748b">Stock mínimo</td><td style="padding:10px 14px;font-size:14px;color:#1e293b">{product.min_stock} {product.unit}</td></tr>
    </table>
    <p style="font-size:14px;color:#64748b;margin:0">Ingresá al sistema para reponer el stock de este producto.</p>
    """
    send_email(
        subject=f"⚠️ Kairos Stock — Stock bajo: {product.name}",
        recipients=recipients,
        html_body=email_template(f"Stock bajo: {product.name}", content, '#f59e0b')
    )


def notify_whatsapp_low_stock(product):
    phone = os.environ.get("WHATSAPP_PHONE", "")
    if not phone:
        return
    message = (
        f"⚠️ *Kairos Stock — Stock Bajo*\n\n"
        f"📦 *Producto:* {product.name}\n"
        f"📉 *Stock actual:* {product.stock} {product.unit}\n"
        f"🔔 *Stock mínimo:* {product.min_stock} {product.unit}\n\n"
        f"Ingresá al sistema para reponer el stock."
    )
    Thread(target=send_whatsapp, args=(phone, message)).start()


def notify_budget_created(budget):
    from app.models import User
    recipients = [
        u.email for u in User.query.filter(
            User.is_active_user == True,
            User.role == 'admin',
            User.notify_new_budget == True
        ).all()
        if u.email
    ]
    content = f"""
    <div style="background:#eef2ff;border:1px solid #c7d2fe;border-radius:8px;padding:20px;margin-bottom:20px">
      <div style="font-size:28px;margin-bottom:8px">💰</div>
      <div style="font-size:16px;font-weight:600;color:#4338ca">Nuevo presupuesto generado</div>
    </div>
    <table style="width:100%;border-collapse:collapse;margin-bottom:20px">
      <tr style="background:#f8fafc"><td style="padding:10px 14px;font-size:12px;font-weight:600;text-transform:uppercase;color:#64748b;border-bottom:1px solid #e2e8f0">N° Presupuesto</td><td style="padding:10px 14px;font-size:14px;color:#6366f1;font-weight:700;border-bottom:1px solid #e2e8f0">{budget.budget_number}</td></tr>
      <tr><td style="padding:10px 14px;font-size:12px;font-weight:600;text-transform:uppercase;color:#64748b;border-bottom:1px solid #e2e8f0">Cliente</td><td style="padding:10px 14px;font-size:14px;color:#1e293b;font-weight:600;border-bottom:1px solid #e2e8f0">{budget.client_name}</td></tr>
      <tr style="background:#f8fafc"><td style="padding:10px 14px;font-size:12px;font-weight:600;text-transform:uppercase;color:#64748b;border-bottom:1px solid #e2e8f0">Total</td><td style="padding:10px 14px;font-size:20px;font-weight:700;color:#10b981;border-bottom:1px solid #e2e8f0">${budget.total:,.2f}</td></tr>
      <tr><td style="padding:10px 14px;font-size:12px;font-weight:600;text-transform:uppercase;color:#64748b;border-bottom:1px solid #e2e8f0">Ítems</td><td style="padding:10px 14px;font-size:14px;color:#1e293b;border-bottom:1px solid #e2e8f0">{len(budget.items)}</td></tr>
      <tr style="background:#f8fafc"><td style="padding:10px 14px;font-size:12px;font-weight:600;text-transform:uppercase;color:#64748b">Creado por</td><td style="padding:10px 14px;font-size:14px;color:#1e293b">{budget.user.username}</td></tr>
    </table>
    """
    send_email(
        subject=f"💰 Kairos Stock — Nuevo presupuesto {budget.budget_number} para {budget.client_name}",
        recipients=recipients,
        html_body=email_template(f"Nuevo presupuesto: {budget.budget_number}", content)
    )


def notify_whatsapp_budget(budget):
    phone = os.environ.get("WHATSAPP_PHONE", "")
    if not phone:
        return
    message = (
        f"💰 *Kairos Stock — Nuevo Presupuesto*\n\n"
        f"🔢 *N°:* {budget.budget_number}\n"
        f"👤 *Cliente:* {budget.client_name}\n"
        f"💵 *Total:* ${budget.total:,.2f}\n"
        f"👨‍💼 *Creado por:* {budget.user.username}"
    )
    Thread(target=send_whatsapp, args=(phone, message)).start()


def notify_admin_denied_access(user, reason, ip):
    from app.models import User
    from datetime import datetime
    admins = User.query.filter_by(role='admin', is_active_user=True).all()
    wa_phone = os.environ.get('WHATSAPP_PHONE', '')
    if wa_phone:
        msg_wa = (
            f"🚫 *Kairos Stock — Acceso Bloqueado*\n\n"
            f"👤 *Usuario:* {user.username}\n"
            f"🕐 *Motivo:* {reason}\n"
            f"🌐 *IP:* {ip}\n"
            f"📅 *Fecha:* {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        )
        Thread(target=send_whatsapp, args=(wa_phone, msg_wa)).start()

    from app import flask_app
    if flask_app.config.get('MAIL_ENABLED'):
        admin_emails = [a.email for a in admins if a.email]
        if admin_emails:
            from datetime import datetime
            content = f"""
            <div style="background:#fef2f2;border:1px solid #fecaca;border-radius:8px;padding:20px;margin-bottom:16px">
              <div style="font-size:28px;margin-bottom:8px">🚫</div>
              <div style="font-size:16px;font-weight:600;color:#b91c1c">Intento de acceso fuera de horario</div>
            </div>
            <table style="width:100%;border-collapse:collapse;font-size:14px">
              <tr><td style="padding:8px 12px;color:#64748b;font-weight:600">Usuario</td><td style="padding:8px 12px">{user.username}</td></tr>
              <tr style="background:#f8fafc"><td style="padding:8px 12px;color:#64748b;font-weight:600">Motivo</td><td style="padding:8px 12px">{reason}</td></tr>
              <tr><td style="padding:8px 12px;color:#64748b;font-weight:600">IP</td><td style="padding:8px 12px">{ip}</td></tr>
              <tr style="background:#f8fafc"><td style="padding:8px 12px;color:#64748b;font-weight:600">Fecha y hora</td><td style="padding:8px 12px">{datetime.now().strftime('%d/%m/%Y %H:%M')}</td></tr>
            </table>
            """
            send_email(
                subject=f"🚫 Acceso bloqueado: {user.username}",
                recipients=admin_emails,
                html_body=email_template("Acceso Bloqueado", content, '#ef4444')
            )


def send_budget_to_client(budget, pdf_bytes):
    if not budget.client_email:
        return False
    items_html = ''.join([
        f"<tr><td style='padding:8px 12px;border-bottom:1px solid #e2e8f0'>{item.description}</td>"
        f"<td style='padding:8px 12px;border-bottom:1px solid #e2e8f0;text-align:right'>{item.quantity:g}</td>"
        f"<td style='padding:8px 12px;border-bottom:1px solid #e2e8f0;text-align:right'>${item.unit_price:,.2f}</td>"
        f"<td style='padding:8px 12px;border-bottom:1px solid #e2e8f0;text-align:right;font-weight:600'>${item.subtotal:,.2f}</td></tr>"
        for item in budget.items
    ])
    content = f"""
    <p style="font-size:15px;color:#475569;margin:0 0 20px">Estimado/a <strong>{budget.client_name}</strong>,</p>
    <p style="font-size:14px;color:#64748b;margin:0 0 24px">Adjuntamos el presupuesto solicitado:</p>
    <table style="width:100%;border-collapse:collapse;margin-bottom:20px;font-size:14px">
      <thead><tr style="background:#6366f1">
        <th style="padding:10px 12px;color:white;text-align:left">Descripción</th>
        <th style="padding:10px 12px;color:white;text-align:right">Cant.</th>
        <th style="padding:10px 12px;color:white;text-align:right">Precio</th>
        <th style="padding:10px 12px;color:white;text-align:right">Subtotal</th>
      </tr></thead>
      <tbody>{items_html}</tbody>
    </table>
    <table style="width:100%;margin-bottom:24px">
      <tr><td style="text-align:right;padding:4px 12px;color:#64748b;font-size:13px">Subtotal:</td><td style="text-align:right;padding:4px 12px;font-weight:600;font-size:13px">${budget.subtotal:,.2f}</td></tr>
      {'<tr><td style="text-align:right;padding:4px 12px;color:#64748b;font-size:13px">Descuento ('+str(int(budget.discount))+"%):</td><td style='text-align:right;padding:4px 12px;color:#ef4444;font-size:13px'>-${:.2f}</td></tr>".format(budget.discount_amount) if budget.discount > 0 else ''}
      {'<tr><td style="text-align:right;padding:4px 12px;color:#64748b;font-size:13px">IVA ('+str(int(budget.tax))+"%):</td><td style='text-align:right;padding:4px 12px;font-size:13px'>${:.2f}</td></tr>".format(budget.tax_amount) if budget.tax > 0 else ''}
      <tr style="border-top:2px solid #6366f1"><td style="text-align:right;padding:10px 12px;font-weight:700;color:#6366f1;font-size:16px">TOTAL:</td><td style="text-align:right;padding:10px 12px;font-weight:700;color:#6366f1;font-size:18px">${budget.total:,.2f}</td></tr>
    </table>
    {'<div style="background:#f8fafc;border-radius:8px;padding:16px;margin-bottom:20px"><p style="margin:0;font-size:13px;color:#64748b"><strong>Notas:</strong> ' + budget.notes + '</p></div>' if budget.notes else ''}
    <p style="font-size:13px;color:#94a3b8;margin:0">El presupuesto tiene validez de 30 días desde su emisión.</p>
    """
    send_email(
        subject=f"Presupuesto {budget.budget_number} — Kairos Stock",
        recipients=[budget.client_email],
        html_body=email_template(f"Su presupuesto N° {budget.budget_number}", content),
        attachments=[(f"presupuesto_{budget.budget_number}.pdf", pdf_bytes, 'application/pdf')]
    )
    return True
