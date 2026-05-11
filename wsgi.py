"""
Kairos Stock — Entry point.
Toda la lógica vive en el paquete app/.
Este archivo solo crea la app y la expone para Gunicorn.
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
