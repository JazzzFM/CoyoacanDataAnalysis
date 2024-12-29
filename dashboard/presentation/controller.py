# presentation/controller.py

"""
Clase DashAppController que encapsula:
1) La creación y configuración de la app de Dash.
2) El layout (sidebar + page-content).
3) El registro de callbacks para la navegación y generación de mapas.
"""

import logging
from typing import Optional, List

import dash
import dash_bootstrap_components as dbc
import geopandas as gpd
from dash import Dash, html, dcc, Input, Output

from services.data_service import DataService
from domain.domain_models import DashboardFilters, MapVisualizationConfig
from figures.figures_utils import FiguresGenerator

logger = logging.getLogger(__name__)

class DashAppController:
    """
    Clase principal de presentación (frontend) que encapsula:
    - La creación y configuración de una aplicación Dash.
    - El layout y la barra lateral (método create_layout()).
    - El registro de los callbacks (método register_callbacks()).
    - Un método run() para lanzar el servidor.

    Esto sigue un estilo POO, de modo que la app y sus componentes
    quedan contenidos en un objeto que se puede instanciar.
    """

    def __init__(self, data_service: DataService) -> None:
        """
        :param data_service: El servicio que provee los datos y filtrados (capa de negocio).
        """
        self.data_service: DataService = data_service

        # Creamos la instancia de la aplicación Dash
        self.app: Dash = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            suppress_callback_exceptions=True
        )

        # Asignamos el layout usando un método de esta clase.
        self.app.layout = self.create_layout()

        # Registramos todos los callbacks
        self.register_callbacks()

    def create_layout(self) -> html.Div:
        """
        Construye la estructura principal del layout (sidebar + content).
        Este layout se asigna como self.app.layout en el constructor.
        """
        sidebar_style = {
            "position": "fixed",
            "top": 0,
            "left": 0,
            "bottom": 0,
            "width": "16rem",
            "padding": "2rem 1rem",
            "background-color": "#f8f9fa",
            "overflow-y": "auto",
        }

        content_style = {
            "margin-left": "18rem",
            "margin-right": "2rem",
            "padding": "2rem 1rem",
        }

        sidebar = html.Div([
            html.H2("Coyoacán", className="display-4"),
            html.Hr(),
            html.P("Análisis de Datos Georeferenciados", className="lead"),
            dbc.Nav(
                [
                    dbc.NavLink("Inicio", href="/", active="exact"),
                    dbc.NavLink("Demográficos", href="/page-1", active="exact"),
                    dbc.NavLink("Edafológicos", href="/page-2", active="exact"),
                    dbc.NavLink("Electorales", href="/page-3", active="exact"),
                ],
                vertical=True,
                pills=True,
            ),
        ], style=sidebar_style)

        content = html.Div(id="page-content", style=content_style)

        return html.Div([
            dcc.Location(id="url"),
            sidebar,
            content
        ])

    def register_callbacks(self) -> None:
        """
        Aquí definimos todos los callbacks de Dash:
        - Navegación entre páginas (pathname)
        - Dropdowns (Año, Granularidad, Métrica)
        - Generación del mapa
        """
        app = self.app  # Para referirnos a self.app dentro de los decoradores

        @app.callback(
            Output("page-content", "children"),
            [Input("url", "pathname")]
        )
        def render_page_content(pathname: str) -> html.Div:
            """
            Renderiza el contenido de la página según la ruta.
            """
            if pathname == "/":
                return html.Div("¡Bienvenido a la página de inicio!")
            elif pathname == "/page-1":
                return self.create_demograficos_page()
            elif pathname == "/page-2":
                return self.create_edafologicos_page()
            elif pathname == "/page-3":
                return self.create_electorales_page()
            else:
                return html.Div([
                    html.H1("404: No encontrado", className="text-danger"),
                    html.Hr(),
                    html.P(f"La ruta {pathname} no fue reconocida."),
                ])

        @app.callback(
            Output("metrica", "options"),
            [Input("anio", "value"), Input("granularidad", "value"), Input("url", "pathname")]
        )
        def actualizar_opciones_metrica(anio: Optional[int], gran: str, pathname: str):
            """
            Callback para llenar el dropdown de 'metrica'
            según el dataset que se asigna por pathname y el año seleccionado.
            """
            dataset_key = self.parse_dataset_key(pathname)
            gdf = self.data_service.datasets.get(dataset_key)
            if gdf is None or gdf.empty:
                logger.warning(f"Dataset '{dataset_key}' vacío o inexistente.")
                return []

            if anio and "anio" in gdf.columns:
                gdf = gdf[gdf["anio"] == anio]

            # Filtrar columnas numéricas
            numeric_cols = [
                c for c in gdf.columns
                if c not in ("geometry", "anio") and gdf[c].dtype.kind in ["i", "f"]
            ]
            return [{"label": c.replace("_", " ").capitalize(), "value": c} for c in numeric_cols]

        @app.callback(
            Output("mapa-demograficos", "children"),
            [Input("anio", "value"), 
             Input("granularidad", "value"), 
             Input("metrica", "value"), 
             Input("url", "pathname")]
        )
        def actualizar_mapa(anio: Optional[int], gran: str, metrica: Optional[str], pathname: str):
            """
            Genera el mapa coroplético según los filtros seleccionados.
            """
            if not metrica:
                return html.Div("Seleccione una métrica para visualizar el mapa.")

            dataset_key = self.parse_dataset_key(pathname)
            # Llenamos un objeto DashboardFilters
            filters = DashboardFilters(anio=anio, granularidad=gran, metrica=metrica)
            gdf_filtrado = self.data_service.obtener_datos_filtrados(dataset_key, filters)
            if gdf_filtrado.empty:
                return html.Div("No se encontraron datos para los filtros seleccionados.")

            # Creamos la configuración para el mapa
            map_config = MapVisualizationConfig(
                titulo="Distribución de la Población en CDMX",
                columna_metrica = metrica,
                esquema_color = "Viridis",
                titulo_colorbar = "Población",
                zoom=13,
                latitud_centro=19.332608,
                longitud_centro=-99.143209,
                mapbox_style="carto-positron"
            )
            figura = FiguresGenerator.generar_mapa_coropletico(gdf_filtrado, map_config)
            if figura is None:
                return html.Div("Mapa no disponible (datos vacíos).")

            return dcc.Graph(figure=figura, style={
                'width': '100%',
                'height': '800px'
            })

    def create_demograficos_page(self) -> html.Div:
        """
        Genera el layout para la página de datos demográficos.
        """
        anios = self.data_service.obtener_anios_disponibles("demograficos")
        return html.Div([
            html.H3("Rubro: Tablero de Demográfico"),
            self.create_filter_row(anios),
            html.Div(id="mapa-demograficos")
        ])

    def create_edafologicos_page(self) -> html.Div:
        anios = self.data_service.obtener_anios_disponibles("edafologicos")
        return html.Div([
            html.H3("Rubro: Tablero de Edafológico"),
            self.create_filter_row(anios),
            html.Div(id="mapa-demograficos")
        ])

    def create_electorales_page(self) -> html.Div:
        anios = self.data_service.obtener_anios_disponibles("electorales")
        return html.Div([
            html.H3("Rubro: Tablero Electoral"),
            self.create_filter_row(anios),
            html.Div(id="mapa-demograficos")
        ])

    def create_filter_row(self, anios: List[int]) -> html.Div:
        """
        Crea los dropdowns de Año, Granularidad y Métrica en una sola fila.
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

    def parse_dataset_key(self, pathname: str) -> str:
        """
        Determina la clave del dataset según el pathname.
        """
        if pathname == "/page-1":
            return "demograficos"
        elif pathname == "/page-2":
            return "edafologicos"
        elif pathname == "/page-3":
            return "electorales"
        return "demograficos"

    def run(self, debug: bool = True) -> None:
        """
        Inicia el servidor de Dash.
        """
        self.app.run_server(debug=debug)

