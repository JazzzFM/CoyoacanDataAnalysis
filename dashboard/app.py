# app.py

import logging
from data_access.data_connection import DatabaseCredentials, DatabaseConnectionManager
from data_access.data_loader import PostgresGeoDataLoader
from services.data_service import DataService
from presentation.controller import DashAppController

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(levelname)s] %(asctime)s - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def main() -> None:
    # 1. Preparar credenciales
    credentials = DatabaseCredentials(
        host="localhost",
        port=5432,
        database="Poligonos",
        user="developer",
        password="MelonSK998"
    )
    connection_manager = DatabaseConnectionManager(credentials)

    # 2. Instanciar loader y data service
    loader = PostgresGeoDataLoader(connection_manager)
    data_service = DataService(loader)

    # 3. Cargar datasets
    data_service.initialize_datasets()

    # 4. Crear la clase controladora de la app Dash
    dash_controller = DashAppController(data_service)

    # 5. Iniciar servidor
    dash_controller.run(debug=True)

if __name__ == "__main__":
    main()
