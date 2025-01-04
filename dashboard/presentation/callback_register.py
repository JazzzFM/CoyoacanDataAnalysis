import logging
import random
from typing import Optional
from pandas import DataFrame, merge
from dash import Dash, html, dcc, Input, Output
from services.data_service import DataService
from domain.domain_models import TableController

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

    def __init__(self, 
                 table_controller: TableController,
                 data_service: DataService, 
                 page_builder: LayoutBuilder) -> None:
        """
        :param data_service: Servicio de negocio para obtener y filtrar datos.
        :param page_factory: Crea los layouts de las distintas páginas.
        """
        self.table_controller = table_controller
        self.data_service = data_service
        self.page_builder = page_builder

        self.poligonos_manzana = self.data_service\
            .initialize_dataset(self.table_controller.poligonos_manzana)

        self.poligonos_ageb = self.data_service\
            .initialize_dataset(self.table_controller.poligonos_ageb)

        self.poligonos_colonia = self.data_service\
            .initialize_dataset(self.table_controller.poligonos_colonia)
        
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
            
            elif pathname == "/demograficos":
                self.data = self.data_service\
                     .initialize_dataset(self.table_controller.demograficos)
                print(f"data: {self.data.columns}")
                anios = self.data_service\
                    .obtener_anios_disponibles(self.data)
                print(f"anios : {anios}")
                page = self.page_builder\
                    .create_demograficos_page(anios)
                
                return page
            
            elif pathname == "/edafologicos":
                self.data = self.data_service\
                    .initialize_dataset(self.table_controller\
                                        .edafologicos)
                
                print(f"data: {self.data.columns}")
                anios = self.data_service\
                    .obtener_anios_disponibles(self.data)
                
                print(f"anios : {anios}")

                page = self.page_builder\
                    .create_edafologicos_page(anios)
                return page

            elif pathname == "/electorales":
                self.data = self.data_service\
                    .initialize_dataset(self.table_controller.electorales)
                    
                anios = self.data_service\
                    .obtener_anios_disponibles(self.data)

                page = self.page_builder.create_electorales_page(anios)
                return page
            
            elif pathname == "/servicios":
                self.data = self.data_service\
                    .initialize_dataset(self.table_controller.servicios)
                
                anios = self.data_service\
                    .obtener_anios_disponibles(self.data)
                
                page = self.page_builder.create_servicios_page(anios)
                return page
            
            elif pathname == "/ambientales":
                self.data = self.data_service\
                    .initialize_dataset(self.table_controller.ambientales)
            
                anios = self.data_service\
                    .obtener_anios_disponibles(self.data)
                
                page = self.page_builder.create_ambientales_page(anios)
                return page
            
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
            gdf = self.data

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
            Output("mapa-plotly", "children"),
            [Input("anio", "value"), 
             Input("granularidad", "value"), 
             Input("metrica", "value"), 
             Input("url", "pathname")]
        )
        def actualizar_mapa(anio: Optional[int], gran: str, metrica: Optional[str], pathname: str):
            if not metrica:
                return html.Div("Seleccione una métrica para visualizar el mapa.")

            dataset_key = self._parse_dataset_key(pathname)

            if gran == 'manzana':

                if dataset_key == "demograficos":
                    self.gdf_poligonos_data = merge(
                        self.poligonos_manzana, 
                        self.data,
                        left_on = ['ID_AGEB'],
                        right_on = ['ageb'], 
                        how = 'left')
                    
                elif dataset_key == 'edafologicos':
                    self.gdf_poligonos_data = merge(
                        self.poligonos_manzana, 
                        self.data,
                        left_on = ['ID_MANZANA', 'GEOM_MANZANA'],
                        right_on = ['ID_MANZANA', 'GEOM_MANZANA'], 
                        how = 'left')
                
            elif gran == 'colonia':
                if dataset_key == "demograficos":
                    self.gdf_poligonos_data = merge(
                        self.poligonos_colonia, 
                        self.data,
                        left_on = ['ID_AGEB'],
                        right_on = ['ageb'], 
                        how = 'left')
                    
                elif dataset_key == 'edafologicos':
                    self.gdf_poligonos_data = merge(
                        self.poligonos_colonia, 
                        self.data,
                        left_on = ['ID_MANZANA', 'GEOM_MANZANA'],
                        right_on = ['ID_MANZANA', 'GEOM_MANZANA'],
                        how = 'left')
                    
            elif gran == 'ageb':
                if dataset_key == "demograficos":
                    self.gdf_poligonos_data = merge(
                        self.poligonos_ageb, 
                        self.data,
                        left_on = ['ID_AGEB'],
                        right_on = ['ageb'], 
                        how = 'left')
                    
                elif dataset_key == "edafologicos":
                    self.gdf_poligonos_data = merge(
                        self.poligonos_manzana, 
                        self.data,
                        left_on = ['ID_MANZANA'],
                        right_on = ['ID_MANZANA'], 
                        how = 'left')
            
            print("#########---->")
            print(f"delf.gdf_poligonos_data: {self.gdf_poligonos_data.columns}")
            print(self.gdf_poligonos_data)
            print("<----#########")

            # Llenamos un objeto DashboardFilters
            filters = DashboardFilters(
                type_data = dataset_key,
                anio = anio,
                granularidad = gran,
                metrica = metrica
            )


            gdf_filtrado = self.data_service\
                .obtener_datos_filtrados(dataset_key, 
                    gdf = self.gdf_poligonos_data,
                    filters = filters)

            if gdf_filtrado.empty:
                return html.Div("No se encontraron datos para los filtros seleccionados.")

            # Generamos un título dinámico
            titulo = f"Distribución de {metrica} del {anio} por {gran} en Coyoacán"

            # Determinamos columnas para hover
            hover_cols = [
                c for c in gdf_filtrado.columns
                if c not in ("geometry",
                             "GEOM_MANZANA",
                             "GEOM_AGEB",
                             "GEOM_COLONIA"
                             "anio") and\
                    gdf_filtrado[c].dtype.kind in ["i", "f"]
            ]
            # Agregamos cualquier columna adicional definida en el dataclass
            hover_cols += filters.tooltip_cols

            # Seleccionamos aleatoriamente un esquema de color
            esquema_select = random.choice(AVAILABLE_COLOR_SCHEMES)

            # Creamos la configuración para el mapa
            map_config = MapVisualizationConfig(
                titulo = titulo,
                columna_metrica = metrica,
                titulo_colorbar = dataset_key,
                hover_columns = hover_cols,
                esquema_color = esquema_select
            )

            figura = FiguresGenerator\
                    .generar_mapa_coropletico(gdf_filtrado, map_config)
            
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
        if pathname == "/demograficos":
            return "demograficos"
        
        elif pathname == "/edafologicos":
            return "edafologicos"
        
        elif pathname == "/electorales":
            return "electorales"
        
        elif pathname == "/servicios":
            return "servicios"
        
        elif pathname == "/ambientales":
            return "ambientales"
        
        return "demograficos"
