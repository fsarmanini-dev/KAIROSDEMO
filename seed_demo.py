"""
Kairos Stock — Demo Data Seeder.
Run once to populate the database with demo data for Pint-Arte.

Usage:
    python seed_demo.py

Requires the app to be configured (database must exist).
Run after first 'python app.py' to initialize the DB.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.models import db, User, Category, Product, ProductStore, StoreConfig, \
    Proveedor, Plazo, StockMovement, Budget, BudgetItem, Venta, VentaItem, \
    CajaMovimiento, Order, OrderItem

app = create_app()

DEMO_PRODUCTS = [
    # PINTURAS
    {"name": "Látex Interior Blanco", "sku": "LAT-001", "category": "Pinturas", "price": 8500, "cost": 5200, "stock": 45, "min_stock": 10, "unit": "litro", "desc": "Pintura látex interior mate color blanco. Cubriente y lavable."},
    {"name": "Látex Interior Hueso", "sku": "LAT-002", "category": "Pinturas", "price": 8500, "cost": 5200, "stock": 30, "min_stock": 10, "unit": "litro", "desc": "Pintura látex interior color hueso. Ideal para living y dormitorios."},
    {"name": "Látex Exterior Blanco", "sku": "LAT-003", "category": "Pinturas", "price": 9500, "cost": 5800, "stock": 25, "min_stock": 8, "unit": "litro", "desc": "Pintura látex exterior con protección UV."},
    {"name": "Esmalte Sintético Blanco", "sku": "ESM-001", "category": "Pinturas", "price": 7200, "cost": 4400, "stock": 20, "min_stock": 5, "unit": "litro", "desc": "Esmalte sintético brillante color blanco para interiores y exteriores."},
    {"name": "Esmalte Sintético Negro", "sku": "ESM-002", "category": "Pinturas", "price": 7200, "cost": 4400, "stock": 15, "min_stock": 5, "unit": "litro", "desc": "Esmalte sintético brillante color negro."},
    {"name": "Esmalte al Agua Blanco", "sku": "ESM-003", "category": "Pinturas", "price": 6800, "cost": 4100, "stock": 18, "min_stock": 5, "unit": "litro", "desc": "Esmalte al agua satinado. Inodoro y de secado rápido."},
    {"name": "Barniz Marino Brillante", "sku": "BRN-001", "category": "Pinturas", "price": 12500, "cost": 7800, "stock": 12, "min_stock": 4, "unit": "litro", "desc": "Barniz marino brillante para exteriores. Protección máxima."},
    {"name": "Barniz Marino Mate", "sku": "BRN-002", "category": "Pinturas", "price": 12500, "cost": 7800, "stock": 8, "min_stock": 4, "unit": "litro", "desc": "Barniz marino mate para exteriores."},
    {"name": "Laca Acrílica Transparente", "sku": "LCA-001", "category": "Pinturas", "price": 9800, "cost": 6000, "stock": 10, "min_stock": 3, "unit": "litro", "desc": "Laca acrílica transparente brillante."},
    {"name": "Pintura Spray Blanco 400ml", "sku": "SPR-001", "category": "Pinturas", "price": 3200, "cost": 1900, "stock": 60, "min_stock": 12, "unit": "unidad", "desc": "Pintura spray acrílica color blanco 400ml."},

    # HERRAMIENTAS
    {"name": "Pincel Plano 1\"", "sku": "PIN-001", "category": "Herramientas", "price": 1200, "cost": 700, "stock": 100, "min_stock": 20, "unit": "unidad", "desc": "Pincel plano profesional cerdas sintéticas 1 pulgada."},
    {"name": "Pincel Plano 2\"", "sku": "PIN-002", "category": "Herramientas", "price": 1800, "cost": 1100, "stock": 80, "min_stock": 15, "unit": "unidad", "desc": "Pincel plano profesional cerdas sintéticas 2 pulgadas."},
    {"name": "Pincel Plano 3\"", "sku": "PIN-003", "category": "Herramientas", "price": 2500, "cost": 1500, "stock": 60, "min_stock": 10, "unit": "unidad", "desc": "Pincel plano profesional cerdas sintéticas 3 pulgadas."},
    {"name": "Pincel Angular 1.5\"", "sku": "PIN-004", "category": "Herramientas", "price": 1600, "cost": 950, "stock": 50, "min_stock": 10, "unit": "unidad", "desc": "Pincel angular para recortes y detalles."},
    {"name": "Rodillo Lana 15cm", "sku": "ROD-001", "category": "Herramientas", "price": 2800, "cost": 1700, "stock": 40, "min_stock": 8, "unit": "unidad", "desc": "Rodillo de lana 15cm con mango."},
    {"name": "Rodillo Lana 23cm", "sku": "ROD-002", "category": "Herramientas", "price": 3500, "cost": 2100, "stock": 35, "min_stock": 8, "unit": "unidad", "desc": "Rodillo de lana 23cm profesional."},
    {"name": "Cinta de Enmascarar 24mm", "sku": "CIN-001", "category": "Herramientas", "price": 800, "cost": 450, "stock": 200, "min_stock": 40, "unit": "unidad", "desc": "Cinta de enmascarar 24mm x 50m."},
    {"name": "Lija al Agua N°180", "sku": "LIJ-001", "category": "Herramientas", "price": 350, "cost": 180, "stock": 500, "min_stock": 100, "unit": "unidad", "desc": "Lija al agua grano 180."},
    {"name": "Lija al Agua N°220", "sku": "LIJ-002", "category": "Herramientas", "price": 350, "cost": 180, "stock": 500, "min_stock": 100, "unit": "unidad", "desc": "Lija al agua grano 220."},
    {"name": "Espátula Plástica 10cm", "sku": "ESP-001", "category": "Herramientas", "price": 600, "cost": 350, "stock": 80, "min_stock": 15, "unit": "unidad", "desc": "Espátula plástica flexible para enduido."},
    {"name": "Enduido Plástico 1kg", "sku": "END-001", "category": "Herramientas", "price": 2200, "cost": 1300, "stock": 30, "min_stock": 8, "unit": "unidad", "desc": "Enduido plástico listo para usar 1kg."},
    {"name": "Masilla Wallplast 1kg", "sku": "END-002", "category": "Herramientas", "price": 1800, "cost": 1000, "stock": 25, "min_stock": 6, "unit": "unidad", "desc": "Masilla wallplast 1kg para interiores."},

    # ACCESORIOS
    {"name": "Agua Ras 10g", "sku": "AGR-001", "category": "Accesorios", "price": 150, "cost": 70, "stock": 300, "min_stock": 50, "unit": "unidad", "desc": "Sobrecito de agua ras de 10g."},
    {"name": "Colorante Negro 50ml", "sku": "COL-001", "category": "Accesorios", "price": 950, "cost": 550, "stock": 40, "min_stock": 10, "unit": "unidad", "desc": "Colorante universal negro 50ml."},
    {"name": "Diluyente Sintético 1lt", "sku": "DIL-001", "category": "Accesorios", "price": 2800, "cost": 1600, "stock": 20, "min_stock": 5, "unit": "litro", "desc": "Diluyente para esmaltes sintéticos."},
    {"name": "Quitaesmalte 500ml", "sku": "DIL-002", "category": "Accesorios", "price": 1800, "cost": 1000, "stock": 15, "min_stock": 5, "unit": "litro", "desc": "Quitaesmalte para limpieza de herramientas."},
    {"name": "Guantes de Látex", "sku": "GUA-001", "category": "Accesorios", "price": 650, "cost": 350, "stock": 150, "min_stock": 30, "unit": "par", "desc": "Guantes de látex para pintar."},
    {"name": "Plástico Protección 4x5m", "sku": "PRO-001", "category": "Accesorios", "price": 1200, "cost": 700, "stock": 50, "min_stock": 10, "unit": "unidad", "desc": "Plástico para protección de superficies 4x5m."},

    # MATERIALES DE CONSTRUCCIÓN
    {"name": "Cemento Portland 50kg", "sku": "CEM-001", "category": "Materiales", "price": 4500, "cost": 2800, "stock": 40, "min_stock": 10, "unit": "bolsa", "desc": "Cemento Portland 50kg."},
    {"name": "Cal 30kg", "sku": "CAL-001", "category": "Materiales", "price": 3200, "cost": 1900, "stock": 25, "min_stock": 5, "unit": "bolsa", "desc": "Cal hidratada 30kg."},
    {"name": "Yeso 25kg", "sku": "YES-001", "category": "Materiales", "price": 2500, "cost": 1500, "stock": 20, "min_stock": 5, "unit": "bolsa", "desc": "Yeso fino 25kg."},
]

DEMO_PROVEEDORES = [
    {"name": "Alba Pinturas S.A.", "contact": "Carlos Méndez", "email": "carlos@albapinturas.com", "phone": "+54 11 4321-5678", "cuit": "30-71234567-8", "website": "www.albapinturas.com.ar"},
    {"name": "Colorín Químicos", "contact": "María López", "email": "ventas@coloring.com.ar", "phone": "+54 11 4987-6543", "cuit": "30-72345678-9", "website": "www.coloring.com.ar"},
    {"name": "Herramientas Pro", "contact": "Juan García", "email": "juan@herramientaspro.com", "phone": "+54 11 4765-4321", "cuit": "30-73456789-0", "website": "www.herramientaspro.com"},
    {"name": "Distribuidora del Oeste", "contact": "Ana Martínez", "email": "ana@distoeste.com.ar", "phone": "+54 11 4455-6677", "cuit": "30-74567890-1"},
    {"name": "Materiales del Sur", "contact": "Pedro Rodríguez", "email": "pedro@mdelsur.com", "phone": "+54 11 4123-4567", "cuit": "30-75678901-2", "website": "www.materialesdelsur.com"},
]

DEMO_PLAZOS = [
    {"name": "Contado", "days": 0, "desc": "Pago al contado efectivo o transferencia"},
    {"name": "7 Días", "days": 7, "desc": "Pago a 7 días"},
    {"name": "15 Días", "days": 15, "desc": "Pago a 15 días"},
    {"name": "30 Días", "days": 30, "desc": "Pago a 30 días"},
    {"name": "60 Días", "days": 60, "desc": "Pago a 60 días"},
]


def seed():
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("ERROR: Run the app first (python app.py) to initialize the DB.")
            return

        already_seeded = Category.query.filter(Category.name != 'General').filter(
            Category.name != 'Electrónica', Category.name != 'Herramientas').first()
        if already_seeded and Product.query.count() > 5:
            print("Demo data already exists. Skipping.")
            return

        print("Seeding demo data...")

        cat_map = {}
        demo_cats = ["Pinturas", "Herramientas", "Accesorios", "Materiales"]
        for cname in demo_cats:
            cat = Category.query.filter_by(name=cname).first()
            if not cat:
                cat = Category(name=cname, description=f"Categoría {cname.lower()}", color={
                    "Pinturas": "#6366f1", "Herramientas": "#f59e0b",
                    "Accesorios": "#10b981", "Materiales": "#ef4444"
                }[cname])
                db.session.add(cat)
                db.session.flush()
            cat_map[cname] = cat

        for pd in DEMO_PRODUCTS:
            existing = Product.query.filter_by(sku=pd["sku"]).first()
            if not existing:
                p = Product(
                    name=pd["name"], sku=pd["sku"],
                    category_id=cat_map[pd["category"]].id,
                    price=pd["price"], cost=pd["cost"],
                    stock=pd["stock"], min_stock=pd["min_stock"],
                    unit=pd["unit"], description=pd["desc"],
                    is_active=True
                )
                db.session.add(p)
                db.session.flush()
                sm = StockMovement(
                    product_id=p.id, user_id=admin.id,
                    movement_type="entrada", quantity=pd["stock"],
                    previous_stock=0, new_stock=pd["stock"],
                    notes="Stock inicial (demo)"
                )
                db.session.add(sm)
                ps = ProductStore(product_id=p.id, visible=True, featured=False)
                db.session.add(ps)

        for prov in DEMO_PROVEEDORES:
            existing = Proveedor.query.filter_by(name=prov["name"]).first()
            if not existing:
                db.session.add(Proveedor(
                    name=prov["name"], contact_name=prov["contact"],
                    email=prov["email"], phone=prov["phone"],
                    cuit=prov["cuit"], website=prov.get("website", ""),
                    is_active=True
                ))

        for pl in DEMO_PLAZOS:
            existing = Plazo.query.filter_by(name=pl["name"]).first()
            if not existing:
                db.session.add(Plazo(name=pl["name"], days=pl["days"], description=pl["desc"]))

        sc = StoreConfig.query.first()
        if sc:
            sc.store_name = "Pint-Arte"
            sc.store_slogan = "Todo para pintar y decorar"
            sc.store_description = "Tu tienda de confianza para pinturas, herramientas y materiales. ¡Transformá tus espacios con nosotros!"
            sc.primary_color = "#6366f1"
            sc.secondary_color = "#0f172a"
            sc.whatsapp_number = "+54 11 2345-6789"
            sc.contact_email = "tienda@pint-arte.com.ar"
            sc.address = "Av. Corrientes 1234, CABA"
            sc.instagram = "@pintarte.ok"
            sc.banner_title = "Decorá tu hogar con estilo"
            sc.banner_subtitle = "Los mejores precios en pinturas y accesorios. Envíos a todo el país."
            sc.footer_text = "© 2024 Pint-Arte — Todos los derechos reservados."
            sc.announcement_text = "🚚 Envíos gratis en compras mayores a $50.000"
            sc.announcement_enabled = True
            sc.about_title = "Sobre Pint-Arte"
            sc.about_text = "Somos una empresa familiar con más de 20 años de experiencia en el rubro de pinturerías. Ofrecemos productos de primera calidad y asesoramiento personalizado para cada proyecto."
            sc.about_enabled = True
            sc.mp_enabled = False
            sc.transfer_enabled = True
            sc.transfer_cbu = "0000003100054321054321"
            sc.transfer_alias = "pintarte.mp"
            sc.transfer_bank = "Banco Nación"
            sc.transfer_owner = "Pint-Arte SRL"

        db.session.commit()
        print(f"[OK] {len(DEMO_PRODUCTS)} productos creados")
        print(f"[OK] {len(DEMO_PROVEEDORES)} proveedores creados")
        print(f"[OK] {len(DEMO_PLAZOS)} plazos de pago creados")
        print(f"[OK] Tienda configurada como 'Pint-Arte'")
        print(f"[OK] Usuario admin: admin / admin123")
        print("\n[OK] Demo data lista!")


if __name__ == '__main__':
    seed()