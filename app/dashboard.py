# dashboard.py
from dash import Dash, html, dcc
import plotly.express as px
import geopandas as gpd
import pandas as pd

def init_dashboard(server):
    dash_app = Dash(__name__, server=server, url_base_pathname='/dashboard/')
    
    # Cargar el archivo GeoJSON de 'manzanas_coyoacan'
    manzanas_gdf = gpd.read_file("data/manzanas_coyoacan.geojson")

    # Asegurarse de que la columna 'nombre' existe
    if 'nombre' not in manzanas_gdf.columns:
        manzanas_gdf['nombre'] = 'Unknown'  # Valor por defecto si falta

    # Crear la figura de Plotly
    fig_manzanas = px.choropleth_mapbox(
        manzanas_gdf,
        geojson=manzanas_gdf.geometry,
        locations=manzanas_gdf.index,
        color='nombre',  
        mapbox_style="carto-positron",
        zoom=10,
        center={"lat": 19.3437, "lon": -99.1621},
        opacity=0.5,
        hover_name="nombre"
    )
    fig_manzanas.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    # Definir el layout de Dash
    dash_app.layout = html.Div([
        html.H1("Mapa de Manzanas en Coyoacán"),
        dcc.Graph(figure=fig_manzanas)
    ])

    return dash_app

