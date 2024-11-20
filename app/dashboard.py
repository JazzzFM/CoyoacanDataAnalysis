# app/dashboard.py
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import geopandas as gpd
import pandas as pd

# Cargar datos
manzanas_gdf = gpd.read_file("data/manzanas_coyoacan.geojson")

def init_dashboard(server):
    dash_app = Dash(__name__, server=server, url_base_pathname='/dashboard/')
    
    # Layout del dashboard
    dash_app.layout = html.Div([
        html.Div([
            html.H1("Coyoacán Dashboard", style={'text-align': 'center', 'padding': '20px'}),
            
            # Filtros
            html.Div([
                html.Label("Selecciona una Zona:", style={'font-weight': 'bold'}),
                dcc.Dropdown(
                    id='zone-dropdown',
                    options=[{'label': nombre, 'value': nombre} for nombre in manzanas_gdf['nombre'].unique()],
                    placeholder="Selecciona una zona",
                    multi=True,
                    style={'width': '100%', 'margin-bottom': '15px'}
                ),
            ], style={'padding': '20px', 'width': '30%', 'display': 'inline-block', 'vertical-align': 'top'}),
            
            # Vista Previa
            html.Div([
                html.H4("Información de Zona Seleccionada"),
                html.Div(id="zone-info", style={'padding': '10px', 'border': '1px solid #ddd', 'border-radius': '5px'}),
            ], style={'width': '60%', 'display': 'inline-block', 'vertical-align': 'top', 'margin-left': '5%'})
            
        ], style={'display': 'flex', 'justify-content': 'space-between', 'width': '100%', 'padding': '20px'}),
        
        # Mapa
        html.Div([
            dcc.Graph(id='map-graph')
        ], style={'padding': '20px', 'width': '100%'}),
        
    ], style={'background-color': '#f9f9f9', 'font-family': 'Arial', 'margin': '0', 'padding': '0'})

    # Callback para actualizar el mapa basado en la selección
    @dash_app.callback(
        Output('map-graph', 'figure'),
        [Input('zone-dropdown', 'value')]
    )
    def update_map(selected_zones):
        # Filtrar el DataFrame basado en la selección del dropdown
        filtered_gdf = manzanas_gdf if not selected_zones else manzanas_gdf[manzanas_gdf['nombre'].isin(selected_zones)]
        
        # Crear el mapa
        fig = px.choropleth_mapbox(
            filtered_gdf,
            geojson=filtered_gdf.geometry,
            locations=filtered_gdf.index,
            color='nombre',
            mapbox_style="carto-positron",
            zoom=10,
            center={"lat": 19.3437, "lon": -99.1621},
            opacity=0.6,
            hover_name="nombre"
        )
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        return fig
    
    # Callback para mostrar información de la zona seleccionada al hacer clic en el mapa
    @dash_app.callback(
        Output('zone-info', 'children'),
        [Input('map-graph', 'clickData')]
    )
    def display_zone_info(clickData):
        if clickData:
            zone_name = clickData['points'][0]['hovertext']
            selected_zone = manzanas_gdf[manzanas_gdf['nombre'] == zone_name].iloc[0]
            # Información detallada de la zona
            info = [
                html.P(f"Nombre: {selected_zone['nombre']}", style={'font-weight': 'bold'}),
                html.P(f"Área: {selected_zone.geometry.area:.2f} m²"),
                html.P(f"Coordenadas: {selected_zone.geometry.centroid.y:.4f}, {selected_zone.geometry.centroid.x:.4f}")
            ]
            return info
        return "Haz clic en una zona del mapa para ver detalles."

    return dash_app

