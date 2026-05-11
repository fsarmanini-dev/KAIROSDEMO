from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


def utcnow():
    """Naive UTC now — compatible with Python 3.12+ and SQLAlchemy datetime columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ─── USERS & ACCESS ───────────────────────────────────────────────────────────

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='viewer')  # admin, editor, viewer
    created_at = db.Column(db.DateTime, default=utcnow)
    is_active_user = db.Column(db.Boolean, default=True)
    notify_low_stock = db.Column(db.Boolean, default=True)
    notify_new_budget = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime, nullable=True)
    avatar_url = db.Column(db.String(500), default='')
    must_change_password = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

    def can_edit(self):
        return self.role in ['admin', 'editor']


class UserSchedule(db.Model):
    """Allowed login windows per user, per day of week."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('schedules', lazy=True, cascade='all, delete-orphan'))
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday … 6=Sunday
    time_start = db.Column(db.String(5), nullable=False, default='08:00')
    time_end = db.Column(db.String(5), nullable=False, default='18:00')
    enabled = db.Column(db.Boolean, default=True)

    DAY_NAMES = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

    @property
    def day_name(self):
        return self.DAY_NAMES[self.day_of_week]


class AccessLog(db.Model):
    """Login / logout / failed-attempt audit log."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    user = db.relationship('User', backref=db.backref('access_logs', lazy=True))
    username = db.Column(db.String(80))
    event = db.Column(db.String(20))          # 'login', 'logout', 'denied'
    timestamp = db.Column(db.DateTime, default=utcnow)
    ip_address = db.Column(db.String(45), default='')
    session_key = db.Column(db.String(64), default='')
    duration_minutes = db.Column(db.Float, nullable=True)
    reason = db.Column(db.String(200), default='')


# ─── INVENTORY ────────────────────────────────────────────────────────────────

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(200))
    color = db.Column(db.String(7), default='#6366f1')
    products = db.relationship('Product', backref='category', lazy=True)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    sku = db.Column(db.String(50), unique=True)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    price = db.Column(db.Float, default=0.0)
    cost = db.Column(db.Float, default=0.0)
    stock = db.Column(db.Integer, default=0)
    min_stock = db.Column(db.Integer, default=5)
    unit = db.Column(db.String(20), default='unidad')
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    is_active = db.Column(db.Boolean, default=True)

    @property
    def low_stock(self):
        return self.stock <= self.min_stock

    @property
    def stock_value(self):
        return self.stock * self.cost


class StockMovement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product = db.relationship('Product', backref='movements')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='movements')
    movement_type = db.Column(db.String(20), nullable=False)  # entrada, salida, ajuste
    quantity = db.Column(db.Integer, nullable=False)
    previous_stock = db.Column(db.Integer)
    new_stock = db.Column(db.Integer)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utcnow)


# ─── BUDGETS ──────────────────────────────────────────────────────────────────

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    budget_number = db.Column(db.String(20), unique=True)
    client_name = db.Column(db.String(200), nullable=False)
    client_email = db.Column(db.String(120))
    client_phone = db.Column(db.String(30))
    client_address = db.Column(db.Text)
    notes = db.Column(db.Text)
    discount = db.Column(db.Float, default=0.0)
    tax = db.Column(db.Float, default=21.0)
    status = db.Column(db.String(20), default='borrador')
    created_at = db.Column(db.DateTime, default=utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='budgets')
    items = db.relationship('BudgetItem', backref='budget', lazy=True, cascade='all, delete-orphan')

    def generate_number(self):
        last = Budget.query.order_by(Budget.id.desc()).first()
        num = (last.id + 1) if last else 1
        self.budget_number = f"PRES-{datetime.now().year}-{num:04d}"

    @property
    def subtotal(self):
        return sum(item.subtotal for item in self.items)

    @property
    def discount_amount(self):
        return self.subtotal * (self.discount / 100)

    @property
    def tax_amount(self):
        return (self.subtotal - self.discount_amount) * (self.tax / 100)

    @property
    def total(self):
        return self.subtotal - self.discount_amount + self.tax_amount


class BudgetItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    budget_id = db.Column(db.Integer, db.ForeignKey('budget.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    product = db.relationship('Product')
    description = db.Column(db.String(300), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)

    @property
    def subtotal(self):
        return self.quantity * self.unit_price


# ─── STORE ────────────────────────────────────────────────────────────────────

class StoreConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    store_name = db.Column(db.String(200), default='Mi Tienda')
    store_slogan = db.Column(db.String(300), default='Los mejores productos al mejor precio')
    store_description = db.Column(db.Text, default='')
    whatsapp_number = db.Column(db.String(30), default='')
    primary_color = db.Column(db.String(7), default='#f97316')
    secondary_color = db.Column(db.String(7), default='#1e293b')
    logo_url = db.Column(db.String(500), default='')
    banner_url = db.Column(db.String(500), default='')
    show_stock = db.Column(db.Boolean, default=True)
    show_sku = db.Column(db.Boolean, default=False)
    contact_email = db.Column(db.String(120), default='')
    address = db.Column(db.String(300), default='')
    instagram = db.Column(db.String(100), default='')
    facebook = db.Column(db.String(100), default='')
    banner_title = db.Column(db.String(300), default='')
    banner_subtitle = db.Column(db.String(500), default='')
    featured_title = db.Column(db.String(200), default='⭐ Destacados')
    about_enabled = db.Column(db.Boolean, default=False)
    about_title = db.Column(db.String(200), default='¿Quiénes somos?')
    about_text = db.Column(db.Text, default='')
    about_image_url = db.Column(db.String(500), default='')
    announcement_enabled = db.Column(db.Boolean, default=False)
    announcement_text = db.Column(db.String(500), default='')
    announcement_color = db.Column(db.String(7), default='#f97316')
    footer_text = db.Column(db.Text, default='')
    mp_enabled = db.Column(db.Boolean, default=False)
    mp_public_key = db.Column(db.String(200), default='')
    mp_access_token = db.Column(db.String(200), default='')
    mp_success_url = db.Column(db.String(500), default='')
    transfer_enabled = db.Column(db.Boolean, default=False)
    transfer_cbu = db.Column(db.String(100), default='')
    transfer_alias = db.Column(db.String(100), default='')
    transfer_bank = db.Column(db.String(100), default='')
    transfer_owner = db.Column(db.String(150), default='')


class ProductStore(db.Model):
    """Extra store-specific fields for a product."""
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), unique=True)
    product = db.relationship('Product', backref='store_info')
    visible = db.Column(db.Boolean, default=True)
    featured = db.Column(db.Boolean, default=False)
    original_price = db.Column(db.Float, default=0.0)
    image_url = db.Column(db.String(500), default='')
    image_url_2 = db.Column(db.String(500), default='')
    image_url_3 = db.Column(db.String(500), default='')
    badge = db.Column(db.String(50), default='')
    colors = db.Column(db.String(300), default='')
    sizes = db.Column(db.String(300), default='')
    store_description = db.Column(db.Text, default='')
    sort_order = db.Column(db.Integer, default=0)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True)
    client_name = db.Column(db.String(200), nullable=False)
    client_email = db.Column(db.String(120))
    client_phone = db.Column(db.String(30))
    client_address = db.Column(db.Text)
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='nuevo')
    total = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=utcnow)
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')

    def generate_number(self):
        last = Order.query.order_by(Order.id.desc()).first()
        num = (last.id + 1) if last else 1
        self.order_number = f"PED-{datetime.now().year}-{num:04d}"


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    product = db.relationship('Product')
    description = db.Column(db.String(300))
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Float, default=0.0)
    color = db.Column(db.String(50), default='')
    size = db.Column(db.String(50), default='')

    @property
    def subtotal(self):
        return self.quantity * self.unit_price


# ─── CAJA (ATENCIÓN AL PÚBLICO) ───────────────────────────────────────────────

class Venta(db.Model):
    """Ticket de venta generado en la caja."""
    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.String(20), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='ventas')
    subtotal = db.Column(db.Float, default=0.0)
    tax_rate = db.Column(db.Float, default=0.0)   # 0 o 21
    tax_amount = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, default=0.0)
    payment_method = db.Column(db.String(30), default='efectivo')  # efectivo, tarjeta, transferencia
    notes = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=utcnow)
    items = db.relationship('VentaItem', backref='venta', lazy=True, cascade='all, delete-orphan')

    def generate_number(self):
        last = Venta.query.order_by(Venta.id.desc()).first()
        num = (last.id + 1) if last else 1
        self.ticket_number = f"TKT-{datetime.now().year}-{num:04d}"


class VentaItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey('venta.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    product = db.relationship('Product')
    description = db.Column(db.String(300), nullable=False)
    quantity = db.Column(db.Float, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False, default=0.0)

    @property
    def subtotal(self):
        return self.quantity * self.unit_price


class CajaMovimiento(db.Model):
    """Ingreso o egreso manual de dinero en caja."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='caja_movimientos')
    tipo = db.Column(db.String(10), nullable=False)   # 'ingreso' | 'egreso'
    monto = db.Column(db.Float, nullable=False)
    concepto = db.Column(db.String(300), default='')
    created_at = db.Column(db.DateTime, default=utcnow)


# ─── PROVEEDORES ──────────────────────────────────────────────────────────────

class Proveedor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    contact_name = db.Column(db.String(150), default='')
    email = db.Column(db.String(120), default='')
    phone = db.Column(db.String(50), default='')
    address = db.Column(db.String(300), default='')
    cuit = db.Column(db.String(30), default='')
    website = db.Column(db.String(300), default='')
    notes = db.Column(db.Text, default='')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)


# ─── PLAZOS DE PAGO ───────────────────────────────────────────────────────────

class Plazo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    days = db.Column(db.Integer, default=0)   # 0 = contado
    description = db.Column(db.String(300), default='')
