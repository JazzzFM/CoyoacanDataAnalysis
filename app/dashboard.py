# app/dashboard.py
import os
import logging
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import geopandas as gpd
from sqlalchemy import create_engine

logger = logging.getLogger(__name__)

def _load_colonias():
    """Carga polígonos de colonias desde Neon PostGIS."""
    db_uri = os.getenv("DATABASE_URI")
    if not db_uri:
        logger.warning("DATABASE_URI no configurada, dashboard sin datos")
        return gpd.GeoDataFrame()

    try:
        engine = create_engine(db_uri, pool_pre_ping=True, pool_recycle=300)
        sql = """
            SELECT DISTINCT "NOMBRE_COLONIA" AS nombre,
                   "GEOM_COLONIA" AS geom
            FROM poligonos_manzanas_agebs_colonias
            WHERE "GEOM_COLONIA" IS NOT NULL
        """
        gdf = gpd.read_postgis(sql, engine, geom_col="geom")
        logger.info(f"Colonias cargadas desde PostGIS: {len(gdf)} registros")
        return gdf
    except Exception as e:
        logger.error(f"Error cargando colonias desde PostGIS: {e}")
        return gpd.GeoDataFrame()


def init_dashboard(server):
    dash_app = Dash(__name__, server=server, url_base_pathname='/dashboard/')

    colonias_gdf = _load_colonias()
    has_data = not colonias_gdf.empty

    options = (
        [{'label': n, 'value': n} for n in sorted(colonias_gdf['nombre'].dropna().unique())]
        if has_data else []
    )

    dash_app.layout = html.Div([
        html.Div([
            html.H1("Coyoacán Dashboard", style={'text-align': 'center', 'padding': '20px'}),

            html.Div([
                html.Label("Selecciona una Colonia:", style={'font-weight': 'bold'}),
                dcc.Dropdown(
                    id='zone-dropdown',
                    options=options,
                    placeholder="Selecciona una colonia",
                    multi=True,
                    style={'width': '100%', 'margin-bottom': '15px'}
                ),
            ], style={'padding': '20px', 'width': '30%', 'display': 'inline-block', 'vertical-align': 'top'}),

            html.Div([
                html.H4("Información de Colonia Seleccionada"),
                html.Div(id="zone-info", style={'padding': '10px', 'border': '1px solid #ddd', 'border-radius': '5px'}),
            ], style={'width': '60%', 'display': 'inline-block', 'vertical-align': 'top', 'margin-left': '5%'})

        ], style={'display': 'flex', 'justify-content': 'space-between', 'width': '100%', 'padding': '20px'}),

        dcc.Store(id='colonias-loaded', data=has_data),

        html.Div([
            dcc.Graph(id='map-graph')
        ], style={'padding': '20px', 'width': '100%'}),

    ], style={'background-color': '#f9f9f9', 'font-family': 'Arial', 'margin': '0', 'padding': '0'})

    @dash_app.callback(
        Output('map-graph', 'figure'),
        [Input('zone-dropdown', 'value')]
    )
    def update_map(selected_zones):
        if not has_data:
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.update_layout(title="Sin datos de polígonos disponibles")
            return fig

        filtered = colonias_gdf if not selected_zones else colonias_gdf[colonias_gdf['nombre'].isin(selected_zones)]

        fig = px.choropleth_mapbox(
            filtered,
            geojson=filtered.geometry,
            locations=filtered.index,
            color='nombre',
            mapbox_style="carto-positron",
            zoom=12,
            center={"lat": 19.332608, "lon": -99.143209},
            opacity=0.6,
            hover_name="nombre"
        )
        fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        return fig

    @dash_app.callback(
        Output('zone-info', 'children'),
        [Input('map-graph', 'clickData')]
    )
    def display_zone_info(clickData):
        if not has_data:
            return "Sin datos disponibles."
        if clickData:
            zone_name = clickData['points'][0].get('hovertext', '')
            matches = colonias_gdf[colonias_gdf['nombre'] == zone_name]
            if not matches.empty:
                selected = matches.iloc[0]
                return [
                    html.P(f"Colonia: {selected['nombre']}", style={'font-weight': 'bold'}),
                    html.P(f"Coordenadas: {selected.geometry.centroid.y:.4f}, {selected.geometry.centroid.x:.4f}")
                ]
        return "Haz clic en una colonia del mapa para ver detalles."

    return dash_app

