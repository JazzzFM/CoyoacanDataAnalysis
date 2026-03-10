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
class TableController:
    poligonos: object = field(init = False)
    demograficos: object = field(init = False)
    edafologicos: object = field(init = False)
    electorales: object = field(init = False)
    servicios: object = field(init = False)
    ambientales: object = field(init = False)

    def __post_init__(self):
        self.poligonos_manzana = {
            "table_name": "poligonos_manzanas_agebs_colonias",
            "geom_column": "GEOM_MANZANA"
        }

        self.poligonos_ageb = {
            "table_name": "poligonos_manzanas_agebs_colonias",
            "geom_column": "GEOM_AGEB"
        }

        self.poligonos_colonia = {
            "table_name": "poligonos_manzanas_agebs_colonias",
            "geom_column": "GEOM_COLONIA"
        }

        self.demograficos = {
            "table_name": "datos_demograficos_particionada",
            "geom_column": "geometry"
        }

        self.edafologicos = {
            "table_name": "datos_edafologicos_particionada",
            "geom_column": "GEOM_MANZANA"
        }

        self.servicios = {
            "table_name": "datos_servicios",
            "geom_column": "geometry"
        }

        self.electorales = {
            "table_name": "datos_electorales",
            "geom_column": "geometry"
        }

        self.ambientales = {
            "table_name": "datos_indicadores_colonia",
            "geom_column": "geometry"
        }

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
    granularidad: str = "manzana"
    metrica: Optional[str] = None
    tooltip_cols: List = field(init = False)

    def __post_init__(self):
        if self.type_data == "demograficos":
            self.tooltip_cols = [
                "ID_AGEB",
                "NOMBRE_COLONIA",
                "alc",
                "amb_loc",
                "area_km2"
            ]
        elif self.type_data == "edafologicos":
            self.tooltip_cols = [
                'ID_AGEB',
                "NOMBRE_COLONIA",
                'USO_SUELO',
                'DNSDD_D',
                'NIVELES',
                'ALTURA'
            ]
        elif self.type_data == "servicios":
            self.tooltip_cols = [
                'nombre',
                'categoria',
                'subcategoria',
                'personal_ocupado'
            ]
        elif self.type_data == "electorales":
            self.tooltip_cols = [
                'seccion',
                'distrito_federal',
                'distrito_local',
                'alc_ganador',
                'alc_participacion',
                'alc_votos_totales',
                'fed_ganador',
                'fed_participacion',
                'area_km2'
            ]
        elif self.type_data == "ambientales":
            self.tooltip_cols = [
                'colonia',
                'densidad_viv_ha',
                'm2_area_verde_hab',
                'm2_espacio_pub_hab',
                'pct_viviendas_desocupadas',
                'incremento_abs_poblacion',
                'cat_urbanismo_social',
            ]
        else:
            self.tooltip_cols = []