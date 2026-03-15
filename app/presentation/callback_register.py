import logging
import random
from typing import Optional, List
import numpy as np
import pandas as pd
from pandas import DataFrame, merge
from dash import Dash, html, dcc, Input, Output, State, ALL
import dash_bootstrap_components as dbc
from app.services.data_service import DataService
from app.domain.domain_models import TableController

from app.domain.domain_models import (
    DashboardFilters,
    MapVisualizationConfig,
    AVAILABLE_COLOR_SCHEMES
)

import plotly.express as px
import plotly.graph_objects as go
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

        # Lazy loading: polígonos se cargan solo cuando se necesitan
        self._poligonos_manzana = None
        self._poligonos_ageb = None
        self._poligonos_colonia = None
        self.data = None  # Dataset activo (se inicializa al navegar a un rubro)

    @property
    def poligonos_manzana(self):
        if self._poligonos_manzana is None:
            self._poligonos_manzana = self.data_service\
                .initialize_dataset(self.table_controller.poligonos_manzana)
        return self._poligonos_manzana

    @property
    def poligonos_ageb(self):
        if self._poligonos_ageb is None:
            self._poligonos_ageb = self.data_service\
                .initialize_dataset(self.table_controller.poligonos_ageb)
        return self._poligonos_ageb

    @property
    def poligonos_colonia(self):
        if self._poligonos_colonia is None:
            self._poligonos_colonia = self.data_service\
                .initialize_dataset(self.table_controller.poligonos_colonia)
        return self._poligonos_colonia
        
    def register_callbacks(self, app: Dash) -> None:
        """
        Registra todos los callbacks en la instancia de Dash.
        """
        self._register_page_callback(app)
        self._register_metrica_callback(app)
        self._register_map_callback(app)
        self._register_categorico_callback(app)
        self._register_capas_callback(app)
        self._register_vulnerabilidad_callback(app)
        self._register_comparador_callback(app)
        self._register_perfil_callback(app)
        self._register_correlaciones_callback(app)
        self._register_riesgo_callback(app)
        self._register_accesibilidad_callback(app)

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

            elif pathname == "/dashboard/vulnerabilidad":
                self._vuln_data = self.data_service\
                    .initialize_dataset(self.table_controller.ambientales)
                return self.page_builder.create_vulnerabilidad_page(
                    self._COMPONENTES_VULNERABILIDAD)

            elif pathname == "/dashboard/comparador":
                self._comparador_data = self.data_service\
                    .initialize_dataset(self.table_controller.ambientales)
                colonias = sorted(
                    self._comparador_data['colonia'].unique())
                return self.page_builder.create_comparador_page(colonias)

            elif pathname == "/dashboard/capas":
                self._capas_indicadores = self.data_service\
                    .initialize_dataset(self.table_controller.ambientales)
                self._capas_infra = self.data_service\
                    .initialize_dataset(self.table_controller.infraestructura)
                self._capas_recursos = self.data_service\
                    .initialize_dataset(self.table_controller.recursos_naturales)

                metricas_base = [
                    {'label': 'Densidad vivienda (viv/ha)',
                     'value': 'densidad_viv_ha'},
                    {'label': 'Área verde por hab. (m²)',
                     'value': 'm2_area_verde_hab'},
                    {'label': 'Viviendas desocupadas (%)',
                     'value': 'pct_viviendas_desocupadas'},
                    {'label': 'Valor del suelo ($/m²)',
                     'value': 'valor_suelo_pesos'},
                    {'label': 'Espacio público por hab. (m²)',
                     'value': 'm2_espacio_pub_hab'},
                    {'label': 'Temperatura nocturna (°C)',
                     'value': 'temp_nocturna_media'},
                    {'label': 'Viviendas con internet (%)',
                     'value': 'pct_viv_internet'},
                    {'label': 'Consumo agua promedio (m³)',
                     'value': 'consumo_agua_prom_m3'},
                    {'label': 'Tasa crecimiento 2010-2020',
                     'value': 'tasa_crecimiento_2010_2020'},
                ]
                cats_infra = sorted(
                    self._capas_infra['subcategoria'].unique())
                cats_rec = sorted(
                    self._capas_recursos['categoria'].unique())
                return self.page_builder.create_capas_page(
                    metricas_base, cats_infra, cats_rec)

            elif pathname == "/dashboard/perfil":
                self._perfil_data = self.data_service\
                    .initialize_dataset(self.table_controller.ambientales)
                colonias = sorted(self._perfil_data['colonia'].unique())
                return self.page_builder.create_perfil_page(colonias)

            elif pathname == "/dashboard/correlaciones":
                self._corr_data = self.data_service\
                    .initialize_dataset(self.table_controller.ambientales)
                return self.page_builder.create_correlaciones_page(
                    self._METRICAS_CORRELACIONES)

            elif pathname == "/dashboard/riesgo":
                self._riesgo_indicadores = self.data_service\
                    .initialize_dataset(self.table_controller.ambientales)
                self._riesgo_infra = self.data_service\
                    .initialize_dataset(self.table_controller.infraestructura)
                return self.page_builder.create_riesgo_page()

            elif pathname == "/dashboard/accesibilidad":
                self._accesibilidad_colonias = self.data_service\
                    .initialize_dataset(self.table_controller.ambientales)
                self._accesibilidad_servicios = self.data_service\
                    .initialize_dataset(self.table_controller.servicios)
                cats = sorted(
                    self._accesibilidad_servicios['categoria'].unique())
                return self.page_builder.create_accesibilidad_page(cats)

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
            infra = self.data_service.initialize_dataset(
                self.table_controller.infraestructura)

            # --- KPIs fila 1: datos generales ---
            pob_total = indicadores['poblacion_2010'].sum()
            n_colonias = len(indicadores)
            # Contar AGEBs y manzanas sin cargar polígonos pesados
            try:
                from sqlalchemy import text as _text
                _engine = self.data_service.loader.connection_manager.get_engine()
                with _engine.connect() as _conn:
                    n_agebs = _conn.execute(_text(
                        'SELECT COUNT(DISTINCT "ID_AGEB") FROM poligonos_manzanas_agebs_colonias'
                    )).scalar() or 0
                    n_manzanas = _conn.execute(_text(
                        'SELECT COUNT(DISTINCT "ID_MANZANA") FROM poligonos_manzanas_agebs_colonias'
                    )).scalar() or 0
            except Exception:
                n_agebs = 154
                n_manzanas = 4813
            media_verde = indicadores['m2_area_verde_hab'].mean()

            kpis = [
                (f"{pob_total:,.0f}", "Habitantes", "Censo 2010"),
                (f"{n_colonias:,}", "Colonias", ""),
                (f"{n_agebs:,}", "AGEBs", ""),
                (f"{n_manzanas:,}", "Manzanas", ""),
                (f"{media_verde:.1f}", "m² verde/hab", "promedio"),
            ]

            # --- KPIs fila 2: indicadores clave ---
            media_internet = indicadores['pct_viv_internet'].mean()
            media_temp = indicadores['temp_nocturna_media'].mean()
            n_infra = len(infra)
            media_desocupadas = indicadores['pct_viviendas_desocupadas'].mean()

            # Calcular vulnerabilidad para el KPI
            try:
                gdf_vuln, _ = self._calcular_indice_vulnerabilidad(indicadores)
                vuln_media = gdf_vuln['score_vulnerabilidad'].mean()
                col_mas_vuln = gdf_vuln.loc[
                    gdf_vuln['score_vulnerabilidad'].idxmax(), 'colonia']
            except Exception:
                vuln_media = 0
                col_mas_vuln = "—"

            kpis += [
                (f"{media_internet:.0f}%", "Internet", "viv. con acceso"),
                (f"{media_temp:.1f}°C", "Temp. nocturna", "media"),
                (f"{n_infra:,}", "Puntos infra.", "15 categorías"),
                (f"{media_desocupadas:.1f}%", "Viv. desocupadas", "promedio"),
                (f"{vuln_media:.0f}/100", "Vulnerabilidad", "score medio"),
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

            # --- Charts extra: mini barras de vulnerabilidad y área verde ---
            extra_charts = []
            try:
                fig_vuln_barras = FiguresGenerator.generar_barras_horizontales(
                    df=gdf_vuln,
                    columna_nombre='colonia',
                    columna_valor='score_vulnerabilidad',
                    titulo='Top 10 colonias más vulnerables',
                )
                if fig_vuln_barras:
                    fig_vuln_barras.update_layout(
                        coloraxis_colorbar=dict(title="Score"),
                        coloraxis=dict(colorscale='YlOrRd'))
                    extra_charts.append(dbc.Col(
                        dcc.Graph(figure=fig_vuln_barras,
                                  config={'displayModeBar': False}),
                        md=6))
            except Exception:
                pass

            fig_verde_barras = FiguresGenerator.generar_barras_horizontales(
                df=indicadores,
                columna_nombre='colonia',
                columna_valor='m2_area_verde_hab',
                titulo='Top 10 colonias por área verde',
            )
            if fig_verde_barras:
                extra_charts.append(dbc.Col(
                    dcc.Graph(figure=fig_verde_barras,
                              config={'displayModeBar': False}),
                    md=6))

            # --- Hallazgos dinámicos enriquecidos ---
            col_max = indicadores.loc[indicadores['densidad_viv_ha'].idxmax()]
            media_dens = indicadores['densidad_viv_ha'].mean()
            uso_dom = edafologicos['USO_SUELO'].value_counts()
            pct_hab = (uso_dom.iloc[0] / len(edafologicos)) * 100

            # Colonia con menos área verde
            col_min_verde = indicadores.loc[
                indicadores['m2_area_verde_hab'].idxmin()]

            # Correlación densidad vs área verde
            corr_dens_verde = indicadores[
                ['densidad_viv_ha', 'm2_area_verde_hab']].corr().iloc[0, 1]

            hallazgos = [
                f"{col_max['colonia']} es la colonia más densa: "
                f"{col_max['densidad_viv_ha']:.0f} viv/ha "
                f"({col_max['densidad_viv_ha'] / media_dens:.1f}x el promedio)",
                f"El {pct_hab:.0f}% del suelo es {uso_dom.index[0].lower()} "
                f"— densidad promedio: {media_dens:.1f} viv/ha",
                f"Área verde: {media_verde:.1f} m²/hab promedio "
                f"— {col_min_verde['colonia']} tiene la menor "
                f"({col_min_verde['m2_area_verde_hab']:.1f} m²/hab)",
                f"Correlación densidad ↔ área verde: R={corr_dens_verde:.2f} "
                f"({'inversa' if corr_dens_verde < 0 else 'directa'})",
                f"Colonia más vulnerable: {col_mas_vuln} "
                f"(score: {vuln_media:.0f}/100 promedio municipal)",
                f"{media_internet:.0f}% de viviendas con internet "
                f"— temp. nocturna media: {media_temp:.1f}°C",
                f"{n_infra:,} puntos de infraestructura mapeados "
                f"en 15 categorías",
            ]

            return self.page_builder.create_inicio_page(
                kpis, fig_mapa, fig_barras, fig_dona, hallazgos,
                extra_charts=extra_charts if extra_charts else None)

        except Exception as e:
            logger.error(f"Error construyendo resumen ejecutivo: {e}")
            return html.Div([
                html.H4("Error cargando resumen ejecutivo"),
                html.P(str(e), className="text-danger"),
            ])

    def _enriquecer_datos_tooltip(self, gdf, metrica):
        """
        Agrega columnas de ranking, desviación vs promedio y semáforo
        para tooltips enriquecidos en mapas coropléticos.
        """
        if metrica not in gdf.columns or gdf[metrica].isna().all():
            return gdf

        # Solo enriquecer métricas numéricas
        if gdf[metrica].dtype.kind not in ('i', 'f'):
            return gdf

        gdf = gdf.copy()
        serie = pd.to_numeric(gdf[metrica], errors='coerce').fillna(0)
        media = serie.mean()
        total = len(gdf)

        # Ranking (1 = valor más alto)
        gdf['_tooltip_ranking'] = serie.rank(
            ascending=False, method='min').astype(int)
        gdf['_tooltip_total'] = total
        gdf['_tooltip_media'] = round(media, 1)

        # Desviación porcentual vs promedio (pre-formateada con signo)
        if media != 0:
            desv = ((serie - media) / media * 100)
            gdf['_tooltip_desviacion'] = desv.apply(
                lambda x: f"+{x:.0f}%" if x >= 0 else f"{x:.0f}%")
        else:
            gdf['_tooltip_desviacion'] = "N/A"

        # Semáforo por terciles
        p33 = serie.quantile(0.33)
        p66 = serie.quantile(0.66)
        gdf['_tooltip_semaforo'] = serie.apply(
            lambda v: "🟢 Bajo" if v <= p33
            else ("🟡 Medio" if v <= p66 else "🔴 Alto"))

        return gdf

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
            # Solo actuar en páginas de rubros con dropdown de métricas
            paginas_validas = {"/dashboard/demograficos", "/dashboard/edafologicos",
                               "/dashboard/electorales", "/dashboard/servicios",
                               "/dashboard/ambientales"}
            if pathname not in paginas_validas:
                return []

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
            if not metrica or not pathname:
                return html.Div("Seleccione una métrica para visualizar el mapa.")

            # Solo actuar en páginas de rubros con mapa coroplético
            paginas_validas = {"/dashboard/demograficos", "/dashboard/edafologicos",
                               "/dashboard/electorales", "/dashboard/servicios",
                               "/dashboard/ambientales"}
            if pathname not in paginas_validas:
                return html.Div()

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
                    # Agregar demograficos a colonias via manzanas (ID_AGEB → ageb)
                    mz = self.poligonos_manzana[['ID_AGEB', 'ID_COLONIA']].drop_duplicates()
                    demo_col = merge(mz, self.data, left_on='ID_AGEB', right_on='ageb', how='inner')
                    # Promediar por colonia
                    num_cols = [c for c in demo_col.columns if demo_col[c].dtype.kind in ('i', 'f')]
                    demo_agg = demo_col.groupby('ID_COLONIA')[num_cols].mean().reset_index()
                    self.gdf_poligonos_data = merge(
                        self.poligonos_colonia, demo_agg,
                        on='ID_COLONIA', how='left')

                elif dataset_key == 'edafologicos':
                    # Agregar edafologicos a colonias via manzanas
                    mz = self.poligonos_manzana[['ID_MANZANA', 'ID_COLONIA']].drop_duplicates()
                    edaf_col = merge(mz, self.data, on='ID_MANZANA', how='inner')
                    self.gdf_poligonos_data = merge(
                        self.poligonos_colonia, edaf_col,
                        on='ID_COLONIA', how='left')

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

            # Enriquecemos con ranking, desviación y semáforo
            gdf_filtrado = self._enriquecer_datos_tooltip(
                gdf_filtrado, metrica)

            # Generamos un título dinámico
            titulo = f"Distribución de {metrica} del {anio} por {gran} en Coyoacán"

            # Columnas de enriquecimiento para tooltip
            enrichment_cols = [
                '_tooltip_ranking', '_tooltip_total', '_tooltip_media',
                '_tooltip_desviacion', '_tooltip_semaforo',
            ]

            # Determinamos columnas para hover (tooltip_cols del rubro + enriquecimiento)
            hover_cols = list(filters.tooltip_cols) + enrichment_cols

            # Seleccionamos aleatoriamente un esquema de color
            esquema_select = random.choice(AVAILABLE_COLOR_SCHEMES)

            # Determinar columna de nombre para hover (usar la que exista)
            nombre_hover = filters.nombre_zona_col
            if nombre_hover and nombre_hover not in gdf_filtrado.columns:
                for fallback in ['NOMBRE_COLONIA', 'ID_COLONIA', 'ID_AGEB', 'ID_MANZANA', 'colonia']:
                    if fallback in gdf_filtrado.columns:
                        nombre_hover = fallback
                        break
                else:
                    nombre_hover = None

            # Creamos la configuración para el mapa
            map_config = MapVisualizationConfig(
                titulo = titulo,
                columna_metrica = metrica,
                titulo_colorbar = dataset_key,
                hover_columns = hover_cols,
                esquema_color = esquema_select,
                nombre_hover = nombre_hover,
            )

            try:
                figura = FiguresGenerator\
                        .generar_mapa_coropletico(gdf_filtrado, map_config)
            except Exception as e:
                logger.warning(f"Error generando mapa para {metrica}: {e}")
                return html.Div(
                    f"No se puede graficar '{metrica}' — "
                    "posiblemente contiene datos no numéricos.",
                    className="text-warning p-3")

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

        elif pathname == "/dashboard/capas":
            return "capas"

        elif pathname == "/dashboard/vulnerabilidad":
            return "vulnerabilidad"

        elif pathname == "/dashboard/comparador":
            return "comparador"

        elif pathname == "/dashboard/perfil":
            return "perfil"

        elif pathname == "/dashboard/correlaciones":
            return "correlaciones"

        elif pathname == "/dashboard/riesgo":
            return "riesgo"

        elif pathname == "/dashboard/accesibilidad":
            return "accesibilidad"

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
            if pathname not in ("/dashboard/infraestructura", "/dashboard/recursos-naturales"):
                return html.Div()

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

    def _register_capas_callback(self, app: Dash) -> None:
        """
        Callback para generar mapa multicapa: coropleta base + overlays.
        """

        @app.callback(
            Output("mapa-capas", "children"),
            [Input("capa-base-metrica", "value"),
             Input("opacidad-base", "value"),
             Input("overlay-infra", "value"),
             Input("overlay-recursos", "value")]
        )
        def actualizar_mapa_capas(metrica_base, opacidad,
                                  cats_infra, cats_rec):
            if not metrica_base:
                return html.Div("Seleccione una métrica base.")

            figura = FiguresGenerator.generar_mapa_multicapa(
                gdf_base=self._capas_indicadores,
                columna_valor=metrica_base,
                columna_nombre='colonia',
                opacidad_base=opacidad or 0.6,
                gdf_infra=self._capas_infra,
                cats_infra=cats_infra or [],
                gdf_recursos=self._capas_recursos,
                cats_recursos=cats_rec or [],
            )

            if figura is None:
                return html.Div("No se pudo generar el mapa.")

            return dcc.Graph(
                figure=figura,
                style={'width': '100%', 'height': '800px'}
            )

    # --- Componentes del índice de vulnerabilidad territorial ---
    # Cada componente: label para UI, variable en datos_indicadores_colonia,
    # peso default (suma = 1.0), invertir (True = más alto → menos vulnerable)
    _COMPONENTES_VULNERABILIDAD = [
        {'label': 'Densidad vivienda',       'variable': 'densidad_viv_ha',
         'peso': 0.10, 'invertir': False},
        {'label': 'Viviendas desocupadas',   'variable': 'pct_viviendas_desocupadas',
         'peso': 0.10, 'invertir': False},
        {'label': 'Área verde por hab.',     'variable': 'm2_area_verde_hab',
         'peso': 0.10, 'invertir': True},
        {'label': 'Espacio público por hab.','variable': 'm2_espacio_pub_hab',
         'peso': 0.08, 'invertir': True},
        {'label': 'Deterioro valor suelo',   'variable': 'deterioro_valor',
         'peso': 0.10, 'invertir': False},
        {'label': 'Calidad vivienda',        'variable': 'indice_calidad_viv_superior',
         'peso': 0.10, 'invertir': True},
        {'label': 'Servicios turismo',       'variable': 'num_servicios_turismo',
         'peso': 0.07, 'invertir': True},
        # --- Nuevos componentes (datos ya en BD) ---
        {'label': 'Isla de calor',           'variable': 'temp_nocturna_media',
         'peso': 0.09, 'invertir': False},
        {'label': 'Brecha digital',          'variable': 'pct_viv_internet',
         'peso': 0.08, 'invertir': True},
        {'label': 'Presión hídrica',         'variable': 'consumo_agua_prom_m3',
         'peso': 0.07, 'invertir': False},
        {'label': 'Rezago espacio público',  'variable': 'rezago_espacio_publico',
         'peso': 0.06, 'invertir': False},
        {'label': 'Acceso educación',        'variable': 'num_escuelas_basicas',
         'peso': 0.05, 'invertir': True},
    ]

    _QUINTIL_LABELS = [
        'Muy baja', 'Baja', 'Media', 'Alta', 'Muy alta'
    ]

    def _calcular_indice_vulnerabilidad(
        self, gdf: pd.DataFrame, pesos_custom: Optional[List[float]] = None
    ) -> pd.DataFrame:
        """
        Calcula el índice de vulnerabilidad territorial por colonia.
        1. Normalización min-max de cada variable
        2. Inversión de variables donde más alto = menos vulnerable
        3. Promedio ponderado → score 0-100
        4. Clasificación en quintiles
        """
        gdf = gdf.copy()
        componentes = self._COMPONENTES_VULNERABILIDAD

        if pesos_custom and len(pesos_custom) == len(componentes):
            total_peso = sum(pesos_custom) or 1
            pesos = [p / total_peso for p in pesos_custom]
        else:
            pesos = [c['peso'] for c in componentes]

        cols_norm = []
        for i, comp in enumerate(componentes):
            col = comp['variable']
            col_norm = f"{col}_norm"
            cols_norm.append(col_norm)

            if col not in gdf.columns:
                gdf[col_norm] = 0.5
                continue

            serie = gdf[col].fillna(0).astype(float)
            vmin, vmax = serie.min(), serie.max()
            if vmax > vmin:
                normalizado = (serie - vmin) / (vmax - vmin)
            else:
                normalizado = pd.Series(0.5, index=gdf.index)

            if comp['invertir']:
                normalizado = 1 - normalizado

            gdf[col_norm] = normalizado

        # Score ponderado 0-100
        gdf['score_vulnerabilidad'] = sum(
            gdf[col_norm] * peso * 100
            for col_norm, peso in zip(cols_norm, pesos)
        )

        # Quintiles
        gdf['quintil_vulnerabilidad'] = pd.qcut(
            gdf['score_vulnerabilidad'], q=5,
            labels=self._QUINTIL_LABELS,
            duplicates='drop',
        )

        # Ranking
        gdf['ranking_vulnerabilidad'] = gdf['score_vulnerabilidad'].rank(
            ascending=False, method='min').astype(int)

        return gdf, cols_norm

    # --- Métricas para correlaciones y perfil ---
    _METRICAS_CORRELACIONES = [
        ('Densidad vivienda (viv/ha)', 'densidad_viv_ha'),
        ('Área verde por hab. (m²)', 'm2_area_verde_hab'),
        ('Espacio público por hab. (m²)', 'm2_espacio_pub_hab'),
        ('Viviendas desocupadas (%)', 'pct_viviendas_desocupadas'),
        ('Valor suelo ($/m²)', 'valor_suelo_pesos'),
        ('Servicios turismo', 'num_servicios_turismo'),
        ('Calidad vivienda', 'indice_calidad_viv_superior'),
        ('Temperatura nocturna (°C)', 'temp_nocturna_media'),
        ('Viviendas con internet (%)', 'pct_viv_internet'),
        ('Consumo agua (m³)', 'consumo_agua_prom_m3'),
        ('Escuelas básicas', 'num_escuelas_basicas'),
        ('Tasa crecimiento 10-20', 'tasa_crecimiento_2010_2020'),
        ('Deterioro valor suelo', 'deterioro_valor'),
        ('Rezago espacio público', 'rezago_espacio_publico'),
        ('Población 2010', 'poblacion_2010'),
        ('UE comerciales', 'ue_comerciales'),
    ]

    _PERFIL_DIMENSIONES = [
        ('Densidad', [
            ('Densidad viv/ha', 'densidad_viv_ha'),
            ('Población 2010', 'poblacion_2010'),
            ('Tasa crecimiento 10-20', 'tasa_crecimiento_2010_2020'),
        ]),
        ('Vivienda', [
            ('Viv. desocupadas (%)', 'pct_viviendas_desocupadas'),
            ('Calidad vivienda', 'indice_calidad_viv_superior'),
            ('Deterioro valor suelo', 'deterioro_valor'),
            ('Valor suelo ($/m²)', 'valor_suelo_pesos'),
        ]),
        ('Medio Ambiente', [
            ('Área verde (m²/hab)', 'm2_area_verde_hab'),
            ('Espacio público (m²/hab)', 'm2_espacio_pub_hab'),
            ('Temp. nocturna (°C)', 'temp_nocturna_media'),
            ('Consumo agua (m³)', 'consumo_agua_prom_m3'),
        ]),
        ('Servicios', [
            ('Escuelas básicas', 'num_escuelas_basicas'),
            ('Servicios turismo', 'num_servicios_turismo'),
            ('UE comerciales', 'ue_comerciales'),
            ('Internet (%)', 'pct_viv_internet'),
        ]),
    ]

    _METRICAS_RADAR = [
        'densidad_viv_ha', 'm2_area_verde_hab', 'm2_espacio_pub_hab',
        'pct_viviendas_desocupadas', 'valor_suelo_pesos',
        'num_servicios_turismo', 'indice_calidad_viv_superior',
        'temp_nocturna_media', 'pct_viv_internet', 'consumo_agua_prom_m3',
    ]
    _LABELS_RADAR = [
        'Densidad', 'Área verde', 'Espacio público',
        'Viv. desocupadas', 'Valor suelo',
        'Turismo', 'Calidad vivienda',
        'Temp. nocturna', 'Internet', 'Consumo agua',
    ]
    _METRICAS_TABLA = [
        ('Población 2010', 'poblacion_2010'),
        ('Densidad (viv/ha)', 'densidad_viv_ha'),
        ('Área verde (m²/hab)', 'm2_area_verde_hab'),
        ('Espacio público (m²/hab)', 'm2_espacio_pub_hab'),
        ('Viv. desocupadas (%)', 'pct_viviendas_desocupadas'),
        ('Valor suelo ($/m²)', 'valor_suelo_pesos'),
        ('Servicios turismo', 'num_servicios_turismo'),
        ('Calidad vivienda', 'cat_calidad_vivienda'),
        ('Urbanismo social', 'cat_urbanismo_social'),
        ('Temp. nocturna (°C)', 'temp_nocturna_media'),
        ('Viviendas con internet (%)', 'pct_viv_internet'),
        ('Consumo agua (m³)', 'consumo_agua_prom_m3'),
        ('Escuelas básicas', 'num_escuelas_basicas'),
        ('Tasa crecimiento 10-20', 'tasa_crecimiento_2010_2020'),
    ]

    def _register_vulnerabilidad_callback(self, app: Dash) -> None:
        """
        Callback para calcular y visualizar el índice de vulnerabilidad.
        Responde al botón recalcular con pesos ajustados por sliders.
        """

        @app.callback(
            [Output("mapa-vulnerabilidad", "children"),
             Output("tabla-ranking-vulnerabilidad", "children"),
             Output("desglose-vulnerabilidad", "children")],
            [Input("btn-recalcular-vuln", "n_clicks")],
            [State({"type": "peso-vuln", "index": ALL}, "value")],
        )
        def actualizar_vulnerabilidad(n_clicks, pesos_slider):
            if not hasattr(self, '_vuln_data') or self._vuln_data is None:
                msg = html.Div("Carga la página de vulnerabilidad primero.")
                return msg, msg, msg

            # Convertir pesos de slider (0-40 enteros) a fracciones
            pesos_custom = None
            if pesos_slider and any(p is not None for p in pesos_slider):
                pesos_custom = [float(p or 0) for p in pesos_slider]

            try:
                gdf_vuln, cols_norm = self._calcular_indice_vulnerabilidad(
                    self._vuln_data, pesos_custom)
            except Exception as e:
                logger.error(f"Error calculando vulnerabilidad: {e}")
                msg = html.Div(f"Error: {e}", className="text-danger")
                return msg, msg, msg

            # --- Mapa ---
            fig = FiguresGenerator.generar_mapa_vulnerabilidad(
                gdf=gdf_vuln,
                columna_score='score_vulnerabilidad',
                columna_quintil='quintil_vulnerabilidad',
                columna_nombre='colonia',
                componentes_cols=cols_norm,
            )
            mapa = (dcc.Graph(figure=fig, style={'width': '100%', 'height': '600px'})
                    if fig else html.Div("No se pudo generar el mapa."))

            # --- Tabla de ranking ---
            ranking = gdf_vuln.sort_values(
                'score_vulnerabilidad', ascending=False
            ).head(20)

            header = [html.Th("#"), html.Th("Colonia"),
                      html.Th("Score"), html.Th("Quintil")]
            rows = []
            for _, row in ranking.iterrows():
                quintil = str(row['quintil_vulnerabilidad'])
                color_badge = {
                    'Muy alta': 'danger', 'Alta': 'warning',
                    'Media': 'info', 'Baja': 'success',
                    'Muy baja': 'success',
                }.get(quintil, 'secondary')
                rows.append(html.Tr([
                    html.Td(row['ranking_vulnerabilidad']),
                    html.Td(html.B(row['colonia'])),
                    html.Td(f"{row['score_vulnerabilidad']:.1f}"),
                    html.Td(dbc.Badge(quintil, color=color_badge)),
                ]))

            tabla = html.Div([
                html.H5("Ranking de vulnerabilidad (Top 20)"),
                dbc.Table(
                    [html.Thead(html.Tr(header)), html.Tbody(rows)],
                    bordered=True, striped=True, hover=True, size="sm",
                    className="mt-2",
                ),
            ])

            # --- Desglose de componentes (barras apiladas top 10) ---
            top10 = gdf_vuln.nlargest(10, 'score_vulnerabilidad')
            componentes = self._COMPONENTES_VULNERABILIDAD

            if pesos_custom:
                total = sum(pesos_custom) or 1
                pesos_frac = [p / total for p in pesos_custom]
            else:
                pesos_frac = [c['peso'] for c in componentes]

            fig_desglose = go.Figure()
            for i, comp in enumerate(componentes):
                col_norm = cols_norm[i]
                if col_norm in top10.columns:
                    valores = top10[col_norm] * pesos_frac[i] * 100
                    fig_desglose.add_trace(go.Bar(
                        y=top10['colonia'],
                        x=valores,
                        name=comp['label'],
                        orientation='h',
                    ))

            fig_desglose.update_layout(
                barmode='stack',
                template='plotly_white',
                title=dict(text='Desglose por componente — Top 10',
                           x=0.5, xanchor='center'),
                margin=dict(r=10, t=40, l=0, b=0),
                height=350,
                xaxis_title='Contribución al score',
                yaxis=dict(autorange='reversed'),
                legend=dict(orientation='h', y=-0.2, xanchor='center', x=0.5,
                            font=dict(size=10)),
            )

            desglose = dcc.Graph(figure=fig_desglose,
                                 config={'displayModeBar': False})

            return mapa, tabla, desglose

    def _register_comparador_callback(self, app: Dash) -> None:
        """
        Callback para comparador de colonias: radar chart + tabla.
        """

        @app.callback(
            [Output("comparador-radar", "children"),
             Output("comparador-tabla", "children")],
            [Input("comparador-colonias", "value")]
        )
        def actualizar_comparador(colonias_sel):
            if not colonias_sel or len(colonias_sel) < 2:
                msg = html.Div("Selecciona al menos 2 colonias.",
                               className="text-muted")
                return msg, msg

            colonias_sel = colonias_sel[:3]
            df = self._comparador_data

            # Radar chart
            fig_radar = FiguresGenerator.generar_radar_comparativo(
                df=df, colonias=colonias_sel,
                metricas=self._METRICAS_RADAR,
                labels=self._LABELS_RADAR)

            radar_div = (dcc.Graph(figure=fig_radar,
                                   config={'displayModeBar': False})
                         if fig_radar
                         else html.Div("Error generando radar."))

            # Tabla comparativa
            header = [html.Th("Indicador")] + [
                html.Th(c, style={"fontSize": "0.85rem"})
                for c in colonias_sel]
            rows = []
            for label, col in self._METRICAS_TABLA:
                cells = [html.Td(html.B(label))]
                for colonia in colonias_sel:
                    row = df[df['colonia'] == colonia]
                    if row.empty or col not in row.columns:
                        cells.append(html.Td("—"))
                    else:
                        val = row[col].values[0]
                        if isinstance(val, float):
                            cells.append(html.Td(f"{val:,.1f}"))
                        else:
                            cells.append(html.Td(str(val)))
                rows.append(html.Tr(cells))

            tabla = dbc.Table(
                [html.Thead(html.Tr(header)),
                 html.Tbody(rows)],
                bordered=True, striped=True, hover=True, size="sm",
                className="mt-3",
            )

            return radar_div, tabla

    # ── PERFIL DE COLONIA ─────────────────────────────────────────
    def _register_perfil_callback(self, app: Dash) -> None:
        @app.callback(
            Output("perfil-contenido", "children"),
            [Input("perfil-colonia-select", "value")]
        )
        def actualizar_perfil(colonia):
            if not colonia or not hasattr(self, '_perfil_data'):
                return html.Div("Selecciona una colonia.", className="text-muted")

            df = self._perfil_data
            row = df[df['colonia'] == colonia]
            if row.empty:
                return html.Div("Colonia no encontrada.", className="text-danger")

            row = row.iloc[0]
            total = len(df)

            # KPI cards con ranking
            kpi_defs = [
                ('densidad_viv_ha', 'Densidad', 'viv/ha'),
                ('m2_area_verde_hab', 'Área verde', 'm²/hab'),
                ('valor_suelo_pesos', 'Valor suelo', '$/m²'),
                ('pct_viv_internet', 'Internet', '%'),
            ]
            kpis = []
            for col, label, unidad in kpi_defs:
                if col in df.columns and pd.notna(row.get(col)):
                    val = row[col]
                    try:
                        val_num = float(val)
                        val_str = f"{val_num:,.1f}"
                    except (ValueError, TypeError):
                        val_str = str(val)
                    rank = int(df[col].rank(ascending=False, method='min')[row.name])
                    kpis.append(dbc.Col(dbc.Card(dbc.CardBody([
                        html.H4(val_str, className="text-primary mb-0"),
                        html.P(f"{label} ({unidad})", className="text-muted mb-0",
                               style={"fontSize": "0.8rem"}),
                        html.Small(f"#{rank} de {total}",
                                   className="text-secondary"),
                    ]), className="text-center shadow-sm",
                        style={"borderRadius": "10px"}), md=3))

            # Radar individual
            fig_radar = FiguresGenerator.generar_radar_comparativo(
                df=df, colonias=[colonia],
                metricas=self._METRICAS_RADAR,
                labels=self._LABELS_RADAR)
            if fig_radar:
                fig_radar.update_layout(
                    title=dict(text=f'Perfil — {colonia}'),
                    height=400)

            # Semáforo por dimensión
            dimension_cards = []
            for dim_nombre, indicadores in self._PERFIL_DIMENSIONES:
                items = []
                for label, col in indicadores:
                    if col not in df.columns:
                        continue
                    val = row.get(col)
                    if pd.isna(val):
                        items.append(html.Li(f"{label}: sin dato",
                                             style={"fontSize": "0.82rem"}))
                        continue
                    serie = df[col].fillna(0)
                    p33, p66 = serie.quantile(0.33), serie.quantile(0.66)
                    semaforo = "🟢" if val <= p33 else ("🟡" if val <= p66 else "🔴")
                    rank = int(serie.rank(ascending=False, method='min')[row.name])
                    items.append(html.Li([
                        html.Span(f"{semaforo} {label}: ",
                                  style={"fontSize": "0.82rem"}),
                        html.B(f"{float(val):,.1f}" if isinstance(val, (int, float)) else str(val),
                               style={"fontSize": "0.82rem"}),
                        html.Span(f"  (#{rank})",
                                  className="text-muted",
                                  style={"fontSize": "0.75rem"}),
                    ]))
                dimension_cards.append(dbc.Col(dbc.Card(dbc.CardBody([
                    html.H6(dim_nombre, className="mb-2"),
                    html.Ul(items, style={"listStyle": "none", "paddingLeft": "0"}),
                ]), className="shadow-sm h-100",
                    style={"borderRadius": "10px"}), md=3))

            return html.Div([
                dbc.Row(kpis, className="mb-3 g-3"),
                dbc.Row([
                    dbc.Col(
                        dcc.Graph(figure=fig_radar,
                                  config={'displayModeBar': False})
                        if fig_radar else html.Div(""),
                        md=6),
                    dbc.Col([
                        html.H5("Categorías", className="mb-2"),
                        html.P([
                            html.Span("Urbanismo social: ",
                                      style={"fontSize": "0.85rem"}),
                            html.B(str(row.get('cat_urbanismo_social', '—'))),
                        ]),
                        html.P([
                            html.Span("Calidad vivienda: ",
                                      style={"fontSize": "0.85rem"}),
                            html.B(str(row.get('cat_calidad_vivienda', '—'))),
                        ]),
                        html.P([
                            html.Span("Concentración equip.: ",
                                      style={"fontSize": "0.85rem"}),
                            html.B(str(row.get('concentracion_equipamiento', '—'))),
                        ]),
                        html.P([
                            html.Span("Zona sísmica: ",
                                      style={"fontSize": "0.85rem"}),
                            html.B(str(row.get('taxonomia_sismica', '—'))),
                        ]),
                    ], md=6),
                ], className="mb-3"),
                html.H5("Indicadores por dimensión", className="mb-2"),
                dbc.Row(dimension_cards, className="g-3"),
            ])

    # ── CORRELACIONES ─────────────────────────────────────────────
    def _register_correlaciones_callback(self, app: Dash) -> None:
        @app.callback(
            [Output("corr-scatter", "children"),
             Output("corr-matriz", "children")],
            [Input("corr-eje-x", "value"),
             Input("corr-eje-y", "value"),
             Input("corr-color", "value")]
        )
        def actualizar_correlaciones(eje_x, eje_y, color_by):
            if not hasattr(self, '_corr_data') or not eje_x or not eje_y:
                msg = html.Div("Selecciona métricas.", className="text-muted")
                return msg, msg

            df = self._corr_data.copy()
            if eje_x not in df.columns or eje_y not in df.columns:
                msg = html.Div("Métrica no disponible.", className="text-danger")
                return msg, msg

            # Scatter plot con trendline
            color_col = color_by if color_by != 'ninguno' and color_by in df.columns else None
            fig_scatter = px.scatter(
                df, x=eje_x, y=eje_y,
                color=color_col,
                hover_name='colonia',
                trendline='ols',
                color_continuous_scale='Viridis' if color_col else None,
                opacity=0.7,
            )

            # Calcular R²
            valid = df[[eje_x, eje_y]].dropna()
            if len(valid) > 2:
                corr = valid[eje_x].corr(valid[eje_y])
                r2_text = f"R = {corr:.3f} (n={len(valid)})"
            else:
                r2_text = "Datos insuficientes"

            x_label = eje_x.replace('_', ' ').title()
            y_label = eje_y.replace('_', ' ').title()
            fig_scatter.update_layout(
                template='plotly_white',
                title=dict(text=f'{x_label} vs {y_label}<br>'
                                f'<span style="font-size:12px">{r2_text}</span>',
                           x=0.5, xanchor='center'),
                height=500,
                margin=dict(r=10, t=70, l=10, b=10),
                xaxis_title=x_label,
                yaxis_title=y_label,
            )

            scatter = dcc.Graph(figure=fig_scatter,
                                config={'displayModeBar': False})

            # Matriz de correlación (top métricas numéricas)
            metric_cols = [col for _, col in self._METRICAS_CORRELACIONES
                          if col in df.columns and df[col].dtype.kind in ('i', 'f')]
            metric_labels = [label for label, col in self._METRICAS_CORRELACIONES
                            if col in metric_cols]
            corr_matrix = df[metric_cols].corr()

            fig_matrix = go.Figure(data=go.Heatmap(
                z=corr_matrix.values,
                x=metric_labels,
                y=metric_labels,
                colorscale='RdBu_r',
                zmin=-1, zmax=1,
                text=np.round(corr_matrix.values, 2),
                texttemplate='%{text}',
                textfont={"size": 8},
            ))
            fig_matrix.update_layout(
                template='plotly_white',
                title=dict(text='Matriz de correlación', x=0.5, xanchor='center'),
                height=500,
                margin=dict(r=10, t=40, l=10, b=10),
                xaxis=dict(tickangle=-45, tickfont=dict(size=8)),
                yaxis=dict(tickfont=dict(size=8)),
            )

            matriz = dcc.Graph(figure=fig_matrix,
                               config={'displayModeBar': False})

            return scatter, matriz

    # ── MAPA DE RIESGO ────────────────────────────────────────────
    def _register_riesgo_callback(self, app: Dash) -> None:
        @app.callback(
            [Output("mapa-riesgo", "children"),
             Output("tabla-riesgo", "children")],
            [Input("btn-calcular-riesgo", "n_clicks")],
            [State("riesgo-componentes", "value")]
        )
        def actualizar_riesgo(n_clicks, componentes):
            if not hasattr(self, '_riesgo_indicadores') or not componentes:
                msg = html.Div("Selecciona componentes y presiona Calcular.",
                               className="text-muted")
                return msg, msg

            import geopandas as _gpd
            gdf = self._riesgo_indicadores.copy()
            infra = self._riesgo_infra

            # Calcular score de riesgo por colonia
            gdf['score_riesgo'] = 0.0
            n_componentes = len(componentes)

            if 'zona_inundacion' in componentes:
                # Contar inundaciones por spatial join con colonias
                inund = infra[infra['subcategoria'] == 'zona_inundacion']
                if not inund.empty and 'geometry' in gdf.columns:
                    try:
                        conteo = _gpd.sjoin(
                            inund.to_crs(gdf.crs),
                            gdf[['colonia', 'geometry']],
                            how='inner', predicate='intersects'
                        ).groupby('colonia').size().rename('n_inundaciones')
                        gdf = gdf.merge(conteo, on='colonia', how='left')
                        gdf['n_inundaciones'] = gdf['n_inundaciones'].fillna(0)
                        vmax = gdf['n_inundaciones'].max()
                        if vmax > 0:
                            gdf['score_riesgo'] += (gdf['n_inundaciones'] / vmax) * (100 / n_componentes)
                    except Exception:
                        gdf['n_inundaciones'] = 0

            if 'accidente_peaton' in componentes:
                acc = infra[infra['subcategoria'] == 'accidente_peaton']
                if not acc.empty and 'geometry' in gdf.columns:
                    try:
                        conteo = _gpd.sjoin(
                            acc.to_crs(gdf.crs),
                            gdf[['colonia', 'geometry']],
                            how='inner', predicate='within'
                        ).groupby('colonia').size().rename('n_accidentes')
                        gdf = gdf.merge(conteo, on='colonia', how='left')
                        gdf['n_accidentes'] = gdf['n_accidentes'].fillna(0)
                        vmax = gdf['n_accidentes'].max()
                        if vmax > 0:
                            gdf['score_riesgo'] += (gdf['n_accidentes'] / vmax) * (100 / n_componentes)
                    except Exception:
                        gdf['n_accidentes'] = 0

            if 'convergencia_riesgos' in componentes:
                conv = infra[infra['subcategoria'] == 'convergencia_riesgos']
                if not conv.empty and 'geometry' in gdf.columns:
                    try:
                        conteo = _gpd.sjoin(
                            conv.to_crs(gdf.crs),
                            gdf[['colonia', 'geometry']],
                            how='inner', predicate='intersects'
                        ).groupby('colonia').size().rename('n_convergencia')
                        gdf = gdf.merge(conteo, on='colonia', how='left')
                        gdf['n_convergencia'] = gdf['n_convergencia'].fillna(0)
                        vmax = gdf['n_convergencia'].max()
                        if vmax > 0:
                            gdf['score_riesgo'] += (gdf['n_convergencia'] / vmax) * (100 / n_componentes)
                    except Exception:
                        gdf['n_convergencia'] = 0

            if 'vulnerabilidad' in componentes:
                # Usar el score de vulnerabilidad ya calculado
                try:
                    gdf_vuln, _ = self._calcular_indice_vulnerabilidad(gdf)
                    gdf['score_riesgo'] += gdf_vuln['score_vulnerabilidad'] * (1 / n_componentes)
                except Exception:
                    pass

            gdf['score_riesgo'] = gdf['score_riesgo'].round(1)
            gdf['ranking_riesgo'] = gdf['score_riesgo'].rank(
                ascending=False, method='min').astype(int)

            # Mapa
            fig = px.choropleth_mapbox(
                data_frame=gdf,
                geojson=gdf.__geo_interface__,
                locations=gdf.index,
                color='score_riesgo',
                mapbox_style='open-street-map',
                zoom=12,
                center={"lat": 19.332608, "lon": -99.143209},
                color_continuous_scale='YlOrRd',
                range_color=[0, gdf['score_riesgo'].quantile(0.95)],
                opacity=0.8,
                hover_name='colonia',
            )
            hover_parts = ['<b>%{hovertext}</b><br>',
                           '<b>Score riesgo:</b> %{z:.1f}<br>']
            fig.update_traces(
                hovertemplate=''.join(hover_parts) + '<extra></extra>',
                marker_line_color='white', marker_line_width=0.5)
            fig.update_layout(
                template='plotly_white',
                title=dict(text='Riesgo Territorial — Coyoacán',
                           x=0.5, y=0.95, xanchor='center', yanchor='top'),
                margin=dict(r=0, t=60, l=0, b=0),
                height=550,
                coloraxis_colorbar=dict(title="Riesgo", len=0.7, thickness=15),
            )
            mapa = dcc.Graph(figure=fig, config={'displayModeBar': False})

            # Tabla ranking top 20
            top20 = gdf.nlargest(20, 'score_riesgo')
            header = [html.Th("#"), html.Th("Colonia"), html.Th("Score")]
            # Agregar columnas de conteo si existen
            count_cols = []
            for col_name, col_label in [('n_inundaciones', 'Inund.'),
                                         ('n_accidentes', 'Accid.'),
                                         ('n_convergencia', 'Conv.')]:
                if col_name in gdf.columns:
                    header.append(html.Th(col_label))
                    count_cols.append(col_name)

            rows = []
            for _, r in top20.iterrows():
                cells = [
                    html.Td(r['ranking_riesgo']),
                    html.Td(html.B(r['colonia'])),
                    html.Td(f"{r['score_riesgo']:.1f}"),
                ]
                for cc in count_cols:
                    cells.append(html.Td(int(r.get(cc, 0))))
                rows.append(html.Tr(cells))

            tabla = html.Div([
                html.H5("Colonias con mayor riesgo (Top 20)"),
                dbc.Table(
                    [html.Thead(html.Tr(header)), html.Tbody(rows)],
                    bordered=True, striped=True, hover=True, size="sm",
                    className="mt-2",
                ),
            ])

            return mapa, tabla

    # ── ACCESIBILIDAD ─────────────────────────────────────────────
    _ACCESIBILIDAD_UMBRALES = [
        (400, 'Alta (< 400m)', '#2ca02c'),
        (800, 'Media (400-800m)', '#ff7f0e'),
        (1200, 'Baja (800-1200m)', '#d62728'),
        (float('inf'), 'Desierto (> 1200m)', '#7f7f7f'),
    ]

    def _register_accesibilidad_callback(self, app: Dash) -> None:
        @app.callback(
            [Output("mapa-accesibilidad", "children"),
             Output("resumen-accesibilidad", "children")],
            [Input("btn-calcular-accesibilidad", "n_clicks")],
            [State("accesibilidad-categoria", "value")]
        )
        def actualizar_accesibilidad(n_clicks, categoria):
            if (not hasattr(self, '_accesibilidad_colonias')
                    or not categoria):
                msg = html.Div("Selecciona una categoría y presiona Calcular.",
                               className="text-muted")
                return msg, msg

            import geopandas as _gpd
            from shapely.ops import nearest_points

            gdf_col = self._accesibilidad_colonias.copy()
            servicios = self._accesibilidad_servicios

            # Filtrar servicios por categoría
            serv_cat = servicios[servicios['categoria'] == categoria].copy()
            if serv_cat.empty:
                msg = html.Div(f"No hay servicios de tipo '{categoria}'.",
                               className="text-warning")
                return msg, msg

            # Reproyectar a UTM 14N para distancias en metros
            gdf_utm = gdf_col.to_crs("EPSG:32614")
            serv_utm = serv_cat.to_crs("EPSG:32614")

            # Centroide de cada colonia
            centroides = gdf_utm.geometry.centroid

            # Union de todos los puntos de servicio para nearest lookup
            from shapely.ops import unary_union
            serv_union = unary_union(serv_utm.geometry)

            # Calcular distancia mínima por colonia
            distancias = []
            for centroid in centroides:
                nearest = nearest_points(centroid, serv_union)[1]
                dist = centroid.distance(nearest)
                distancias.append(round(dist, 0))

            gdf_col['distancia_servicio_m'] = distancias

            # Contar servicios dentro de 800m por colonia
            conteos = []
            for centroid in centroides:
                buffer = centroid.buffer(800)
                n = serv_utm[serv_utm.geometry.within(buffer)].shape[0]
                conteos.append(n)
            gdf_col['servicios_800m'] = conteos

            # Clasificar accesibilidad
            def clasificar(dist):
                for umbral, label, _ in self._ACCESIBILIDAD_UMBRALES:
                    if dist <= umbral:
                        return label
                return 'Desierto (> 1200m)'

            gdf_col['accesibilidad'] = gdf_col['distancia_servicio_m'].apply(
                clasificar)

            # Mapa coroplético por distancia
            fig = px.choropleth_mapbox(
                data_frame=gdf_col,
                geojson=gdf_col.__geo_interface__,
                locations=gdf_col.index,
                color='distancia_servicio_m',
                mapbox_style='open-street-map',
                zoom=12,
                center={"lat": 19.332608, "lon": -99.143209},
                color_continuous_scale='RdYlGn_r',
                opacity=0.8,
                hover_name='colonia',
                custom_data=['accesibilidad', 'servicios_800m'],
            )
            cat_label = categoria.replace('_', ' ').title()
            fig.update_traces(
                hovertemplate=(
                    '<b>%{hovertext}</b><br>'
                    f'Distancia a {cat_label}: %{{z:,.0f}}m<br>'
                    'Accesibilidad: %{customdata[0]}<br>'
                    f'{cat_label} en 800m: %{{customdata[1]}}'
                    '<extra></extra>'
                ),
                marker_line_color='white', marker_line_width=0.5,
            )
            fig.update_layout(
                template='plotly_white',
                title=dict(
                    text=f'Accesibilidad a {cat_label} — Coyoacán',
                    x=0.5, y=0.95, xanchor='center', yanchor='top'),
                margin=dict(r=0, t=60, l=0, b=0),
                height=550,
                coloraxis_colorbar=dict(
                    title="Distancia (m)", len=0.7, thickness=15),
            )

            mapa = dcc.Graph(figure=fig, config={'displayModeBar': False})

            # Resumen: conteo por clasificación + tabla desiertos
            conteo_acc = gdf_col['accesibilidad'].value_counts()
            resumen_items = []
            for _, label, color in self._ACCESIBILIDAD_UMBRALES:
                n = conteo_acc.get(label, 0)
                pct = n / len(gdf_col) * 100
                resumen_items.append(html.Div([
                    html.Span(f"{label}: ", style={
                        "color": color, "fontWeight": "bold",
                        "fontSize": "0.9rem"}),
                    html.Span(f"{n} colonias ({pct:.0f}%)",
                              style={"fontSize": "0.9rem"}),
                ]))

            # Tabla de desiertos urbanos
            desiertos = gdf_col[
                gdf_col['distancia_servicio_m'] > 1200
            ].sort_values('distancia_servicio_m', ascending=False)

            if not desiertos.empty:
                rows_desert = []
                for _, r in desiertos.head(15).iterrows():
                    rows_desert.append(html.Tr([
                        html.Td(html.B(r['colonia'])),
                        html.Td(f"{r['distancia_servicio_m']:,.0f}m"),
                        html.Td(r.get('servicios_800m', 0)),
                    ]))
                tabla_desiertos = html.Div([
                    html.H6(f"Desiertos urbanos de {cat_label} "
                            f"({len(desiertos)} colonias)", className="mt-3"),
                    dbc.Table([
                        html.Thead(html.Tr([
                            html.Th("Colonia"), html.Th("Distancia"),
                            html.Th(f"{cat_label} en 800m")])),
                        html.Tbody(rows_desert),
                    ], bordered=True, striped=True, hover=True, size="sm"),
                ])
            else:
                tabla_desiertos = html.Div(
                    html.P(f"No hay desiertos urbanos de {cat_label}.",
                           className="text-success mt-3"))

            # Stats generales
            media_dist = gdf_col['distancia_servicio_m'].mean()
            mediana_dist = gdf_col['distancia_servicio_m'].median()

            resumen = html.Div([
                dbc.Row([
                    dbc.Col([
                        html.H5(f"Accesibilidad a {cat_label}"),
                        *resumen_items,
                        html.P(f"Distancia media: {media_dist:,.0f}m | "
                               f"Mediana: {mediana_dist:,.0f}m",
                               className="text-muted mt-2",
                               style={"fontSize": "0.85rem"}),
                    ], md=5),
                    dbc.Col(tabla_desiertos, md=7),
                ]),
            ])

            return mapa, resumen
