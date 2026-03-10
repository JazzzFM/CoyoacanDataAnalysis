# utils/figures_utils.py

"""
Genera visualizaciones (e.g. mapas coropléticos) con Plotly.
"""

import warnings
import geopandas as gpd
from geopandas import GeoDataFrame
import plotly.express as px
import plotly.graph_objects as go
from typing import Any, Optional, List
from app.domain.domain_models import MapVisualizationConfig
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

    @staticmethod
    def generar_mapa_categorico(
        gdf: GeoDataFrame,
        columna_cat: str,
        columna_nombre: str,
        titulo: str,
        categorias_visibles: Optional[List[str]] = None,
    ) -> Optional[go.Figure]:
        """
        Genera un mapa con capas categoricas (puntos, lineas, poligonos).
        Cada categoria se muestra como una traza separada con color distinto.

        :param gdf: GeoDataFrame con geometry y columnas categoricas
        :param columna_cat: Columna para agrupar por categoria (color)
        :param columna_nombre: Columna con el nombre para hover
        :param titulo: Titulo del mapa
        :param categorias_visibles: Lista de categorias a mostrar (None = todas)
        """
        if gdf is None or gdf.empty:
            return None

        if categorias_visibles:
            gdf = gdf[gdf[columna_cat].isin(categorias_visibles)]
            if gdf.empty:
                return None

        COLORES = px.colors.qualitative.Bold
        fig = go.Figure()
        categorias = gdf[columna_cat].unique()
        # Suprimir warnings de centroid en CRS geografico (error despreciable a escala local)
        warnings.filterwarnings('ignore', message='.*geographic CRS.*centroid.*')

        for i, cat in enumerate(categorias):
            subset = gdf[gdf[columna_cat] == cat].copy()
            color = COLORES[i % len(COLORES)]
            nombre_display = cat.replace('_', ' ').title()
            first_in_group = True
            geom_types = subset.geometry.geom_type

            # Puntos
            mask_pts = geom_types.isin(['Point', 'MultiPoint'])
            if mask_pts.any():
                pts = subset[mask_pts]
                centroids = pts.geometry.centroid
                fig.add_trace(go.Scattermapbox(
                    lat=centroids.y, lon=centroids.x,
                    mode='markers',
                    marker=dict(size=9, color=color),
                    name=nombre_display,
                    text=pts[columna_nombre].fillna(cat),
                    hovertemplate='%{text}<extra>' + nombre_display + '</extra>',
                    legendgroup=cat,
                    showlegend=first_in_group,
                ))
                first_in_group = False

            # Lineas
            mask_lines = geom_types.isin(['LineString', 'MultiLineString'])
            if mask_lines.any():
                lats, lons = [], []
                for geom in subset[mask_lines].geometry:
                    lines = geom.geoms if hasattr(geom, 'geoms') else [geom]
                    for line in lines:
                        coords = list(line.coords)
                        lats.extend([c[1] for c in coords] + [None])
                        lons.extend([c[0] for c in coords] + [None])
                fig.add_trace(go.Scattermapbox(
                    lat=lats, lon=lons,
                    mode='lines',
                    line=dict(width=3, color=color),
                    name=nombre_display,
                    hovertemplate=nombre_display + '<extra></extra>',
                    legendgroup=cat,
                    showlegend=first_in_group,
                ))
                first_in_group = False

            # Poligonos (centroides con tamano proporcional al area)
            mask_poly = geom_types.isin(['Polygon', 'MultiPolygon'])
            if mask_poly.any():
                polys = subset[mask_poly].copy()
                centroids = polys.geometry.centroid
                # Calcular area en m2 para escalar marcadores
                polys_utm = polys.to_crs("EPSG:32614")
                areas = polys_utm.geometry.area
                # Escalar: min 4px, max 15px
                if areas.max() > areas.min():
                    sizes = 4 + 11 * (areas - areas.min()) / (areas.max() - areas.min())
                else:
                    sizes = 7
                fig.add_trace(go.Scattermapbox(
                    lat=centroids.y, lon=centroids.x,
                    mode='markers',
                    marker=dict(size=sizes, color=color, opacity=0.6),
                    name=nombre_display,
                    text=polys[columna_nombre].fillna(cat),
                    hovertemplate='%{text}<extra>' + nombre_display + '</extra>',
                    legendgroup=cat,
                    showlegend=first_in_group,
                ))

        fig.update_layout(
            mapbox=dict(
                style='open-street-map',
                center=dict(lat=19.332608, lon=-99.143209),
                zoom=13,
            ),
            title=dict(text=titulo, x=0.5, y=0.95,
                       xanchor='center', yanchor='top'),
            template='plotly_white',
            margin=dict(r=0, t=60, l=0, b=0),
            legend=dict(
                yanchor="top", y=0.99, xanchor="left", x=0.01,
                bgcolor="rgba(255,255,255,0.8)",
            ),
            hoverlabel=dict(bgcolor="white", font_size=12, font_family="Arial"),
        )

        return fig
