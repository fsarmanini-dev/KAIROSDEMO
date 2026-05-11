"""
Kairos Stock — Application factory.
"""
import os
import sys

from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect

from app.models import db

mail = Mail()
login_manager = LoginManager()
csrf = CSRFProtect()

flask_app = None


def create_app():
    global flask_app

    app = Flask(__name__, template_folder='../templates', static_folder='../static')

    secret_key = os.environ.get('SECRET_KEY', '')
    if not secret_key:
        if os.environ.get('FLASK_ENV') == 'production' or os.environ.get('RAILWAY_ENVIRONMENT'):
            sys.exit(
                "ERROR: La variable de entorno SECRET_KEY no está definida. "
                "Generá una con: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        import secrets as _s
        secret_key = _s.token_hex(32)
        print("[WARNING] SECRET_KEY no definida — usando clave temporal de desarrollo.")
    app.config['SECRET_KEY'] = secret_key
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600

    db_url = os.environ.get('DATABASE_URL', 'sqlite:///kairos_stock.db')
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER',
                                                        os.environ.get('MAIL_USERNAME', ''))
    app.config['MAIL_ENABLED'] = bool(os.environ.get('MAIL_USERNAME', ''))

    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    csrf.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.inventory import inventory_bp
    from app.routes.budgets import budgets_bp
    from app.routes.users import users_bp
    from app.routes.store import store_bp
    from app.routes.caja import caja_bp
    from app.routes.proveedores import proveedores_bp
    from app.routes.plazos import plazos_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(budgets_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(store_bp)
    app.register_blueprint(caja_bp)
    app.register_blueprint(proveedores_bp)
    app.register_blueprint(plazos_bp)

    with app.app_context():
        _init_db(app)

    flask_app = app
    return app


def _init_db(app):
    try:
        db.create_all()
        from app.models import User, Category
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@kairos.local',
                role='admin',
                must_change_password=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            for cat in [
                Category(name='General', description='Productos generales', color='#6366f1'),
                Category(name='Electrónica', description='Equipos electrónicos', color='#06b6d4'),
                Category(name='Herramientas', description='Herramientas y equipamiento', color='#f59e0b'),
            ]:
                db.session.add(cat)
            db.session.commit()
            app.logger.info("Base de datos inicializada. Usuario admin debe cambiar contraseña.")
    except Exception as e:
        app.logger.warning(f"[init_db] {e}")
