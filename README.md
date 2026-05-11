# 🎨 Pint-Arte — Sistema de Gestión de Inventario

Sistema completo de gestión comercial desarrollado en Python/Flask. Ideal para pinturerías, ferreterías y comercios minoristas.

## ✨ Características

| Módulo | Descripción |
|--------|-------------|
| **Dashboard** | Resumen con estadísticas, stock bajo, gráficos y actividad reciente |
| **Punto de Venta** | Interfaz tipo POS con productos, carrito, IVA y métodos de pago |
| **Productos** | CRUD completo, búsqueda, filtros, importación/exportación Excel |
| **Categorías** | Gestión con colores personalizados |
| **Stock** | Control de movimientos (entrada/salida/ajuste) con alertas de stock bajo |
| **Presupuestos** | Creación con PDF exportable, envío por email |
| **Proveedores** | Gestión completa con importación/exportación |
| **Plazos de Pago** | Configuración de plazos (contado, 7, 15, 30, 60 días) |
| **Tienda Online** | Catálogo público con carrito, MercadoPago y transferencia |
| **Usuarios** | Roles (admin/editor/viewer), horarios por día, monitoreo |
| **Notificaciones** | Email SMTP + WhatsApp (CallMeBot) |
| **Staff** | Monitoreo de sesiones, logs de acceso, horarios programados |

## 🚀 Inicio Rápido

```bash
# 1. Clonar o descargar
cd pint-arte-demo

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Iniciar la app (crea DB y admin automáticamente)
python app.py

# 5. Cargar datos demo (opcional, recomendado)
python seed_demo.py
```

Luego abrí `http://localhost:5000` e iniciá sesión con:

```
Usuario: admin
Contraseña: admin123
```

## 🐳 Docker

```bash
docker build -t pint-arte .
docker run -p 5000:5000 -e SECRET_KEY=mi-clave-secreta pint-arte
```

## 🏗️ Estructura

```
pint-arte/
├── app.py                  # Entry point
├── seed_demo.py            # Datos demo precargados
├── app/
│   ├── __init__.py         # Application factory + CSRF
│   ├── models.py           # Modelos SQLAlchemy
│   ├── routes/
│   │   ├── auth.py         # Login con rate limiting
│   │   ├── main.py         # Dashboard y API
│   │   ├── inventory.py    # Productos, categorías, movimientos
│   │   ├── budgets.py      # Presupuestos y PDF
│   │   ├── caja.py         # Punto de venta
│   │   ├── store.py        # Tienda online
│   │   ├── users.py        # Usuarios, email, staff
│   │   ├── proveedores.py  # Proveedores
│   │   └── plazos.py       # Plazos de pago
│   └── utils/
│       ├── email.py        # Email + WhatsApp
│       ├── pdf.py          # PDF con ReportLab
│       └── decorators.py   # @admin_required, @editor_required
├── templates/              # Tailwind CSS + Font Awesome
├── static/                 # Archivos estáticos
├── requirements.txt
└── Procfile / railway.json # Deploy en Railway
```

## 🔒 Seguridad

- CSRF protección activada en todos los formularios
- Rate limiting en login (previene fuerza bruta)
- Contraseñas hasheadas con Werkzeug
- Validación de horarios de acceso por usuario
- Roles con permisos granulares

## 🌐 Deploy en Railway

1. Subí el proyecto a GitHub
2. En [Railway](https://railway.app) → New Project → Deploy from GitHub
3. Agregá PostgreSQL (+ New → Database → PostgreSQL)
4. Configurá variables de entorno:
   - `SECRET_KEY` → generar con `python -c "import secrets; print(secrets.token_hex(32))"`
5. Railway genera dominio automáticamente

## 📄 Licencia

Uso comercial. Prohibida la redistribución sin autorización.
