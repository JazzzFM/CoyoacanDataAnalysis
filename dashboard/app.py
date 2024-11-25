# dashboard_app.py

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, dcc, html
from data_loader import load_static_data, validate_geometries
from data_processor import DataProcessor
from figures_utils import create_choropleth
import geopandas as gpd

class DashboardApp:
    def __init__(self):
        # Cargar y preparar los datos
        try:
            self.datos = load_static_data()
            # Validar geometrías
            for gdf_name, gdf in self.datos.items():
                if gdf.empty:
                    print(f"[ERROR] La tabla '{gdf_name}' está vacía o no contiene datos válidos.")
                else:
                    print(f"[INFO] Tabla '{gdf_name}' cargada con las siguientes columnas: {list(gdf.columns)}")
                    validate_geometries(gdf)
            print("[INFO] Datos cargados y validados exitosamente.")
        except Exception as e:
            raise RuntimeError(f"Error al cargar o validar datos: {e}")

        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
        self.layout_app()
        self.add_callbacks()

    def layout_app(self):
        # Estilos para la barra lateral y el contenido
        SIDEBAR_STYLE = {
            "position": "fixed",
            "top": 0,
            "left": 0,
            "bottom": 0,
            "width": "16rem",
            "padding": "2rem 1rem",
            "background-color": "#f8f9fa",
            "overflow-y": "auto",
        }

        CONTENT_STYLE = {
            "margin-left": "18rem",
            "margin-right": "2rem",
            "padding": "2rem 1rem",
        }

        sidebar = html.Div(
            [
                html.H2("Coyoacán", className="display-4"),
                html.Hr(),
                html.P("Análisis de Datos Georeferenciados", className="lead"),
                dbc.Nav(
                    [
                        dbc.NavLink("Parámetros", href="/", active="exact"),
                        dbc.NavLink("Demográficos", href="/page-1", active="exact"),
                        dbc.NavLink("Edafológicos", href="/page-2", active="exact"),
                        dbc.NavLink("Económicos", href="/page-3", active="exact"),
                        dbc.NavLink("Electorales", href="/page-4", active="exact"),
                        dbc.NavLink("Ambientales", href="/page-5", active="exact")
                    ],
                    vertical=True,
                    pills=True,
                ),
            ],
            style=SIDEBAR_STYLE,
        )

        content = html.Div(id="page-content", style=CONTENT_STYLE)

        self.app.layout = html.Div([dcc.Location(id="url"), sidebar, content])

    def add_callbacks(self):
        @self.app.callback(Output("page-content", "children"), [Input("url", "pathname")])
        def render_page_content(pathname):
            if pathname == "/":
                return html.P("Esta es la página de inicio del dashboard de Coyoacán. ¡Bienvenido!")
            elif pathname == "/page-1":
                return self.create_demographic_dashboard()
            elif pathname == "/page-2":
                return html.P("Esta es la página de análisis edafológico.")
            # Si el usuario intenta acceder a una página no definida
            return html.Div(
                [
                    html.H1("404: No encontrado", className="text-danger"),
                    html.Hr(),
                    html.P(f"El pathname {pathname} no fue reconocido..."),
                ],
                className="p-3 bg-light rounded-3",
            )

        @self.app.callback(
            Output("mapa-interactivo", "figure"),
            [Input("anio", "value"),
             Input("nivel-granularidad", "value"),
             Input("metrica", "value")]
        )
        def actualizar_mapa(anio, nivel_granularidad, metrica):
            try:
                datos_procesados = self.get_filtered_data(anio, nivel_granularidad, metrica)
                if datos_procesados.empty:
                    return create_choropleth(gpd.GeoDataFrame(), None, f"No hay datos disponibles para el año {anio}", nivel_granularidad)
                # Crear el mapa interactivo
                fig = create_choropleth(
                    gdf=datos_procesados,
                    metric_column=metrica,
                    title=f"{metrica.capitalize()} por {nivel_granularidad.capitalize()} - {anio}",
                    nivel_granularidad=nivel_granularidad
                )
                fig.update_layout(margin={"r": 0, "t": 50, "l": 0, "b": 0})
                return fig
            except Exception as e:
                print(f"[CALLBACK ERROR] Error al actualizar el mapa: {e}")
                return create_choropleth(gpd.GeoDataFrame(), None, "Error al generar el mapa", nivel_granularidad)

    # Nueva función para crear el dashboard demográfico
    def create_demographic_dashboard(self):
        # Obtener las métricas y años disponibles
        metricas_disponibles = self.get_metric_options()
        anios_disponibles = self.get_available_years()

        return html.Div([
            html.H3("Dashboard Demográfico"),
            self.create_filter_row(metricas_disponibles, anios_disponibles),
            # Contenedor para el mapa
            dcc.Graph(id="mapa-interactivo")
        ])

    # Nueva función para crear la fila de filtros
    def create_filter_row(self, metricas_disponibles, anios_disponibles):
        return html.Div([
            # Selector de año
            html.Div([
                html.Label("Año:"),
                dcc.Dropdown(
                    id="anio",
                    options=[{"label": str(anio), "value": anio} for anio in anios_disponibles],
                    value=anios_disponibles[0],  # Valor por defecto
                    style={"width": "100%"}
                )
            ], style={"width": "20%", "display": "inline-block", "verticalAlign": "top", "marginRight": "10px"}),

            # Selector de nivel de granularidad
            html.Div([
                html.Label("Nivel de Granularidad:"),
                dcc.Dropdown(
                    id="nivel-granularidad",
                    options=[
                        {"label": "Manzana", "value": "manzana"},
                        {"label": "Colonia", "value": "colonia"},
                        {"label": "AGEB", "value": "ageb"}
                    ],
                    value="colonia",
                    style={"width": "100%"}
                )
            ], style={"width": "20%", "display": "inline-block", "verticalAlign": "top", "marginRight": "10px"}),

            # Selector de métrica
            html.Div([
                html.Label("Métrica:"),
                dcc.Dropdown(
                    id="metrica",
                    options=[{"label": metrica.capitalize(), "value": metrica} for metrica in metricas_disponibles],
                    value="pob_total",
                    style={"width": "100%"}
                )
            ], style={"width": "20%", "display": "inline-block", "verticalAlign": "top"})
        ], style={"display": "flex", "flexDirection": "row"})

    # Nueva función para obtener las métricas disponibles
    def get_metric_options(self):
        # Puedes obtener dinámicamente las métricas disponibles a partir de tus datos
        # Aquí las definimos estáticamente por simplicidad
        return ["pob_total", "densidad_pob_total", "densidad_hombres", "densidad_mujeres", "dependencia_infantil", "relacion_genero"]

    # Nueva función para obtener los años disponibles
    def get_available_years(self):
        anios_disponibles = set()
        for df in self.datos.values():
            if 'anio' in df.columns:
                anios_disponibles.update(df['anio'].unique())
        anios_disponibles = sorted(anios_disponibles)
        return anios_disponibles

    # Nueva función para obtener y filtrar los datos
    def get_filtered_data(self, anio, nivel_granularidad, metrica):
        df = self.datos.get(nivel_granularidad, None)
        if df is None or df.empty:
            print(f"[ERROR] No se encontraron datos para '{nivel_granularidad}'.")
            return gpd.GeoDataFrame()

        # Filtrar por año si la columna 'anio' está presente
        if 'anio' in df.columns:
            df = df[df['anio'] == anio]
            if df.empty:
                print(f"[INFO] No hay datos disponibles para el año {anio} y el nivel de granularidad '{nivel_granularidad}'.")
                return gpd.GeoDataFrame()
        else:
            print(f"[WARNING] La columna 'anio' no está presente en los datos para '{nivel_granularidad}'.")

        print(f"[INFO] Generando datos para año {anio}, nivel de granularidad {nivel_granularidad}, métrica {metrica}.")

        # Procesar datos según el nivel de granularidad
        datos_procesados = DataProcessor.procesar_datos(
            df=df,
            nivel_granularidad=nivel_granularidad,
            metricas=[metrica]
        )

        return datos_procesados

    def run(self):
        self.app.run_server(debug=True)

if __name__ == "__main__":
    dashboard_app = DashboardApp()
    dashboard_app.run()
