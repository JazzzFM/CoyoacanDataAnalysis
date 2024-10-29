# app/__init__.py
from flask import Flask, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from dotenv import load_dotenv
import os
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno desde .env
load_dotenv()

# Inicializar extensiones
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

# Configurar el Login Manager
login_manager.login_view = 'main.login'
login_manager.login_message_category = 'info'

# Agregar un manejador personalizado para redirección en caso de no estar autorizado
@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect(url_for(login_manager.login_view, next=request.path))

def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object('config.default.Config')  # Asegurado que apunta a la clase Config

    # Si hay configuraciones adicionales pasadas como argumento, actualízalas
    if config:
        app.config.update(config)

    # Inicializar extensiones con la aplicación
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Configurar el Login Manager
    login_manager.login_view = 'main.login'
    login_manager.login_message_category = 'info'

    # Registrar blueprints dentro de la función para evitar importación circular
    from .routes import main_bp
    app.register_blueprint(main_bp)

    # Registrar el dashboard
    from .dashboard import init_dashboard
    init_dashboard(app)

    # Definir el user_loader
    from .models import User  # Mover la importación aquí para evitar importación circular
    @login_manager.user_loader
    def load_user(user_id):
        logger.info(f"Cargando usuario con ID: {user_id}")
        return User.query.get(int(user_id))

    # Registrar comandos personalizados
    from .commands import register_commands
    register_commands(app)

    return app

