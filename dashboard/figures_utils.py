from dataclasses import dataclass
from typing import Dict, Optional
import geopandas as gpd
import plotly.express as px
import logging

logger = logging.getLogger(__name__)

@dataclass
class MapConfig:
    """
    Configuración para generar mapas coropléticos.
    """
    titulo: str
    columna_metrica: str
    esquema_color: str = "Viridis"

class FiguresUtils:
    @staticmethod
    def generar_mapa_coropletico(
        data: gpd.GeoDataFrame, config: MapConfig
    ) -> Optional[px.choropleth]:
        """
        Genera un mapa coroplético basado en los datos y configuración.
        """
        try:
            if config.columna_metrica not in data.columns:
                logger.error(f"La columna métrica '{config.columna_metrica}' no está en los datos.")
                return None

            fig = px.choropleth(
                data,
                geojson=data.geometry,
                locations=data.index,
                color=config.columna_metrica,
                title=config.titulo,
                color_continuous_scale=config.esquema_color,
            )
            fig.update_geos(fitbounds="locations", visible=False)
            logger.info("Mapa coroplético generado exitosamente.")
            return fig
        except Exception as e:
            logger.error(f"Error al generar mapa coroplético: {e}")
            return None
