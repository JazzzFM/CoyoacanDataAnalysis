import logging
import random
from typing import Optional
from pandas import DataFrame, merge
from dash import Dash, html, dcc, Input, Output
from app.services.data_service import DataService
from app.domain.domain_models import TableController

from app.domain.domain_models import (
    DashboardFilters,
    MapVisualizationConfig,
    AVAILABLE_COLOR_SCHEMES
)

from app.figures.figures_utils import FiguresGenerator
from app.presentation.layout_builder import LayoutBuilder

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
        self._register_categorico_callback(app)

    def _register_page_callback(self, app: Dash) -> None:
        """
        Callback para renderizar el contenido de la página según la ruta.
        """

        @app.callback(
            Output("page-content", "children"),
            [Input("url", "pathname")]
        )
        def render_page_content(pathname: str) -> html.Div:
            if pathname in ("/dashboard/", "/dashboard"):
                return self._build_inicio_page()
            
            elif pathname == "/dashboard/demograficos":
                self.data = self.data_service\
                     .initialize_dataset(self.table_controller.demograficos)
                anios = self.data_service\
                    .obtener_anios_disponibles(self.data)
                return self.page_builder.create_demograficos_page(anios)

            elif pathname == "/dashboard/edafologicos":
                self.data = self.data_service\
                    .initialize_dataset(self.table_controller.edafologicos)
                anios = self.data_service\
                    .obtener_anios_disponibles(self.data)
                return self.page_builder.create_edafologicos_page(anios)

            elif pathname == "/dashboard/electorales":
                self.data = self.data_service\
                    .initialize_dataset(self.table_controller.electorales)
                    
                anios = self.data_service\
                    .obtener_anios_disponibles(self.data)

                page = self.page_builder.create_electorales_page(anios)
                return page
            
            elif pathname == "/dashboard/servicios":
                self.data = self.data_service\
                    .initialize_dataset(self.table_controller.servicios)
                
                anios = self.data_service\
                    .obtener_anios_disponibles(self.data)
                
                page = self.page_builder.create_servicios_page(anios)
                return page
            
            elif pathname == "/dashboard/ambientales":
                self.data = self.data_service\
                    .initialize_dataset(self.table_controller.ambientales)

                anios = self.data_service\
                    .obtener_anios_disponibles(self.data)

                page = self.page_builder.create_ambientales_page(anios)
                return page

            elif pathname == "/dashboard/infraestructura":
                self.data = self.data_service\
                    .initialize_dataset(self.table_controller.infraestructura)
                cats = sorted(self.data['subcategoria'].unique())
                return self.page_builder.create_infraestructura_page(cats)

            elif pathname == "/dashboard/recursos-naturales":
                self.data = self.data_service\
                    .initialize_dataset(self.table_controller.recursos_naturales)
                cats = sorted(self.data['categoria'].unique())
                return self.page_builder.create_recursos_naturales_page(cats)

            else:
                return html.Div([
                    html.H1("404: No encontrado", className = "text-danger"),
                    html.Hr(),
                    html.P(f"La ruta {pathname} no fue reconocida."),
                ])

    def _build_inicio_page(self) -> html.Div:
        """
        Construye la página de resumen ejecutivo cargando datos y generando
        KPIs, figuras y hallazgos dinámicamente.
        """
        try:
            indicadores = self.data_service.initialize_dataset(
                self.table_controller.ambientales)
            edafologicos = self.data_service.initialize_dataset(
                self.table_controller.edafologicos)

            # --- KPIs ---
            pob_total = indicadores['poblacion_2010'].sum()
            n_colonias = len(indicadores)
            n_agebs = self.poligonos_ageb['ID_AGEB'].nunique()
            n_manzanas = self.poligonos_manzana['ID_MANZANA'].nunique()

            kpis = [
                (f"{pob_total:,.0f}", "Habitantes", "Censo 2010"),
                (f"{n_colonias:,}", "Colonias", ""),
                (f"{n_agebs:,}", "AGEBs", ""),
                (f"{n_manzanas:,}", "Manzanas", ""),
                ("7", "Rubros", "de análisis"),
            ]

            # --- Figuras ---
            fig_mapa = FiguresGenerator.generar_mapa_resumen(
                gdf=indicadores,
                columna_valor='densidad_viv_ha',
                columna_nombre='colonia',
                titulo='Densidad de vivienda por colonia (viv/ha)',
            )

            fig_barras = FiguresGenerator.generar_barras_horizontales(
                df=indicadores,
                columna_nombre='colonia',
                columna_valor='densidad_viv_ha',
                titulo='Top 10 colonias por densidad',
            )

            fig_dona = FiguresGenerator.generar_dona(
                df=edafologicos,
                columna_categoria='USO_SUELO',
                titulo='Distribución de uso de suelo',
            )

            # --- Hallazgos dinámicos ---
            col_max = indicadores.loc[indicadores['densidad_viv_ha'].idxmax()]
            media_dens = indicadores['densidad_viv_ha'].mean()
            uso_dom = edafologicos['USO_SUELO'].value_counts()
            pct_hab = (uso_dom.iloc[0] / len(edafologicos)) * 100
            media_verde = indicadores['m2_area_verde_hab'].mean()

            hallazgos = [
                f"{col_max['colonia']} es la colonia más densa: "
                f"{col_max['densidad_viv_ha']:.0f} viv/ha "
                f"({col_max['densidad_viv_ha'] / media_dens:.1f}x el promedio)",
                f"Densidad promedio municipal: {media_dens:.1f} viv/ha",
                f"El {pct_hab:.0f}% del suelo es {uso_dom.index[0].lower()}",
                f"Promedio de área verde: {media_verde:.1f} m² por habitante",
                f"Población total (2010): {pob_total:,.0f} habitantes "
                f"en {n_colonias} colonias",
            ]

            return self.page_builder.create_inicio_page(
                kpis, fig_mapa, fig_barras, fig_dona, hallazgos)

        except Exception as e:
            logger.error(f"Error construyendo resumen ejecutivo: {e}")
            return html.Div([
                html.H4("Error cargando resumen ejecutivo"),
                html.P(str(e), className="text-danger"),
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

            # Datasets con geometria propia (no requieren merge con poligonos)
            if dataset_key in ("electorales", "servicios", "ambientales"):
                self.gdf_poligonos_data = self.data

            elif gran == 'manzana':
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
        if pathname == "/dashboard/demograficos":
            return "demograficos"
        
        elif pathname == "/dashboard/edafologicos":
            return "edafologicos"
        
        elif pathname == "/dashboard/electorales":
            return "electorales"
        
        elif pathname == "/dashboard/servicios":
            return "servicios"
        
        elif pathname == "/dashboard/ambientales":
            return "ambientales"

        elif pathname == "/dashboard/infraestructura":
            return "infraestructura"

        elif pathname == "/dashboard/recursos-naturales":
            return "recursos_naturales"

        return "demograficos"

    def _register_categorico_callback(self, app: Dash) -> None:
        """
        Callback para generar mapas categoricos (infraestructura y recursos naturales).
        Usa dropdown multi-select de categorias en vez de año/granularidad/métrica.
        """

        @app.callback(
            Output("mapa-categorico", "children"),
            [Input("cat-infra", "value"),
             Input("cat-recursos", "value"),
             Input("url", "pathname")]
        )
        def actualizar_mapa_categorico(cats_infra, cats_recursos, pathname):
            dataset_key = self._parse_dataset_key(pathname)

            if dataset_key == "infraestructura":
                categorias_sel = cats_infra or []
                columna_cat = 'subcategoria'
                titulo = "Infraestructura en Coyoacán"
            elif dataset_key == "recursos_naturales":
                categorias_sel = cats_recursos or []
                columna_cat = 'categoria'
                titulo = "Recursos Naturales en Coyoacán"
            else:
                return html.Div()

            if not categorias_sel:
                return html.Div("Seleccione al menos una categoría.")

            figura = FiguresGenerator.generar_mapa_categorico(
                gdf=self.data,
                columna_cat=columna_cat,
                columna_nombre='nombre',
                titulo=titulo,
                categorias_visibles=categorias_sel,
            )

            if figura is None:
                return html.Div("No se encontraron datos para las categorías seleccionadas.")

            return dcc.Graph(
                figure=figura,
                style={'width': '100%', 'height': '800px'}
            )
