# data_access/data_loader.py

"""
Carga datos geoespaciales en forma de GeoDataFrames desde PostgreSQL,
usando la conexión proveída por DatabaseConnectionManager.
"""

import logging
import geopandas as gpd
from typing import Dict
from .data_connection import DatabaseConnectionManager
from geopandas import GeoDataFrame

logger = logging.getLogger(__name__)

class PostgresGeoDataLoader:
    """
    SRP: Encargado de cargar datos de PostgreSQL usando GeoPandas.
    No filtra ni aplica lógica de negocio, solo se limita a consultas básicas.
    """

    def __init__(self, connection_manager: DatabaseConnectionManager) -> None:
        """
        :param connection_manager: Proveedor de Engines para conectarse a la DB.
        """
        self.connection_manager: DatabaseConnectionManager = connection_manager

    def load_dataset(self, table_name: str, geom_column: str) -> Dict[str, GeoDataFrame]:
        """
        Carga múltiples tablas de la base de datos y las
        devuelve en un diccionario {nombre_tabla: GeoDataFrame}.

        :return: Diccionario con datasets
        :raises RuntimeError: Si no se pudo leer alguna tabla.
        """
        try:
            logger.info("Cargando datasets geoespaciales desde PostgreSQL...")
            engine = self.connection_manager.get_engine()

            # Sugerencia de filtrado en SQL para eficiencia:
            # Ejemplo: "SELECT * FROM datos_demograficos WHERE anio >= 2010"
            # Esto podría hacerse condicional según tus necesidades.

            # Ajusta las queries a tus tablas reales
            data = gpd.read_postgis(
                f"SELECT * FROM {table_name}",
                con = engine,
                geom_col = f"{geom_column}")

            logger.info(f"data: {data.__dict__}")
            print(data)
            logger.info(f"data.columns: {data.columns}")

            logger.info("Dataset cargados exitosamente.")
            return data

        except Exception as ex:
            logger.error(f"Error al cargar los datasets: {ex}")
            raise RuntimeError("No se pudieron cargar los GeoDataFrames desde la DB.") from ex
