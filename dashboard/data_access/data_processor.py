# data_access/data_processor.py

"""
Encapsula la lógica de filtrado y selección de columnas.
"""

import geopandas as gpd
from geopandas import GeoDataFrame
from typing import Optional, List

class GeoDataProcessor:
    """
    Contiene métodos estáticos para filtrar y procesar GeoDataFrames.
    """

    @staticmethod
    def filtrar_por_anio(gdf: GeoDataFrame, anio: Optional[int]) -> GeoDataFrame:
        """
        Filtra un GeoDataFrame por el valor de 'anio', si corresponde.
        :param gdf: El GeoDataFrame de entrada.
        :param anio: Año a filtrar (None = sin filtrar).
        :return: Un GDF filtrado por 'anio'.
        """
        if anio is not None and "anio" in gdf.columns:
            return gdf[gdf["anio"] == anio].copy()
        return gdf

    @staticmethod
    def seleccionar_metricas(gdf: GeoDataFrame, 
                            metricas: List[str],
                            tooltip_cols: str) -> GeoDataFrame:
        """
        Selecciona solo las columnas indicadas en 'metricas' (si existen) más la geometría.
        :param gdf: El GeoDataFrame de entrada.
        :param metricas: Lista de nombres de columnas que interesan.
        :return: Un GDF con las columnas seleccionadas.
        """
        if not metricas:
            return gdf

        columnas_validas = [col for col in metricas \
                            if col in gdf.columns]
                
        if "geometry" not in columnas_validas and\
            "geometry" in gdf.columns:
            columnas_validas.append("geometry")
        
        columnas_validas += tooltip_cols

        return gdf[columnas_validas].copy()

