from sqlalchemy import create_engine
from typing import Dict
import geopandas as gpd
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    database: str = "Poligonos"
    user: str = "developer"
    password: str = "MelonSK998"

class DataLoader:
    def __init__(self, config: DatabaseConfig):
        self.config = config

    def load_static_data(self) -> Dict[str, gpd.GeoDataFrame]:
        """
        Carga los datos geoespaciales de las tablas necesarias.
        """
        try:
            # Aquí puedes usar una conexión con SQLAlchemy o psycopg2 para cargar datos de PostgreSQL
            logger.info("Conectando a la base de datos para cargar datos...")
            # Ejemplo con geopandas para cargar tablas como GeoDataFrames
            datos = {
                "demograficos": gpd.read_postgis("SELECT * FROM datos_demograficos",
                                                        con = self.get_connection(), 
                                                        geom_col = "geometry"),
                "edafologia": gpd.read_postgis("SELECT * FROM uso_suelo", 
                                            con = self.get_connection(), 
                                            geom_col = "geometry"),
                # Agrega más tablas si es necesario
            }
            logger.info("Datos cargados exitosamente.")
            return datos
        except Exception as e:
            logger.error(f"Error al cargar los datos: {e}")
            raise e

    def get_connection(self):
        """
        Crea una conexión a la base de datos PostgreSQL.
        """
        engine = create_engine(
            f"postgresql://{self.config.user}:" +\
            f"{self.config.password}@{self.config.host}:" +\
            f"{self.config.port}/{self.config.database}"
        )
        return engine
