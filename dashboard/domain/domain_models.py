# domain/domain_models.py
"""
Define entidades (dataclasses) que representan el dominio de la aplicación.
"""
from dataclasses import dataclass, field
from typing import Optional, List
import random

# Lista de esquemas de colores disponibles
AVAILABLE_COLOR_SCHEMES = [
    "Viridis",
    "Cividis",
    "Plasma",
    "Inferno",
    "Magma",
    "Turbo",
    "Rainbow",
    "Portland",
    "Blackbody",
    "Electric",
    "Earth",
    "Bluered",
    "Blues",
    "Greens",
    "Greys",
    "Hot",
    "RdBu",
    "Reds",
    "Temps",
    "Teal"
]


@dataclass
class MapVisualizationConfig:
    titulo: str
    columna_metrica: str
    hover_columns: List[str]  # Lista de columnas para mostrar en el tooltip
    esquema_color: str 
    nombre_hover: str = None   # Nombre para el hover principal
    titulo_colorbar: str = "#000000"
    zoom: int = 13
    latitud_centro: float = 19.332608
    longitud_centro: float = -99.143209
    mapbox_style: str = "open-street-map"  # Estilo por defecto
            

@dataclass
class DashboardFilters:
    """
    Representa los filtros usados en el dashboard:
    - anio: Año específico
    - granularidad: "colonia", "ageb", etc.
    - metrica: Nombre de la columna a graficar
    """
    type_data: str
    anio: Optional[int] = None
    granularidad: str = "colonia"
    metrica: Optional[str] = None
    tooltip_cols: List = field(init = False)

    def __post_init__(self):
        if self.type_data == "demograficos":
            self.tooltip_cols = [
                "ageb",
                "alc",
                "amb_loc",
                "area_km2"
            ]
        elif self.type_data == "edafologicos":
            self.tooltip_cols = [
                "alcaldi",
                "colonia",
                "us dscr",
                "calle"
            ]