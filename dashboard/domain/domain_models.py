# domain/domain_models.py

"""
Define entidades (dataclasses) que representan el dominio de la aplicación.
"""

from dataclasses import dataclass
from typing import Optional, List

@dataclass
class MapVisualizationConfig:
    titulo: str
    columna_metrica: str
    esquema_color: str
    #hover_columns: List[str]  # Lista de columnas para mostrar en el tooltip
    #nombre_hover: str = None   # Nombre para el hover principal
    titulo_colorbar: str = None
    zoom: int = 13
    latitud_centro: float = 19.35
    longitud_centro: float = -99.16
    mapbox_style: str = "carto-positron"  # Estilo por defecto

@dataclass
class DashboardFilters:
    """
    Representa los filtros usados en el dashboard:
    - anio: Año específico
    - granularidad: "colonia", "ageb", etc.
    - metrica: Nombre de la columna a graficar
    """
    anio: Optional[int] = None
    granularidad: str = "colonia"
    metrica: Optional[str] = None

# Agrega más dataclasses si hay otras entidades
# Por ejemplo, si necesitas representar "Usuario", "EntidadCatastral", etc.
