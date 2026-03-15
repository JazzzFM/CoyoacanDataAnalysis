# data_access/data_loader.py

"""
Carga datos geoespaciales en forma de GeoDataFrames desde PostgreSQL,
con caché en disco (parquet) para reducir transferencia de datos desde Neon.
"""

import os
import hashlib
import logging
import geopandas as gpd
from typing import Dict
from .data_connection import DatabaseConnectionManager
from geopandas import GeoDataFrame

logger = logging.getLogger(__name__)

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), '.cache_geodata')


class PostgresGeoDataLoader:
    """
    SRP: Encargado de cargar datos de PostgreSQL usando GeoPandas.
    Usa caché en disco (parquet) para evitar re-descargar datos pesados
    en cada restart del servidor.
    """

    def __init__(self, connection_manager: DatabaseConnectionManager) -> None:
        self.connection_manager: DatabaseConnectionManager = connection_manager
        os.makedirs(CACHE_DIR, exist_ok=True)

    def _cache_path(self, table_name: str) -> str:
        return os.path.join(CACHE_DIR, f"{table_name}.parquet")

    def load_dataset(self, table_name: str, geom_column: str) -> GeoDataFrame:
        """
        Carga un dataset desde caché local (parquet) si existe,
        o desde PostgreSQL si no. Guarda en caché tras la primera carga.
        """
        cache_file = self._cache_path(table_name)

        # Intentar cargar desde caché
        if os.path.exists(cache_file):
            try:
                data = gpd.read_parquet(cache_file)
                logger.info(f"Dataset desde caché: {table_name} ({len(data)} registros)")
                return data
            except Exception as e:
                logger.warning(f"Caché corrupta para {table_name}, recargando: {e}")

        # Cargar desde PostgreSQL
        try:
            logger.info("Cargando datasets geoespaciales desde PostgreSQL...")
            engine = self.connection_manager.get_engine()
            data = gpd.read_postgis(
                f"SELECT * FROM {table_name}",
                con=engine,
                geom_col=f"{geom_column}")
            logger.info(f"Dataset cargado: {table_name} ({len(data)} registros)")

            # Guardar en caché
            try:
                data.to_parquet(cache_file)
                logger.info(f"  Caché guardada: {cache_file}")
            except Exception as e:
                logger.warning(f"  No se pudo guardar caché: {e}")

            return data

        except Exception as ex:
            logger.error(f"Error al cargar los datasets: {ex}")
            raise RuntimeError("No se pudieron cargar los GeoDataFrames desde la DB.") from ex

    def invalidate_cache(self, table_name: str = None):
        """Elimina caché de una tabla o de todas."""
        if table_name:
            cache_file = self._cache_path(table_name)
            if os.path.exists(cache_file):
                os.remove(cache_file)
                logger.info(f"Caché eliminada: {table_name}")
        else:
            import glob
            for f in glob.glob(os.path.join(CACHE_DIR, "*.parquet")):
                os.remove(f)
            logger.info("Toda la caché eliminada")
