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

from app.data_access.data_loader import PostgresGeoDataLoader
from app.data_access.data_processor import GeoDataProcessor
from app.domain.domain_models import DashboardFilters

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

    def initialize_dataset(self, table: Dict) -> None:
        """
        Carga todos los datasets y los guarda en memoria.
        :raises RuntimeError: Si falla la carga desde la DB.
        """
        try:
            self.data = self.loader.load_dataset(
                    table_name = table.get("table_name"),
                    geom_column = table.get("geom_column")
            )
            return self.data
        except RuntimeError as ex:
            logger.error("No se pudieron inicializar los datasets.")
            raise

    def obtener_anios_disponibles(self, gdf: GeoDataFrame) -> List[int]:
        """
        Retorna la lista de años disponibles en un dataset dado,
        asumiendo que existe la columna 'anio'.
        """
        if gdf is None or gdf.empty or "anio" not in gdf.columns:
            return []
        return sorted(gdf["anio"].unique())

    def obtener_datos_filtrados(self, dataset_key: str,
                                gdf: GeoDataFrame,
                                filters: DashboardFilters) -> GeoDataFrame:
        """
        Dado un dataset y un set de filtros, retorna un GeoDataFrame filtrado.
        """
        if gdf is None or gdf.empty:
            logger.warning(f"Dataset '{dataset_key}' vacío o inexistente.")
            return gpd.GeoDataFrame()

        metricas = [filters.metrica] if filters.metrica else []
        # Filtrar tooltip_cols a columnas que realmente existen en el dataset
        tooltip_validos = [c for c in filters.tooltip_cols if c in gdf.columns]
        columnas_fijas = metricas + tooltip_validos

        # Helper: filtrar lista de columnas a solo las existentes en gdf
        def _cols_existentes(cols):
            return [c for c in cols if c in gdf.columns]

        # Detectar columna de geometría activa (buscar entre candidatas)
        geom_col = None
        try:
            if hasattr(gdf, 'geometry') and gdf.geometry is not None:
                geom_col = gdf.geometry.name
        except Exception:
            pass
        if geom_col is None or geom_col not in gdf.columns:
            for candidate in ['GEOM_MANZANA', 'GEOM_AGEB', 'GEOM_COLONIA', 'geometry']:
                if candidate in gdf.columns:
                    geom_col = candidate
                    break
            else:
                geom_col = gdf.columns[-1]  # fallback

        if filters.granularidad == "ageb":
            agrupa = _cols_existentes(columnas_fijas + metricas + ["ID_AGEB", geom_col])
            gdf = gdf.groupby(list(set(agrupa)))\
                .first().reset_index()
            gdf = gdf[list(set(agrupa))]
            gdf = gdf.set_geometry(geom_col)

        elif filters.granularidad == "colonia":
            if filters.type_data == "demograficos":
                agrupa = _cols_existentes(columnas_fijas + metricas + ["ID_COLONIA", geom_col])
                gdf = gdf.groupby(list(set(agrupa)))\
                    .first().reset_index()
                gdf = gdf[list(set(agrupa))]
                gdf = gdf.set_geometry(geom_col)

            elif filters.type_data == "edafologicos":
                group_cols = _cols_existentes(['ID_COLONIA', 'USO_SUELO',
                                               'SUPERFICIE', 'DNSDD_D',
                                               'NIVELES', 'ALTURA'])
                gdf_ = gdf.groupby(group_cols)\
                        .size()\
                        .reset_index(name='counts')\
                        .sort_values('counts', ascending=False)\
                        .drop_duplicates('ID_COLONIA')

                geom_cols_avail = [c for c in ['GEOM_COLONIA', geom_col] if c in gdf.columns]
                merge_cols = ['ID_COLONIA'] + geom_cols_avail[:1]
                gdf = gdf[merge_cols].merge(
                        gdf_,
                        on=['ID_COLONIA'],
                        how='left'
                    )
                gdf = gdf.set_geometry(geom_cols_avail[0] if geom_cols_avail else geom_col)\
                    .dropna(subset=['USO_SUELO'])
        else:
            agrupa = _cols_existentes(columnas_fijas + metricas + ["ID_MANZANA", geom_col])
            gdf = gdf[list(set(agrupa))]
            gdf = gdf.set_geometry(geom_col)

        return gdf
