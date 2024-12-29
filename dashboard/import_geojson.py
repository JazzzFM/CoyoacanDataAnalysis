from dataclasses import dataclass
from typing import Optional, Dict, Any
import pandas as pd
import geopandas as gpd
import logging

logger = logging.getLogger(__name__)

@dataclass
class ProcessingConfig:
    """
    Configuración para procesamiento de datos.
    """
    nivel_granularidad: str
    filtro_anio: Optional[int] = None
    columna_metrica: Optional[str] = None

class DataProcessor:
    @staticmethod
    def procesar_datos(
        data: gpd.GeoDataFrame,
        config: ProcessingConfig
    ) -> Optional[gpd.GeoDataFrame]:
        """
        Procesa los datos basándose en configuración específica.
        """
        try:
            # Filtrar por año si se especifica
            if config.filtro_anio:
                data = data[data["anio"] == config.filtro_anio]
                logger.info(f"Datos filtrados para el año {config.filtro_anio}: {len(data)} registros.")

            # Selección de columna métrica si se especifica
            if config.columna_metrica and config.columna_metrica in data.columns:
                data = data[["geometry", config.columna_metrica]].copy()
                logger.info(f"Seleccionando columna métrica: {config.columna_metrica}.")
            else:
                logger.warning(f"La columna métrica '{config.columna_metrica}' no está presente.")

            return data
        except Exception as e:
            logger.error(f"Error al procesar datos: {e}")
            return None

    @staticmethod
    def agregar_metrica_personalizada(
        data: gpd.GeoDataFrame, columna_base: str, nueva_columna: str, funcion: Any
    ) -> gpd.GeoDataFrame:
        """
        Agrega una métrica personalizada calculada con una función proporcionada.
        """
        try:
            if columna_base in data.columns:
                data[nueva_columna] = data[columna_base].apply(funcion)
                logger.info(f"Nueva columna '{nueva_columna}' agregada con base en '{columna_base}'.")
            else:
                logger.warning(f"La columna base '{columna_base}' no está disponible.")
            return data
        except Exception as e:
            logger.error(f"Error al agregar métrica personalizada: {e}")
            return data
