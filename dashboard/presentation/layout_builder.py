from dash import html, dcc
from typing import List
import dash_bootstrap_components as dbc

class LayoutBuilder:
    """
    Clase encargada de construir el layout principal de la aplicación:
    - Barra lateral (sidebar)
    - Contenedor del contenido (page-content)
    """

    def create_layout(self) -> html.Div:
        """
        Construye la estructura principal del layout (sidebar + content).
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
            html.H2("Coyoacán", className = "display-4"),
            html.Hr(),
            html.P("Análisis de Datos Georeferenciados", className="lead"),
            dbc.Nav(
                [
                    dbc.NavLink("Inicio", href="/", 
                    active="exact"),
                    dbc.NavLink("Demográficos", href="/demograficos", active="exact"),
                    dbc.NavLink("Edafológicos", href="/edafologicos", active="exact"),
                    dbc.NavLink("Electorales", href="/electorales", active="exact"),
                    dbc.NavLink("Servicios", href="/servicios", active="exact"),
                    dbc.NavLink("Ambientales", href="/ambientales", active="exact")
                ],
                vertical=True,
                pills=True,
            ),
        ], style = sidebar_style)

        content = html.Div(id="page-content", style=content_style)

        return html.Div([
            dcc.Location(id="url"),
            sidebar,
            content
        ])

    def create_demograficos_page(self, anios: List[int]) -> html.Div:
        return html.Div([
            html.H3("Rubro: Tablero de Demográfico"),
            self.create_filter_row(anios),
            html.Div(id="mapa-plotly")
        ])

    def create_edafologicos_page(self, anios: List[int]) -> html.Div:
        return html.Div([
            html.H3("Rubro: Tablero de Edafológico"),
            self.create_filter_row(anios),
            html.Div(id="mapa-plotly")
        ])

    def create_electorales_page(self, anios: List[int]) -> html.Div:
        return html.Div([
            html.H3("Rubro: Tablero Electoral"),
            self.create_filter_row(anios),
            html.Div(id="mapa-plotly")
        ])

    def create_servicios_page(self, anios: List[int]) -> html.Div:
        return html.Div([
            html.H3("Rubro: Tablero de Servicios"),
            self.create_filter_row(anios),
            html.Div(id="mapa-plotly")
        ])

    def create_ambientales_page(self, anios: List[int]) -> html.Div:
        return html.Div([
            html.H3("Rubro: Tablero Ambiental"),
            self.create_filter_row(anios),
            html.Div(id="mapa-plotly")
        ])

    def create_filter_row(self, anios: List[int]) -> html.Div:
        """
        Crea los dropdowns de Año, Granularidad y 
            Métrica en una sola fila.
        """
        return html.Div([
            html.Div([
                html.Label("Año:"),
                dcc.Dropdown(
                    id = "anio",
                    options = [{"label": str(a), "value": a} \
                               for a in anios],
                    value = anios[0] if anios else None
                )
            ], style = {"width": "20%", 
                      "display": "inline-block", 
                      "marginRight": "10px"}),

            html.Div([
                html.Label("Granularidad:"),
                dcc.Dropdown(
                    id = "granularidad",
                    options = [
                        {"label": "Manzana", 
                         "value": "manzana"},
                        {"label": "AGEB", 
                         "value": "ageb"},
                        {"label": "Colonia", 
                         "value": "colonia"}
                    ],
                    value = "manzana"
                )
            ], style={"width": "20%", 
                      "display": "inline-block", 
                      "marginRight": "10px"}),

            html.Div([
                html.Label("Métrica:"),
                dcc.Dropdown(
                    id = "metrica",
                    value = None 
                )
            ], style = {"width": "20%", 
                        "display": "inline-block"})
        ], style = {"display": "flex", 
                  "flexDirection": "row"})
