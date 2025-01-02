import logging
import random
from typing import Optional

from dash import Dash, html, dcc, Input, Output
from services.data_service import DataService

from domain.domain_models import (
    DashboardFilters,
    MapVisualizationConfig,
    AVAILABLE_COLOR_SCHEMES
)

from figures.figures_utils import FiguresGenerator
from presentation.layout_builder import LayoutBuilder

logger = logging.getLogger(__name__)


class CallbackRegister:
    """
    Clase encargada de registrar todos los callbacks de la aplicación.
    - Navegación entre páginas
    - Actualización de dropdown de métricas
    - Generación de mapas
    """

    def __init__(self, data_service: DataService, page_builder: LayoutBuilder) -> None:
        """
        :param data_service: Servicio de negocio para obtener y filtrar datos.
        :param page_factory: Crea los layouts de las distintas páginas.
        """
        self.data_service = data_service
        self.page_builder = page_builder

    def register_callbacks(self, app: Dash) -> None:
        """
        Registra todos los callbacks en la instancia de Dash.
        """
        self._register_page_callback(app)
        self._register_metrica_callback(app)
        self._register_map_callback(app)

    def _register_page_callback(self, app: Dash) -> None:
        """
        Callback para renderizar el contenido de la página según la ruta.
        """

        @app.callback(
            Output("page-content", "children"),
            [Input("url", "pathname")]
        )
        def render_page_content(pathname: str) -> html.Div:
            if pathname == "/":
                return html.Div("¡Bienvenido a la página de inicio!")
            
            elif pathname == "/demografia":
                anios = self.data_service\
                    .obtener_anios_disponibles("demograficos")
                return self.page_builder.create_demograficos_page(anios)
            
            elif pathname == "/edafologia":
                anios = self.data_service\
                    .obtener_anios_disponibles("edafologicos")
                return self.page_builder.create_edafologicos_page(anios)
            
            elif pathname == "/electorales":
                anios = self.data_service\
                    .obtener_anios_disponibles("electorales")
                return self.page_builder.create_electorales_page(anios)
            
            elif pathname == "/servicios":
                anios = self.data_service\
                    .obtener_anios_disponibles("servicios")
                return self.page_builder.create_servicios_page(anios)
            
            elif pathname == "/ambientales":
                anios = self.data_service\
                    .obtener_anios_disponibles("ambientales")
                return self.page_builder.create_ambientales_page(anios)
            
            else:
                return html.Div([
                    html.H1("404: No encontrado", className = "text-danger"),
                    html.Hr(),
                    html.P(f"La ruta {pathname} no fue reconocida."),
                ])

    def _register_metrica_callback(self, app: Dash) -> None:
        """
        Callback para actualizar el dropdown de 'metrica' según el 
        dataset (pathname), año y granularidad.
        """

        @app.callback(
            Output("metrica", "options"),
            [Input("anio", "value"), 
             Input("granularidad", "value"), 
             Input("url", "pathname")]
        )
        def actualizar_opciones_metrica(anio: Optional[int], gran: str, pathname: str):
            dataset_key = self._parse_dataset_key(pathname)
            gdf = self.data_service.datasets.get(dataset_key)
            if gdf is None or gdf.empty:
                logger.warning(f"Dataset '{dataset_key}' vacío o inexistente.")
                return []

            if anio and "anio" in gdf.columns:
                gdf = gdf[gdf["anio"] == anio]

            # Filtrar columnas numéricas
            numeric_cols = [
                c for c in gdf.columns
                if c not in ("geometry", "anio") and \
                    gdf[c].dtype.kind in ["i", "f"]
            ]
            return [{"label": c.replace("_", " ").capitalize(), "value": c}\
                     for c in numeric_cols]

    def _register_map_callback(self, app: Dash) -> None:
        """
        Callback para generar el mapa coroplético en base a los valores 
        seleccionados.
        """

        @app.callback(
            Output("mapa-demograficos", "children"),
            [Input("anio", "value"), 
             Input("granularidad", "value"), 
             Input("metrica", "value"), 
             Input("url", "pathname")]
        )
        def actualizar_mapa(anio: Optional[int], gran: str, metrica: Optional[str], pathname: str):
            if not metrica:
                return html.Div("Seleccione una métrica para visualizar el mapa.")

            dataset_key = self._parse_dataset_key(pathname)

            # Llenamos un objeto DashboardFilters
            filters = DashboardFilters(
                type_data = dataset_key,
                anio = anio,
                granularidad = gran,
                metrica = metrica
            )

            gdf_filtrado = self.data_service.obtener_datos_filtrados(dataset_key, filters)

            if gdf_filtrado.empty:
                return html.Div("No se encontraron datos para los filtros seleccionados.")

            # Generamos un título dinámico
            titulo = f"Distribución de {metrica} del {anio} por {gran} en Coyoacán"

            # Determinamos columnas para hover
            hover_cols = [
                c for c in gdf_filtrado.columns
                if c not in ("geometry", "anio") and gdf_filtrado[c].dtype.kind in ["i", "f"]
            ]
            # Agregamos cualquier columna adicional definida en el dataclass
            hover_cols += filters.tooltip_cols

            # Seleccionamos aleatoriamente un esquema de color
            esquema_color_seleccionado = random.choice(AVAILABLE_COLOR_SCHEMES)

            # Creamos la configuración para el mapa
            map_config = MapVisualizationConfig(
                titulo = titulo,
                columna_metrica = metrica,
                titulo_colorbar = dataset_key,
                hover_columns = hover_cols,
                esquema_color = esquema_color_seleccionado
            )

            figura = FiguresGenerator.generar_mapa_coropletico(gdf_filtrado, map_config)
            if figura is None:
                return html.Div("Mapa no disponible (datos vacíos).")

            return dcc.Graph(figure = figura, 
                             style = {'width': '100%', 
                                      'height': '800px'})

    def _parse_dataset_key(self, pathname: str) -> str:
        """
        Determina la clave del dataset según el pathname.
        """
        # Ajusta el parseo de rutas según tu lógica
        if pathname == "/demografia":
            return "demograficos"
        
        elif pathname == "/edafologia":
            return "edafologicos"
        
        elif pathname == "/electorales":
            return "electorales"
        
        elif pathname == "/servicios":
            return "servicios"
        
        elif pathname == "/ambientales":
            return "ambientales"
        
        return "demograficos"
