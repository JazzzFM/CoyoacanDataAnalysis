import logging
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

import dash
import dash_bootstrap_components as dbc
from dash import Dash, Input, Output, dcc, html
import geopandas as gpd

# Se asume que en tu proyecto ya existen estas clases o módulos.
from data_loader import DataLoader, DatabaseConfig
from data_processor import DataProcessor
from figures_utils import FiguresUtils

# ------------------------------------------------------------------------------------------
# Configurar el sistema de logging
# ------------------------------------------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(levelname)s] %(asctime)s - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------------------
# Dataclasses de Configuración
# ------------------------------------------------------------------------------------------

@dataclass
class LayoutStyleConfig:
    """
    Clase para definir la configuración de estilos del layout (barra lateral y contenido).
    """
    sidebar_style: Dict[str, Any]
    content_style: Dict[str, Any]

@dataclass
class MapConfig:
    """
    Clase para gestionar la configuración de los mapas a generar.
    """
    titulo: str
    columna_metrica: str
    esquema_color: str

def get_dataset_key_for_path(pathname: str) -> str:
    """
    Determina la clave de 'self.datos' que se utilizará
    según el pathname recibido.
    """
    if pathname == "/page-1":
        return "demograficos"
    elif pathname == "/page-2":
        return "edafologicos"
    elif pathname == "/page-3":
        return "electorales"

    # Página por defecto o en caso de no coincidir nada:
    return "demograficos"
