# callbacks.py

"""
Registra los callbacks para las interacciones de Dash,
separados del layout. Implementa inyección de dependencias
al necesitar el DataService para filtrar datos.
"""

import logging
from dash import Output, Input, State, dcc, html
import dash
import geopandas as gpd

from services.data_service import DataService
from domain.domain_models import DashboardFilters, MapVisualizationConfig
from figures.figures_utils import FiguresGenerator

logger = logging.getLogger(__name__)

def register_callbacks(app: dash.Dash, data_service: DataService) -> None:
    """
    Función que registra los callbacks de Dash, inyectando la dependencia
    'data_service' que maneja la lógica de datos.
    """

    @app.callback(
        Output("page-content", "children"),
        [Input("url", "pathname")]
    )
    def render_page(pathname: str):
        """
        Renderiza el contenido principal según la ruta seleccionada.
        """
        if pathname == "/":
            return html.Div("¡Bienvenido a la página de inicio!")
        elif pathname == "/page-1":
            return create_demograficos_page()
        elif pathname == "/page-2":
            return create_edafologicos_page()
        elif pathname == "/page-3":
            return create_electorales_page()
        else:
            return html.Div([
                html.H1("404 - No encontrado", className="text-danger"),
                html.P(f"La ruta {pathname} no corresponde a ninguna página existente."),
            ])

    def create_demograficos_page():
        """
        Crea el contenido para la página de demográficos,
        incluyendo dropdowns y divs para inyectar gráficos.
        """
        anios = data_service.obtener_anios_disponibles("demograficos")
        return html.Div([
            html.H3("Rubro: Tablero de demográfico"),
            create_filter_row(anios),
            html.Div(id="mapa-demograficos")
        ])

    def create_edafologicos_page():
        """
        Crea el contenido para la página de edafológicos.
        """
        anios = data_service.obtener_anios_disponibles("edafologicos")
        return html.Div([
            html.H3("Rubro: Tablero de edafológico"),
            create_filter_row(anios),
            html.Div(id="mapa-demograficos")  # O id distinto si gustas
        ])

    def create_electorales_page():
        """
        Crea el contenido para la página de electorales.
        """
        anios = data_service.obtener_anios_disponibles("electorales")
        return html.Div([
            html.H3("Rubro: Tablero de electoral"),
            create_filter_row(anios),
            html.Div(id="mapa-demograficos")  # O id distinto
        ])

    def create_filter_row(anios):
        """
        Crea una fila de dropdowns para Año, Granularidad, Métrica.
        Observa que podríamos reutilizar un solo ID en cada página
        o hacerlos distintos, según convenga.
        """
        return html.Div([
            html.Div([
                html.Label("Año:"),
                dcc.Dropdown(
                    id="anio",
                    options=[{"label": str(a), "value": a} for a in anios],
                    value=anios[0] if anios else None
                )
            ], style={"width": "20%", "display": "inline-block", "marginRight": "10px"}),

            html.Div([
                html.Label("Granularidad:"),
                dcc.Dropdown(
                    id="granularidad",
                    options=[
                        {"label": "Colonia", "value": "colonia"},
                        {"label": "AGEB", "value": "ageb"}
                    ],
                    value="colonia"
                )
            ], style={"width": "20%", "display": "inline-block", "marginRight": "10px"}),

            html.Div([
                html.Label("Métrica:"),
                dcc.Dropdown(
                    id="metrica",
                    value=None
                )
            ], style={"width": "20%", "display": "inline-block"})
        ], style={"display": "flex", "flexDirection": "row"})

    # CALLBACK: Poblar el dropdown "metrica"
    @app.callback(
        Output("metrica", "options"),
        [Input("anio", "value"), 
         Input("granularidad", "value"), 
         Input("url", "pathname")]
    )
    def actualizar_opciones_metrica(anio, gran, pathname):
        """
        Usa DataService para ver qué dataset usar según pathname,
        y genera las posibles columnas 'numéricas' para la métrica.
        """
        dataset_key = parse_dataset_key(pathname)
        gdf = data_service.datasets.get(dataset_key, None)
        if gdf is None or gdf.empty:
            logger.warning(f"Dataset '{dataset_key}' vacío o inexistente.")
            return []

        # Filtrar por año para deducir columnas relevantes
        gdf = gdf[gdf['anio'] == anio] if anio and 'anio' in gdf.columns else gdf
        # Podríamos filtrar también por 'gran' si existiera la columna 'granularidad'
        # ...
        numeric_cols = [
            c for c in gdf.columns if c not in ['geometry', 'anio'] and gdf[c].dtype.kind in ['i', 'f']
        ]
        return [{"label": c.capitalize(), "value": c} for c in numeric_cols]

    # CALLBACK: Generar el mapa
    @app.callback(
        Output("mapa-demograficos", "children"),
        [Input("anio", "value"), 
         Input("granularidad", "value"), 
         Input("metrica", "value"), 
         Input("url", "pathname")]
    )
    def actualizar_mapa(anio, gran, metrica, pathname):
        """
        Crea el mapa coroplético en base a los filtros.
        """
        if not metrica:
            return html.Div("Seleccione una métrica para visualizar el mapa.")

        dataset_key = parse_dataset_key(pathname)
        filters = DashboardFilters(anio=anio, granularidad=gran, metrica=metrica)
        gdf_filtrado = data_service.obtener_datos_filtrados(dataset_key, filters)
        if gdf_filtrado.empty:
            return html.Div("No se encontraron datos para los filtros seleccionados.")

        map_config = MapVisualizationConfig(
            titulo="Distribución de la Población en CDMX",
            columna_metrica = metrica,
            esquema_color = "Viridis",
            titulo_colorbar = "Población",
            zoom=10,
            latitud_centro=19.432608,
            longitud_centro=-99.133209,
            mapbox_style="carto-positron"
        )
        figura = FiguresGenerator.generar_mapa_coropletico(gdf_filtrado, map_config)
        if not figura:
            return html.Div("Mapa no disponible (datos vacíos).")
        return dcc.Graph(figure=figura)

def parse_dataset_key(pathname: str) -> str:
    """
    Dado un pathname, retorna la clave de dataset correspondiente.
    """
    if pathname == "/page-1":
        return "demograficos"
    elif pathname == "/page-2":
        return "edafologicos"
    elif pathname == "/page-3":
        return "electorales"
    return "demograficos"
