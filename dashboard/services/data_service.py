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

    def initialize_dataset(self, table: Dict) -> None:
        """
        Carga todos los datasets y los guarda en memoria.
        :raises RuntimeError: Si falla la carga desde la DB.
        """
        logger.info("Inicializando carga de datasets en DataService...")
        try:
            self.data = self.loader.load_dataset(
                    table_name = table.get("table_name"),
                    geom_column = table.get("geom_column")
            )

            return self.data
            #logger.info(f"Datasets disponibles: {list(self.datasets.keys())}")
        except RuntimeError as ex:
            logger.error("No se pudieron inicializar los datasets.")
            raise

    def obtener_anios_disponibles(self, gdf: GeoDataFrame) -> List[int]:
        """
        Retorna la lista de años disponibles en un dataset dado,
        asumiendo que existe la columna 'anio'.

        :param dataset_key: "demograficos", "edafologicos", etc.
        :return: Lista de años encontrados (ordenada).
        """
        if gdf is None or gdf.empty or "anio" not in gdf.columns:
            return []
        return sorted(gdf["anio"].unique())

    def obtener_datos_filtrados(self, dataset_key: str, 
                                gdf: GeoDataFrame,
                                filters: DashboardFilters) -> GeoDataFrame:
        """
        Dado un dataset (p. ej. "demograficos") y un set de filtros,
        retorna un GeoDataFrame filtrado.

        :param dataset_key: Clave para self.datasets
        :param filters: Filtros de dominio (anio, granularidad, metrica)
        :return: El GDF filtrado
        """
        ### Aquii estamos 
        #gdf =  self.datasets.get(dataset_key)

        if gdf is None or gdf.empty:
            logger.warning(f"Dataset '{dataset_key}' vacío o inexistente.")
            return gpd.GeoDataFrame()


        print(f"ANTES gdf filtrado por anio: filters.anio == {filters.anio}")
        print(gdf)
        # 1. Filtrar por año
        #gdf = GeoDataProcessor\
        #    .filtrar_por_anio(gdf, filters.anio)
        
        print(f"gdf filtrado por anio: filters.anio == {filters.anio}")
        print(gdf)

        # 2. Seleccionar columnas/métricas
        metricas = [filters.metrica] if filters.metrica else []
        columnas_fijas = metricas + filters.tooltip_cols
        print(f"filters.tooltip_cols: {filters.tooltip_cols}")

        # 2. Agrupar por granularidad si hay una columna que la maneje
        
        if filters.granularidad == "ageb":
            agrupa = columnas_fijas + metricas
            agrupa += ["ID_AGEB", "GEOM_AGEB"]
            gdf = gdf.groupby(list(set(agrupa)))\
                .first().reset_index()
            gdf = gdf[list(set(agrupa))]
            gdf = gdf.set_geometry("GEOM_AGEB")

        elif filters.granularidad == "colonia":
            if filters.type_data == "demofraficos":
                agrupa = columnas_fijas + metricas
                agrupa += ["ID_COLONIA", "GEOM_COLONIA"]
                gdf = gdf.groupby(list(set(agrupa)))\
                    .first().reset_index()
                gdf = gdf[list(set(agrupa))]
                gdf = gdf.set_geometry("GEOM_COLONIA")

            elif filters.type_data == "edafologicos":
                agrupa = columnas_fijas + metricas
                agrupa += ["ID_COLONIA", "GEOM_COLONIA"]
                print("inicia ------ Dentro del agrupamiento ------")
                print(gdf.columns)
                gdf_ = gdf.groupby(['ID_COLONIA',
                                    'USO_SUELO',
                                    'SUPERFICIE',
                                    'DNSDD_D', 
                                    'NIVELES', 
                                    'ALTURA'])\
                        .size()\
                        .reset_index(name='counts')\
                        .sort_values('counts', ascending=False)\
                        .drop_duplicates('ID_COLONIA')
                print(gdf_.columns)
                print(gdf_)

                print("finaliza ------ Dentro del agrupamiento ------")

                gdf = gdf[['ID_COLONIA', 'GEOM_COLONIA']].merge(
                        gdf_,
                        on = ['ID_COLONIA'],
                        how = 'left'
                    )
                #gdf = gdf[list(set(agrupa))]
                gdf = gdf.set_geometry("GEOM_COLONIA")\
                    .dropna(subset=['USO_SUELO'])

                print("############## FINAL GDF")
                print(gdf)
        else:
            # Aqui no hay agrupaciones?
            agrupa = columnas_fijas + metricas
            agrupa += ["ID_MANZANA", "GEOM_MANZANA"]
            gdf = gdf[(list(set(agrupa)))]
            gdf = gdf.set_geometry("GEOM_MANZANA")

        print(f"Dentro de granularidad inicio ----------- {filters.granularidad} \n\n")
        print(gdf.columns)
        print(gdf)
        print(f"Dentro de granularidad final ----------- {filters.granularidad} \n\n")

        return gdf
