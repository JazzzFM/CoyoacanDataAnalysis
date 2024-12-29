# utils/figures_utils.py

"""
Genera visualizaciones (e.g. mapas coropléticos) con Plotly.
"""

import geopandas as gpd
from geopandas import GeoDataFrame
import plotly.express as px
from typing import Any, Optional, List
from domain.domain_models import MapVisualizationConfig
import dash_leaflet as dl
import json


class FiguresGenerator:
    """
    Clase con métodos estáticos para crear figuras usando Plotly.
    """
    
    @staticmethod
    def generar_mapa_coropletico(data: GeoDataFrame, config: MapVisualizationConfig) -> Optional[Any]:
        """
        Genera un mapa coroplético con Plotly Express, o None si data está vacío.
        
        :param data: GeoDataFrame con geometry y la columna métrica
        :param config: Parámetros de configuración de la visualización
        :return: Un objeto Figure de Plotly, o None si data está vacío.
        """
        if data.empty:
            return None

        # Verificar que las columnas de hover existen en los datos
        #for col in config.hover_columns:
        #   if col not in data.columns:
        #       raise ValueError(f"La columna de hover '{col}' no existe en los datos.")

        # Crear el mapa coroplético
        fig = px.choropleth_mapbox(
            data_frame=data,
            geojson=data.__geo_interface__,
            locations=data.index,
            color=config.columna_metrica,
            mapbox_style=config.mapbox_style,  # Usar el estilo configurado
            zoom=config.zoom,
            center = {"lat": config.latitud_centro, "lon": config.longitud_centro},
            color_continuous_scale=config.esquema_color,
            opacity = 0.7,  # Ajustar la opacidad para mejor visibilidad
            #hover_name = config.nombre_hover if config.nombre_hover else config.columna_metrica,
            #hover_data = {col: True for col in config.hover_columns}  # Mostrar columnas adicionales en el hover
        )

        # Actualizar el layout para mejorar el aspecto
        fig.update_layout(
            title={
                'text': config.titulo,
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            margin={"r":0,"t":50,"l":0,"b":0},
            coloraxis_colorbar=dict(
                title=config.titulo_colorbar if config.titulo_colorbar else config.columna_metrica,
                titleside='right',
                ticks='outside',
                lenmode='fraction',
                len=0.75,
                y=0.5
            )
        )

        # Personalizar los tooltips con formato
        #fig.update_traces(
        #   hovertemplate=FiguresGenerator._crear_hovertemplate(config.hover_columns, config.nombre_hover)
        #)

        return fig

    @staticmethod
    def _crear_hovertemplate(hover_columns: List[str], nombre_hover: Optional[str]) -> str:
        """
        Crea un hovertemplate personalizado.

        :param hover_columns: Lista de columnas a mostrar en el tooltip
        :param nombre_hover: Nombre principal a mostrar
        :return: String con el hovertemplate
        """
        template = ""
        if nombre_hover:
            template += f"<b>%{{customdata[0]}}</b><br>"
            hover_data = hover_columns[1:]
        else:
            hover_data = hover_columns

        for i, col in enumerate(hover_data, start=1 if nombre_hover else 0):
            template += f"{col}: %{{customdata[{i}]}}<br>"

        template += "<extra></extra>"  # Remover información adicional por defecto
        return template
    

class LeafletMapGenerator:
    """
    Clase que genera mapas basados en dash-leaflet en lugar de Plotly.
    """

    @staticmethod
    def generar_mapa_leaflet(data: GeoDataFrame, config: MapVisualizationConfig) -> Optional[dl.Map]:
        """
        Genera un mapa Leaflet con dash-leaflet, coloreando polígonos (coroplético).
        
        :param data: GeoDataFrame con geometrías y la columna métrica.
        :param config: Configuración de la visualización (columna de métrica, título, etc.)
        :return: Un dl.Map con TileLayer + capas geoespaciales, o None si data está vacío.
        """
        if data.empty or config.columna_metrica not in data.columns:
            return None

        # Convertir el GeoDataFrame a GeoJSON
        # dash-leaflet trabaja directamente con geojson para pintar polígonos.
        geojson_data = json.loads(data.to_json())

        # O podemos aplicar una escala de colores en Python, según la métrica.
        # Por ejemplo, asignar una escala con base en min-max.
        valores = data[config.columna_metrica]
        vmin, vmax = valores.min(), valores.max()
        rango = vmax - vmin if vmax != vmin else 1

        # En Leaflet, se puede usar "style" a nivel de Feature. 
        # Creamos un diccionario con la propiedad "style" que devuelva color según la métrica.
        def style_function(feature):
            # Cada 'feature' corresponde a un polígono en geojson_data
            # Obtenemos la métrica del feature
            prop_val = feature["properties"].get(config.columna_metrica, 0)
            # Normalizamos y asignamos un color
            intensidad = (prop_val - vmin) / rango
            # Por ejemplo, un degrade de azul a rojo
            r = int(intensidad * 255)
            g = 0
            b = int((1 - intensidad) * 255)
            fill_color = f"rgb({r},{g},{b})"

            return {
                "fillColor": fill_color,
                "color": "black",
                "weight": 1,
                "fillOpacity": 0.6,
            }

        # Crear el componente dl.GeoJSON
        geojson_layer = dl.GeoJSON(
            data = geojson_data,
            options=dict(style=style_function),
            id="geojson-layer"
        )

        # Configurar un centro y un zoom apropiado, o calcula bounding box
        center = [19.35, -99.16]  # Ejemplo: CDMX
        zoom = 11

        # Crear un mapa con TileLayer + la capa GeoJSON
        leaflet_map = dl.Map(
            children=[
                dl.TileLayer(),
                geojson_layer
            ],
            center=center,
            zoom=zoom,
            style={"width": "100%", "height": "600px"}
        )

        return leaflet_map

