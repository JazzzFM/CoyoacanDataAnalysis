# utils/figures_utils.py

"""
Genera visualizaciones (e.g. mapas coropléticos) con Plotly.
"""

import geopandas as gpd
from geopandas import GeoDataFrame
import plotly.express as px
from typing import Any, Optional
from domain.domain_models import MapVisualizationConfig
import dash_leaflet as dl
import json


class FiguresGenerator:
    """
    Clase con métodos estáticos para crear figuras usando Plotly.
    """
    
    @staticmethod
    def generar_mapa_coropletico(
        data: GeoDataFrame, 
        config: MapVisualizationConfig
    ) -> Optional[Any]:
        """
        Genera un mapa coroplético con Plotly Express, o None si data está vacío.
        
        :param data: GeoDataFrame con geometry y la columna métrica
        :param config: Parámetros de configuración de la visualización
        :return: Un objeto Figure de Plotly, o None si data está vacío.
        """
        if data.empty:
            return None

        # -------------------------------------------
        # Preparar las columnas para el tooltip
        # -------------------------------------------
        custom_data_cols = [col for col in config.hover_columns\
                             if col in data.columns and \
                                col != config.columna_metrica]

        # Crear el mapa coroplético con Plotly Express
        fig = px.choropleth_mapbox(
            data_frame = data,
            geojson = data.__geo_interface__,     # GeoJSON directamente desde la geometría
            locations = data.index,               # Usa los índices como identificadores
            color = config.columna_metrica,       # Columna principal que define el color
            mapbox_style = config.mapbox_style,   # Estilo de Mapbox
            zoom = config.zoom,
            center = {"lat": config.latitud_centro, 
                    "lon": config.longitud_centro},
            color_continuous_scale=config.esquema_color,
            opacity=0.7,
            hover_name=(
                config.nombre_hover 
                if config.nombre_hover 
                else config.columna_metrica
            ),
            custom_data = custom_data_cols        # Para construir un hover_template más detallado
        )

        # -------------------------------------------
        # Construir un hover_template "a la medida"
        # -------------------------------------------
        # Se aprovecha %{z} para mostrar el valor de la métrica principal
        # (la que define el color).
        # 
        #  
        hover_template = (
            f"• <b>{config.columna_metrica}:</b> %{{z}}<br>"
        )
        for i, col in enumerate(custom_data_cols):
            hover_template += f"• <b>{col}:</b> %{{customdata[{i}]}}<br>"
        hover_template += "<extra></extra>"

        # Se aplica el hover_template a la traza
        fig.update_traces(
            hovertemplate=hover_template,
            marker_line_color='white',  # Borde fino en blanco para delimitar polígonos
            marker_line_width=0.5
        )

        # Ajustes finales de diseño
        fig.update_layout(
            template='plotly_white',  
            title={
                'text': config.titulo,
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            margin={"r": 0, "t": 60, "l": 0, "b": 0},
            hoverlabel=dict(
                bgcolor="white",
                font_size=12,
                font_family="Arial"
            ),
            coloraxis_colorbar=dict(
                title=(
                    config.titulo_colorbar 
                    if config.titulo_colorbar 
                    else config.columna_metrica
                ),
                titleside='right',
                ticks='outside',
                lenmode='fraction',
                len=0.75,
                y=0.5
            )
        )

        return fig
