# app/dashboard.py
"""
Integra el dashboard completo de Dash dentro del servidor Flask.
Usa la arquitectura en capas de data_access/, domain/, services/,
presentation/ y figures/.
"""
import os
import logging
import dash
import dash_bootstrap_components as dbc

from app.data_access.data_connection import DatabaseConnectionManager
from app.data_access.data_loader import PostgresGeoDataLoader
from app.domain.domain_models import TableController
from app.services.data_service import DataService
from app.presentation.layout_builder import LayoutBuilder
from app.presentation.callback_register import CallbackRegister

logger = logging.getLogger(__name__)


def init_dashboard(server):
    """
    Crea la app Dash embebida en el servidor Flask.
    Usa DATABASE_URI del entorno para conectarse a Neon PostGIS.
    """
    database_uri = os.getenv("DATABASE_URI")
    if not database_uri:
        logger.warning("DATABASE_URI no configurada, dashboard sin datos")
        return None

    # 1. Conexion a la base de datos
    connection_manager = DatabaseConnectionManager(database_uri=database_uri)

    # 2. Loader y servicio de datos
    loader = PostgresGeoDataLoader(connection_manager)
    data_service = DataService(loader)
    table_controller = TableController()

    # 3. Layout y callbacks
    layout_builder = LayoutBuilder()
    callback_register = CallbackRegister(table_controller, data_service, layout_builder)

    # 4. Crear app Dash embebida en Flask
    dash_app = dash.Dash(
        __name__,
        server=server,
        url_base_pathname='/dashboard/',
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        suppress_callback_exceptions=True
    )

    dash_app.layout = layout_builder.create_layout()
    callback_register.register_callbacks(dash_app)

    logger.info("Dashboard Dash integrado en Flask exitosamente")
    return dash_app