# ------------------------------------------------------------------------------------------
# Clase principal del Dashboard
# ------------------------------------------------------------------------------------------
class DashboardApp:
    """
    Clase principal que configura y ejecuta la aplicación Dash.
    Cumple con los principios SOLID, teniendo una responsabilidad clara:
    - Crear la aplicación
    - Definir el layout
    - Configurar los callbacks
    - Iniciar el servidor de Dash
    """

    def __init__(self) -> None:
        """
        Constructor que inicializa la configuración de la base de datos, carga los datos
        necesarios y genera la instancia de la aplicación Dash.
        """
        # Configuración de la base de datos (SRP: separar la responsabilidad de cargar datos en DataLoader)
        config = DatabaseConfig()

        # Inicializa el cargador de datos con la configuración
        self.data_loader: DataLoader = DataLoader(config)

        try:
            # Carga datos estáticos (una sola vez) mediante el DataLoader
            self.datos: Dict[str, gpd.GeoDataFrame] = self.data_loader.load_static_data()
            logger.info("Datos cargados exitosamente.")
        except Exception as e:
            logger.error(f"Error al cargar datos: {e}")
            raise RuntimeError("No se pudieron cargar los datos para la aplicación.")

        # Crea la instancia de la aplicación Dash
        self.app: Dash = Dash(
            __name__,
            external_stylesheets = [dbc.themes.BOOTSTRAP],
            suppress_callback_exceptions = True
        )

        # Define la configuración de estilos del layout usando la dataclass LayoutStyleConfig
        self.layout_style_config: LayoutStyleConfig = LayoutStyleConfig(
            sidebar_style = {
                "position": "fixed",
                "top": 0,
                "left": 0,
                "bottom": 0,
                "width": "16rem",
                "padding": "2rem 1rem",
                "background-color": "#f8f9fa",
                "overflow-y": "auto",
            },
            content_style = {
                "margin-left": "18rem",
                "margin-right": "2rem",
                "padding": "2rem 1rem",
            }
        )

        # Configurar el layout y callbacks de la aplicación
        self.layout_app()
        self.add_callbacks()

    def layout_app(self) -> None:
        """
        Define el layout general de la aplicación, incluyendo la barra lateral (sidebar)
        y el área de contenido.
        """
        # Barra lateral que contiene los enlaces de navegación
        sidebar: html.Div = html.Div(
            [
                html.H2("Coyoacán", className="display-4"),           # Título del sidebar
                html.Hr(),                                            # Separador
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
            ],
            style=self.layout_style_config.sidebar_style
        )

        # Contenedor principal para las vistas dinámicas (pages)
        content: html.Div = html.Div(id="page-content", style=self.layout_style_config.content_style)

        # Asigna el layout principal de la app
        logger.info("Iniciando configuración del layout...")
        self.app.layout = html.Div([
            dcc.Location(id="url"),  # Permite a Dash acceder a la ruta actual
            sidebar,
            content
        ])
        logger.info("Layout principal asignado.")

    def add_callbacks(self) -> None:
        """
        Registra todos los callbacks de la aplicación:
        - Navegación entre páginas
        - Actualización de los gráficos en función de los filtros seleccionados
        """

        @self.app.callback(
            Output("page-content", "children"),
            [Input("url", "pathname")]
        )
        def render_page_content(pathname: str) -> html.Div:
            """
            Callback para renderizar el contenido de la página según la ruta
            seleccionada en la barra lateral.
            
            :param pathname: Ruta de la aplicación (/page-1, /page-2, etc.)
            :return: Componente HTML con el contenido de la página correspondiente.
            """
            # Página de inicio
            if pathname == "/":
                return html.P("Esta es la página de inicio del dashboard de Coyoacán. ¡Bienvenido!")

            # Página de demográficos
            elif pathname == "/page-1":
                return self.generate_dashboard(category='demográfico')

            # Página de edafológicos
            elif pathname == "/page-2":
                return self.generate_dashboard(category='edafológico')

            # Página de electorales
            elif pathname == "/page-3":
                return self.generate_dashboard(category='electoral')

            # Página no encontrada
            return html.Div(
                [
                    html.H1("404: No encontrado", className="text-danger"),
                    html.Hr(),
                    html.P(f"El pathname {pathname} no fue reconocido."),
                ],
                className="p-3 bg-light rounded-3",
            )
        
        @self.app.callback(
            Output("metrica", "options"),
            [
                Input("url", "pathname"),
                Input("anio", "value"),
                Input("nivel-granularidad", "value")
            ]
        )
        def actualizar_opciones_metrica(pathname, anio, nivel_granularidad):
            """
            Determina las opciones del dropdown 'Métrica'
            en base al dataset correspondiente a `pathname`.
            """
            logger.debug(f"--> actualizar_opciones_metrica(path={pathname}, anio={anio}, gran={nivel_granularidad})")
            try:
                df_key = get_dataset_key_for_path(pathname)
                df = self.datos.get(df_key, None)

                if df is None or df.empty:
                    logger.warning(f"El DataFrame '{df_key}' está vacío o no existe.")
                    return []

                # Filtrado por año
                if 'anio' in df.columns and anio is not None:
                    df = df[df['anio'] == anio]

                # (Opcional) Filtrado adicional por granularidad
                # ...

                # Columnas numéricas
                columnas_numericas = [
                    col for col in df.columns
                    if col not in ['geometry', 'anio'] and df[col].dtype.kind in ['i', 'f']
                ]
                options = [
                    {"label": col.replace("_", " ").capitalize(), "value": col}
                    for col in columnas_numericas
                ]
                logger.debug(f"[{df_key}] Opciones generadas: {options}")
                return options
            except Exception as e:
                logger.error(f"Error al actualizar las opciones de 'metrica': {e}")
                return []
        
        @self.app.callback(
            Output("nuevo-mapa-interactivo", "children"),
            [
                Input("url", "pathname"),
                Input("anio", "value"),
                Input("nivel-granularidad", "value"),
                Input("metrica", "value")
            ]
        )
        def actualizar_nuevo_mapa(pathname, anio, nivel_granularidad, metrica):
            """
            Genera el mapa coroplético en base a la página (dataset),
            el año, la granularidad y la métrica seleccionada.
            """
            logger.debug(f"--> actualizar_nuevo_mapa(path={pathname}, anio={anio}, gran={nivel_granularidad}, metrica={metrica})")
            try:
                if not metrica:
                    logger.warning("No se seleccionó una métrica válida.")
                    return html.Div("Seleccione una métrica para visualizar el mapa.")

                df_key = get_dataset_key_for_path(pathname)
                datos_procesados = self.get_filtered_data(
                    anio = anio,
                    nivel_granularidad = nivel_granularidad,
                    metrica = metrica,
                    dataframe_key = df_key
                )

                if datos_procesados.empty:
                    logger.warning(f"[{df_key}] Los datos procesados están vacíos.")
                    return html.Div("No se encontraron datos para los filtros seleccionados.")

                mapa_config = MapConfig(
                    titulo=f"{metrica.replace('_', ' ').capitalize()} "
                        f"por {nivel_granularidad.capitalize()} - {anio}",
                    columna_metrica=metrica,
                    esquema_color="Viridis"
                )

                mapa = FiguresUtils.generar_mapa_coropletico(datos_procesados, mapa_config)
                logger.debug(f"Mapa coroplético generado para [{df_key}] con métrica={metrica}.")

                return dcc.Graph(figure=mapa)

            except Exception as e:
                logger.error(f"Error en actualizar_nuevo_mapa: {e}")
                return html.Div("Ocurrió un error al generar el mapa.")
            
    def create_filter_row(self, anios_disponibles: List[int]) -> html.Div:
        """
        Crea y retorna una fila de filtros (dropdowns) para seleccionar el año,
        la granularidad y la métrica.

        :param anios_disponibles: Lista de años disponibles para filtrar.
        :return: Un componente HTML con los filtros.
        """
        return html.Div([
            # Filtro de Años
            html.Div([
                html.Label("Año:"),
                dcc.Dropdown(
                    id="anio",
                    options=[
                        {"label": str(anio), "value": anio} \
                            for anio in anios_disponibles
                    ],
                    value = anios_disponibles[0] \
                            if anios_disponibles else None,
                    style = {"width": "100%"}
                )
            ], style = {"width": "20%", 
                        "display": "inline-block", 
                        "marginRight": "10px"}),

            # Filtro de Granularidad
            html.Div([
                html.Label("Granularidad:"),
                dcc.Dropdown(
                    id="nivel-granularidad",
                    options=[
                        {"label": "Colonia", "value": "colonia"},
                        {"label": "AGEB", "value": "ageb"}
                    ],
                    value="colonia",
                    style={"width": "100%"}
                )
            ], style={"width": "20%", 
                      "display": "inline-block", 
                      "marginRight": "10px"}),

            # Filtro de Métrica
            html.Div([
                html.Label("Métrica:"),
                dcc.Dropdown(
                    id = "metrica",
                    value = None,
                    style = {"width": "100%"}
                )
            ], style={"width": "20%", "display": "inline-block"})
        ], style={"display": "flex", "flexDirection": "row"})

    def get_filtered_data(self,
                          anio: Optional[int],
                          nivel_granularidad: str,
                          metrica: Optional[str],
                          dataframe_key: str) -> gpd.GeoDataFrame:
        """
        Obtiene y retorna los datos filtrados según el año, la granularidad
        y la métrica seleccionada. Aplica procesamiento adicional a través de
        DataProcessor.

        :param anio: Año seleccionado para filtrar los datos.
        :param nivel_granularidad: Nivel de granularidad (p.ej. "colonia", "ageb").
        :param metrica: Métrica seleccionada para el mapa (p.ej. "poblacion").
        :param dataframe_key: Clave para acceder al diccionario de datos self.datos.
        :return: GeoDataFrame procesado y filtrado.
        """
        # Obtiene el DataFrame a partir de la llave especificada
        df: gpd.GeoDataFrame = self.datos.get(dataframe_key, gpd.GeoDataFrame())

        # Si el DataFrame está vacío, retornar un GDF vacío para manejarlo en el callback
        if df.empty:
            return gpd.GeoDataFrame()

        # Filtro por año si existe la columna 'anio' en el DataFrame
        if 'anio' in df.columns and anio is not None:
            df = df[df['anio'] == anio]

        # Procesar datos con DataProcessor (SRP: DataProcessor se encarga de la lógica de transformación)
        return DataProcessor.procesar_datos(
            df=df,
            nivel_granularidad=nivel_granularidad,
            metricas=[metrica] if metrica else []
        )

    def get_available_years(self) -> List[int]:
        """
        Obtiene la lista de años disponibles a partir del DataFrame 'datos_demograficos'.

        :return: Lista de años encontrados en el dataset de datos demográficos.
        """
        # Se asume que 'datos_demograficos' existe en self.datos
        demograficos: gpd.GeoDataFrame = self.datos.get('datos_demograficos', gpd.GeoDataFrame())

        # Retornar lista de años ordenada si existe la columna 'anio'
        if 'anio' in demograficos.columns:
            return sorted(demograficos['anio'].unique())
        return []

    def generate_dashboard(self, category: str) -> html.Div:
        """
        Genera y retorna la estructura de un dashboard para una categoría específica
        (demográfica, edafológica o electoral).

        :param category: Categoría de datos que se desea mostrar en el dashboard.
        :return: Componente HTML con el título y el mapa correspondiente.
        """
        try:
            # Obtenemos años disponibles para mostrar en el dropdown
            anios_disponibles: List[int] = self.get_available_years()

            return html.Div([
                html.H3(f"Rubro: Tablero de {category}"),
                self.create_filter_row(anios_disponibles),
                html.Div(id="nuevo-mapa-interactivo")  # Contenedor donde se inyectará el mapa
            ])
        except Exception as e:
            logger.error(f"Error generando el nuevo dashboard de {category}: {e}")
            return html.Div([html.P("Error al cargar el nuevo dashboard.")])

    def run(self) -> None:
        """
        Inicia el servidor de la aplicación Dash en modo debug.
        """
        self.app.run_server(debug=True)


# Punto de entrada de la aplicación
if __name__ == "__main__":
    dashboard_app = DashboardApp()
    dashboard_app.run()
