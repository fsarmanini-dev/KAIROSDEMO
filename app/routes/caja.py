"""Caja — Punto de venta / Atención al público."""
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from app.models import db, Product, Category, Venta, VentaItem, CajaMovimiento, StockMovement, utcnow
from app.utils.decorators import editor_required

caja_bp = Blueprint('caja', __name__)


# ─── VISTA PRINCIPAL ──────────────────────────────────────────────────────────

@caja_bp.route('/caja')
@login_required
def caja():
    products = Product.query.filter(
        Product.is_active == True,
        Product.stock > 0
    ).order_by(Product.name).all()
    categories = Category.query.all()

    # Resumen del día
    hoy = date.today()
    ventas_hoy = Venta.query.filter(
        db.func.date(Venta.created_at) == hoy
    ).all()
    ingresos_hoy = CajaMovimiento.query.filter(
        db.func.date(CajaMovimiento.created_at) == hoy,
        CajaMovimiento.tipo == 'ingreso'
    ).all()
    egresos_hoy = CajaMovimiento.query.filter(
        db.func.date(CajaMovimiento.created_at) == hoy,
        CajaMovimiento.tipo == 'egreso'
    ).all()

    total_ventas_hoy = sum(v.total for v in ventas_hoy)
    total_ingresos_hoy = sum(m.monto for m in ingresos_hoy)
    total_egresos_hoy = sum(m.monto for m in egresos_hoy)
    saldo_caja = total_ventas_hoy + total_ingresos_hoy - total_egresos_hoy

    return render_template('caja.html',
        products=products,
        categories=categories,
        total_ventas_hoy=total_ventas_hoy,
        total_ingresos_hoy=total_ingresos_hoy,
        total_egresos_hoy=total_egresos_hoy,
        saldo_caja=saldo_caja,
        cant_ventas_hoy=len(ventas_hoy),
    )


# ─── PROCESAR VENTA ───────────────────────────────────────────────────────────

@caja_bp.route('/caja/venta', methods=['POST'])
@login_required
@editor_required
def procesar_venta():
    data = request.get_json()
    items_data = data.get('items', [])
    if not items_data:
        return jsonify({'error': 'El ticket no tiene ítems.'}), 400

    tax_rate = float(data.get('tax_rate', 0))
    if tax_rate not in (0, 21):
        return jsonify({'error': 'IVA inválido.'}), 400

    # Validate stock before touching anything
    for item_data in items_data:
        pid = item_data.get('product_id')
        if pid:
            product = Product.query.get(pid)
            if not product or not product.is_active:
                return jsonify({'error': f'Producto no encontrado: {item_data.get("description")}'}), 400
            qty = float(item_data.get('quantity', 1))
            if product.stock < qty:
                return jsonify({'error': f'Stock insuficiente para "{product.name}". Disponible: {product.stock}'}), 400

    venta = Venta(
        user_id=current_user.id,
        tax_rate=tax_rate,
        payment_method=data.get('payment_method', 'efectivo'),
        notes=data.get('notes', ''),
    )
    venta.generate_number()
    db.session.add(venta)
    db.session.flush()

    subtotal = 0.0
    for item_data in items_data:
        qty = float(item_data.get('quantity', 1))
        price = float(item_data.get('unit_price', 0))
        item = VentaItem(
            venta_id=venta.id,
            product_id=item_data.get('product_id') or None,
            description=item_data['description'],
            quantity=qty,
            unit_price=price,
        )
        db.session.add(item)
        subtotal += item.subtotal

        # Descontar stock
        pid = item_data.get('product_id')
        if pid:
            product = Product.query.get(pid)
            prev = product.stock
            product.stock -= int(qty)
            product.updated_at = utcnow()
            db.session.add(StockMovement(
                product_id=product.id,
                user_id=current_user.id,
                movement_type='salida',
                quantity=int(qty),
                previous_stock=prev,
                new_stock=product.stock,
                notes=f'Venta caja {venta.ticket_number}',
            ))

    venta.subtotal = subtotal
    venta.tax_amount = subtotal * (tax_rate / 100)
    venta.total = subtotal + venta.tax_amount
    db.session.commit()

    return jsonify({
        'ticket_number': venta.ticket_number,
        'subtotal': venta.subtotal,
        'tax_amount': venta.tax_amount,
        'total': venta.total,
        'items': [{'description': i.description, 'quantity': i.quantity,
                   'unit_price': i.unit_price, 'subtotal': i.subtotal}
                  for i in venta.items],
    })


# ─── MOVIMIENTOS DE CAJA (INGRESO / EGRESO) ───────────────────────────────────

@caja_bp.route('/caja/movimiento', methods=['POST'])
@login_required
@editor_required
def movimiento_caja():
    data = request.get_json()
    tipo = data.get('tipo')
    if tipo not in ('ingreso', 'egreso'):
        return jsonify({'error': 'Tipo inválido.'}), 400
    try:
        monto = float(data.get('monto', 0))
        if monto <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({'error': 'Monto inválido.'}), 400

    mov = CajaMovimiento(
        user_id=current_user.id,
        tipo=tipo,
        monto=monto,
        concepto=data.get('concepto', '').strip(),
    )
    db.session.add(mov)
    db.session.commit()
    return jsonify({'ok': True, 'tipo': tipo, 'monto': monto})


# ─── HISTORIAL ────────────────────────────────────────────────────────────────

@caja_bp.route('/caja/historial')
@login_required
def historial_caja():
    page = request.args.get('page', 1, type=int)
    fecha = request.args.get('fecha', '')

    q_ventas = Venta.query.order_by(Venta.created_at.desc())
    q_movs = CajaMovimiento.query.order_by(CajaMovimiento.created_at.desc())

    if fecha:
        try:
            d = datetime.strptime(fecha, '%Y-%m-%d').date()
            q_ventas = q_ventas.filter(db.func.date(Venta.created_at) == d)
            q_movs = q_movs.filter(db.func.date(CajaMovimiento.created_at) == d)
        except ValueError:
            pass

    ventas = q_ventas.paginate(page=page, per_page=30)
    movimientos = q_movs.limit(50).all()

    total_ventas = sum(v.total for v in ventas.items)
    total_ingresos = sum(m.monto for m in movimientos if m.tipo == 'ingreso')
    total_egresos = sum(m.monto for m in movimientos if m.tipo == 'egreso')

    return render_template('caja_historial.html',
        ventas=ventas,
        movimientos=movimientos,
        total_ventas=total_ventas,
        total_ingresos=total_ingresos,
        total_egresos=total_egresos,
        fecha=fecha,
    )


# ─── DETALLE TICKET ───────────────────────────────────────────────────────────

@caja_bp.route('/caja/ticket/<int:id>')
@login_required
def ver_ticket(id):
    venta = Venta.query.get_or_404(id)
    return jsonify({
        'ticket_number': venta.ticket_number,
        'created_at': venta.created_at.strftime('%d/%m/%Y %H:%M'),
        'user': venta.user.username,
        'subtotal': venta.subtotal,
        'tax_rate': venta.tax_rate,
        'tax_amount': venta.tax_amount,
        'total': venta.total,
        'payment_method': venta.payment_method,
        'notes': venta.notes,
        'items': [{'description': i.description, 'quantity': i.quantity,
                   'unit_price': i.unit_price, 'subtotal': i.subtotal}
                  for i in venta.items],
    })
