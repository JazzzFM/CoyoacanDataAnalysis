# services/data_service.py

"""
Define la clase DataService, que combina la carga de datos
y el procesamiento para exponer métodos de alto nivel
a la capa de presentación.
"""

import logging
import geopandas as gpd
from geopandas import GeoDataFrame
from typing import Dict, List

from data_access.data_loader import PostgresGeoDataLoader
from data_access.data_processor import GeoDataProcessor
from domain.domain_models import DashboardFilters

logger = logging.getLogger(__name__)

class DataService:
    """
    Orquesta la carga de datos (con PostgresGeoDataLoader)
    y su posterior filtrado (con GeoDataProcessor).
    Expuesto a la capa de presentación (Dash).
    """

    def __init__(self, loader: PostgresGeoDataLoader) -> None:
        """
        :param loader: Cargador de datos desde PostgreSQL
        """
        self.loader: PostgresGeoDataLoader = loader
        self.datasets: Dict[str, GeoDataFrame] = {}

    def initialize_datasets(self) -> None:
        """
        Carga todos los datasets y los guarda en memoria.
        :raises RuntimeError: Si falla la carga desde la DB.
        """
        logger.info("Inicializando carga de datasets en DataService...")
        try:
            self.datasets = self.loader.load_datasets()
            logger.info(f"Datasets disponibles: {list(self.datasets.keys())}")
        except RuntimeError as ex:
            logger.error("No se pudieron inicializar los datasets.")
            raise

    def obtener_anios_disponibles(self, dataset_key: str) -> List[int]:
        """
        Retorna la lista de años disponibles en un dataset dado,
        asumiendo que existe la columna 'anio'.

        :param dataset_key: "demograficos", "edafologicos", etc.
        :return: Lista de años encontrados (ordenada).
        """
        gdf = self.datasets.get(dataset_key)
        if gdf is None or gdf.empty or "anio" not in gdf.columns:
            return []
        return sorted(gdf["anio"].unique())

    def obtener_datos_filtrados(self, dataset_key: str, filters: DashboardFilters) -> GeoDataFrame:
        """
        Dado un dataset (p. ej. "demograficos") y un set de filtros,
        retorna un GeoDataFrame filtrado.

        :param dataset_key: Clave para self.datasets
        :param filters: Filtros de dominio (anio, granularidad, metrica)
        :return: El GDF filtrado
        """
        gdf = self.datasets.get(dataset_key)
        if gdf is None or gdf.empty:
            logger.warning(f"Dataset '{dataset_key}' vacío o inexistente.")
            return gpd.GeoDataFrame()

        # 1. Filtrar por año
        gdf = GeoDataProcessor.filtrar_por_anio(gdf, filters.anio)

        # 2. (Opcional) Filtrar por granularidad si hay una columna que la maneje
        # if "granularidad" in gdf.columns:
        #     gdf = gdf[gdf["granularidad"] == filters.granularidad]

        # 3. Seleccionar columnas/métricas
        metricas = [filters.metrica] if filters.metrica else []
        gdf = GeoDataProcessor.seleccionar_metricas(gdf, metricas)

        return gdf
