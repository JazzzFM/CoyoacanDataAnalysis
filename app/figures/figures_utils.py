# utils/figures_utils.py

"""
Genera visualizaciones (e.g. mapas coropléticos) con Plotly.
"""

import warnings
import geopandas as gpd
from geopandas import GeoDataFrame
import pandas as pd
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
        custom_data_cols = [col for col in config.hover_columns
                           if col in data.columns
                           and col != config.columna_metrica]

        # Separar columnas de enriquecimiento de las regulares
        enrichment_prefix = '_tooltip_'
        col_idx = {c: i for i, c in enumerate(custom_data_cols)}
        has_enrichment = any(c.startswith(enrichment_prefix)
                            for c in custom_data_cols)

        # Crear el mapa coroplético con Plotly Express
        fig = px.choropleth_mapbox(
            data_frame=data,
            geojson=data.__geo_interface__,
            locations=data.index,
            color=config.columna_metrica,
            mapbox_style=config.mapbox_style,
            zoom=config.zoom,
            center={"lat": config.latitud_centro,
                    "lon": config.longitud_centro},
            color_continuous_scale=config.esquema_color,
            opacity=0.7,
            hover_name=(config.nombre_hover
                        if config.nombre_hover
                        else config.columna_metrica),
            custom_data=custom_data_cols,
        )

        # -------------------------------------------
        # Construir hover_template
        # -------------------------------------------
        metrica_label = config.columna_metrica.replace('_', ' ').title()

        if has_enrichment:
            # Template enriquecido con ranking, desviación y semáforo
            hover_template = f"<b>%{{hovertext}}</b><br>──────────────<br>"

            # Métrica principal + semáforo
            hover_template += f"<b>{metrica_label}:</b> %{{z:,.1f}}"
            if '_tooltip_semaforo' in col_idx:
                hover_template += (
                    f"  %{{customdata[{col_idx['_tooltip_semaforo']}]}}")
            hover_template += "<br>"

            # Ranking
            if '_tooltip_ranking' in col_idx and '_tooltip_total' in col_idx:
                hover_template += (
                    f"<b>Ranking:</b> "
                    f"#%{{customdata[{col_idx['_tooltip_ranking']}]}} "
                    f"de %{{customdata[{col_idx['_tooltip_total']}]}}<br>")

            # Desviación vs promedio
            if '_tooltip_desviacion' in col_idx and '_tooltip_media' in col_idx:
                hover_template += (
                    f"<b>vs Promedio:</b> "
                    f"%{{customdata[{col_idx['_tooltip_desviacion']}]}} "
                    f"(media: %{{customdata[{col_idx['_tooltip_media']}]:,.1f}})"
                    f"<br>")

            # Columnas regulares del rubro
            regular_cols = [c for c in custom_data_cols
                           if not c.startswith(enrichment_prefix)
                           and c != config.nombre_hover]
            if regular_cols:
                hover_template += "──────────────<br>"
                for col in regular_cols:
                    label = col.replace('_', ' ').title()
                    idx = col_idx[col]
                    hover_template += (
                        f"<b>{label}:</b> %{{customdata[{idx}]}}<br>")

            hover_template += "<extra></extra>"
        else:
            # Template original (fallback)
            hover_template = (
                f"• <b>{config.columna_metrica}:</b> %{{z}}<br>")
            for i, col in enumerate(custom_data_cols):
                hover_template += (
                    f"• <b>{col}:</b> %{{customdata[{i}]}}<br>")
            hover_template += "<extra></extra>"

        # Se aplica el hover_template a la traza
        fig.update_traces(
            hovertemplate=hover_template,
            marker_line_color='white',
            marker_line_width=0.5,
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

    @staticmethod
    def generar_mapa_resumen(
        gdf: GeoDataFrame,
        columna_valor: str,
        columna_nombre: str,
        titulo: str,
    ) -> Optional[go.Figure]:
        """
        Genera un mapa coroplético compacto para el resumen ejecutivo.
        """
        if gdf is None or gdf.empty:
            return None

        fig = px.choropleth_mapbox(
            data_frame=gdf,
            geojson=gdf.__geo_interface__,
            locations=gdf.index,
            color=columna_valor,
            mapbox_style='open-street-map',
            zoom=12,
            center={"lat": 19.332608, "lon": -99.143209},
            color_continuous_scale='Viridis',
            opacity=0.7,
            hover_name=columna_nombre,
        )
        fig.update_traces(
            marker_line_color='white',
            marker_line_width=0.5,
            hovertemplate=(
                '<b>%{hovertext}</b><br>'
                f'{columna_valor}: %{{z:.1f}}'
                '<extra></extra>'
            ),
        )
        fig.update_layout(
            title=dict(text=titulo, x=0.5, xanchor='center'),
            template='plotly_white',
            margin=dict(r=0, t=40, l=0, b=0),
            height=460,
            coloraxis_colorbar=dict(
                title=columna_valor.replace('_', ' ').title(),
                len=0.6,
                thickness=15,
            ),
        )
        return fig

    @staticmethod
    def generar_barras_horizontales(
        df: pd.DataFrame,
        columna_nombre: str,
        columna_valor: str,
        titulo: str,
        n: int = 10,
    ) -> Optional[go.Figure]:
        """
        Genera un bar chart horizontal con las top N entidades.
        """
        if df is None or df.empty:
            return None

        top = df.nlargest(n, columna_valor)[[columna_nombre, columna_valor]].copy()
        top = top.sort_values(columna_valor, ascending=True)

        fig = px.bar(
            top, x=columna_valor, y=columna_nombre,
            orientation='h',
            color=columna_valor,
            color_continuous_scale='Viridis',
            title=titulo,
        )
        fig.update_layout(
            template='plotly_white',
            margin=dict(r=10, t=40, l=0, b=0),
            height=225,
            showlegend=False,
            yaxis_title=None,
            xaxis_title=None,
            coloraxis_showscale=False,
        )
        return fig

    @staticmethod
    def generar_dona(
        df: pd.DataFrame,
        columna_categoria: str,
        titulo: str,
        n_categorias: int = 8,
    ) -> Optional[go.Figure]:
        """
        Genera un donut chart con la distribución de una columna categórica.
        """
        if df is None or df.empty:
            return None

        conteos = df[columna_categoria].value_counts().head(n_categorias)
        fig = px.pie(
            values=conteos.values,
            names=conteos.index,
            title=titulo,
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig.update_traces(textinfo='percent+label', textfont_size=10)
        fig.update_layout(
            template='plotly_white',
            margin=dict(r=10, t=40, l=10, b=10),
            height=225,
            showlegend=False,
        )
        return fig

    @staticmethod
    def generar_radar_comparativo(
        df: pd.DataFrame,
        colonias: list,
        metricas: list,
        labels: list,
    ) -> Optional[go.Figure]:
        """
        Genera un radar chart comparativo para 2-3 colonias.
        Los valores se normalizan a 0-100 por métrica.
        """
        if df is None or df.empty or not colonias:
            return None

        # Filtrar solo métricas numéricas disponibles
        metricas_validas = []
        labels_validas = []
        for m, l in zip(metricas, labels):
            if m in df.columns and df[m].dtype.kind in ('i', 'f'):
                metricas_validas.append(m)
                labels_validas.append(l)

        if len(metricas_validas) < 3:
            return None

        fig = go.Figure()
        for colonia in colonias:
            row = df[df['colonia'] == colonia]
            if row.empty:
                continue
            valores_norm = []
            for m in metricas_validas:
                val = row[m].values[0]
                col_min = df[m].min()
                col_max = df[m].max()
                if col_max > col_min:
                    norm = (val - col_min) / (col_max - col_min) * 100
                else:
                    norm = 50
                valores_norm.append(round(norm, 1))

            fig.add_trace(go.Scatterpolar(
                r=valores_norm + [valores_norm[0]],
                theta=labels_validas + [labels_validas[0]],
                fill='toself',
                name=colonia,
                opacity=0.6,
            ))

        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            template='plotly_white',
            title=dict(text='Perfil comparativo', x=0.5, xanchor='center'),
            margin=dict(r=30, t=50, l=30, b=30),
            height=500,
            legend=dict(orientation='h', yanchor='bottom', y=-0.15,
                        xanchor='center', x=0.5),
        )
        return fig

    @staticmethod
    def generar_mapa_vulnerabilidad(
        gdf: GeoDataFrame,
        columna_score: str,
        columna_quintil: str,
        columna_nombre: str,
        componentes_cols: List[str],
    ) -> Optional[go.Figure]:
        """
        Genera un mapa coroplético de vulnerabilidad con paleta divergente
        verde→rojo (RdYlGn_r) y tooltip con score + quintil + componentes.
        """
        if gdf is None or gdf.empty:
            return None

        custom_cols = [columna_quintil] + componentes_cols
        custom_cols = [c for c in custom_cols if c in gdf.columns]
        col_idx = {c: i for i, c in enumerate(custom_cols)}

        fig = px.choropleth_mapbox(
            data_frame=gdf,
            geojson=gdf.__geo_interface__,
            locations=gdf.index,
            color=columna_score,
            mapbox_style='open-street-map',
            zoom=12,
            center={"lat": 19.332608, "lon": -99.143209},
            color_continuous_scale='RdYlGn_r',
            range_color=[0, 100],
            opacity=0.8,
            hover_name=columna_nombre,
            custom_data=custom_cols,
        )

        # Hover template enriquecido
        hover = "<b>%{hovertext}</b><br>──────────────<br>"
        hover += "<b>Score vulnerabilidad:</b> %{z:.1f}/100<br>"
        if columna_quintil in col_idx:
            hover += (
                f"<b>Clasificación:</b> "
                f"%{{customdata[{col_idx[columna_quintil]}]}}<br>")
        hover += "──────────────<br>"
        for comp_col in componentes_cols:
            if comp_col in col_idx:
                label = comp_col.replace('_norm', '').replace('_', ' ').title()
                hover += (
                    f"<b>{label}:</b> "
                    f"%{{customdata[{col_idx[comp_col]}]:.1f}}<br>")
        hover += "<extra></extra>"

        fig.update_traces(
            hovertemplate=hover,
            marker_line_color='white',
            marker_line_width=0.8,
        )

        fig.update_layout(
            template='plotly_white',
            title=dict(
                text='Índice de Vulnerabilidad Territorial — Coyoacán',
                x=0.5, y=0.95, xanchor='center', yanchor='top'),
            margin=dict(r=0, t=60, l=0, b=0),
            height=600,
            hoverlabel=dict(bgcolor="white", font_size=12, font_family="Arial"),
            coloraxis_colorbar=dict(
                title="Vulnerabilidad",
                tickvals=[0, 25, 50, 75, 100],
                ticktext=["0 (baja)", "25", "50", "75", "100 (alta)"],
                len=0.7, thickness=15,
            ),
        )
        return fig

    @staticmethod
    def generar_mapa_multicapa(
        gdf_base: GeoDataFrame,
        columna_valor: str,
        columna_nombre: str,
        opacidad_base: float,
        gdf_infra: GeoDataFrame,
        cats_infra: list,
        gdf_recursos: GeoDataFrame,
        cats_recursos: list,
    ) -> Optional[go.Figure]:
        """
        Genera un mapa multicapa: coropleta base + overlays de scatter.
        Reutiliza generar_mapa_categorico para los overlays.
        """
        if gdf_base is None or gdf_base.empty:
            return None

        # --- Capa base: coropleta ---
        fig = px.choropleth_mapbox(
            data_frame=gdf_base,
            geojson=gdf_base.__geo_interface__,
            locations=gdf_base.index,
            color=columna_valor,
            mapbox_style='open-street-map',
            zoom=12,
            center={"lat": 19.332608, "lon": -99.143209},
            color_continuous_scale='Viridis',
            opacity=opacidad_base,
            hover_name=columna_nombre,
        )
        fig.update_traces(
            marker_line_color='white',
            marker_line_width=0.5,
            hovertemplate=(
                '<b>%{hovertext}</b><br>'
                f'{columna_valor.replace("_", " ").title()}: '
                '%{z:,.1f}<extra></extra>'
            ),
        )

        # --- Overlays: transferir traces de generar_mapa_categorico ---
        if cats_infra:
            overlay = FiguresGenerator.generar_mapa_categorico(
                gdf=gdf_infra, columna_cat='subcategoria',
                columna_nombre='nombre', titulo='',
                categorias_visibles=cats_infra)
            if overlay:
                for trace in overlay.data:
                    fig.add_trace(trace)

        if cats_recursos:
            overlay = FiguresGenerator.generar_mapa_categorico(
                gdf=gdf_recursos, columna_cat='categoria',
                columna_nombre='nombre', titulo='',
                categorias_visibles=cats_recursos)
            if overlay:
                for trace in overlay.data:
                    fig.add_trace(trace)

        # --- Layout final ---
        titulo_metrica = columna_valor.replace('_', ' ').title()
        fig.update_layout(
            template='plotly_white',
            title=dict(text=f'Capas: {titulo_metrica} + overlays',
                       x=0.5, y=0.95, xanchor='center', yanchor='top'),
            margin=dict(r=0, t=60, l=0, b=0),
            legend=dict(
                yanchor="top", y=0.99, xanchor="left", x=0.01,
                bgcolor="rgba(255,255,255,0.8)",
            ),
            hoverlabel=dict(bgcolor="white", font_size=12,
                            font_family="Arial"),
            coloraxis_colorbar=dict(
                title=titulo_metrica, len=0.6, thickness=15),
        )
        return fig
