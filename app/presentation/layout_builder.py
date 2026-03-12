from dash import html, dcc
from typing import List, Tuple
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

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
                    dbc.NavLink("Inicio", href="/dashboard/",
                    active="exact"),
                    dbc.NavLink("Demográficos", href="/dashboard/demograficos", active="exact"),
                    dbc.NavLink("Edafológicos", href="/dashboard/edafologicos", active="exact"),
                    dbc.NavLink("Electorales", href="/dashboard/electorales", active="exact"),
                    dbc.NavLink("Servicios", href="/dashboard/servicios", active="exact"),
                    dbc.NavLink("Ambientales", href="/dashboard/ambientales", active="exact"),
                    dbc.NavLink("Infraestructura", href="/dashboard/infraestructura", active="exact"),
                    dbc.NavLink("Recursos Naturales", href="/dashboard/recursos-naturales", active="exact"),
                    html.Hr(),
                    dbc.NavLink("Vulnerabilidad", href="/dashboard/vulnerabilidad", active="exact"),
                    dbc.NavLink("Capas", href="/dashboard/capas", active="exact"),
                    dbc.NavLink("Comparador", href="/dashboard/comparador", active="exact"),
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

    def _create_kpi_card(self, valor: str, titulo: str, subtitulo: str = "") -> dbc.Card:
        """
        Crea una card de KPI con valor destacado, título y subtítulo opcional.
        """
        return dbc.Card(
            dbc.CardBody([
                html.H3(valor, className="text-primary mb-0",
                         style={"fontWeight": "bold", "fontSize": "1.6rem"}),
                html.P(titulo, className="text-muted mb-0",
                       style={"fontSize": "0.85rem"}),
                html.Small(subtitulo, className="text-muted") if subtitulo else None,
            ]),
            className="text-center shadow-sm h-100",
            style={"borderRadius": "10px"},
        )

    def create_inicio_page(
        self,
        kpis: List[Tuple[str, str, str]],
        fig_mapa: go.Figure,
        fig_barras: go.Figure,
        fig_dona: go.Figure,
        hallazgos: List[str],
    ) -> html.Div:
        """
        Construye la página de resumen ejecutivo con KPIs, mapa overview,
        charts y hallazgos clave.
        """
        kpi_cards = dbc.Row(
            [dbc.Col(self._create_kpi_card(v, t, s), md=True)
             for v, t, s in kpis],
            className="mb-4 g-3",
        )

        charts_row = dbc.Row([
            dbc.Col(
                dcc.Graph(figure=fig_mapa,
                          config={'displayModeBar': False}),
                md=7,
            ),
            dbc.Col([
                dcc.Graph(figure=fig_barras,
                          config={'displayModeBar': False}),
                dcc.Graph(figure=fig_dona,
                          config={'displayModeBar': False}),
            ], md=5),
        ], className="mb-4")

        hallazgos_card = dbc.Card(
            dbc.CardBody([
                html.H5("Hallazgos clave", className="mb-3"),
                html.Ul([html.Li(h, className="mb-1") for h in hallazgos]),
            ]),
            className="shadow-sm",
            style={"borderRadius": "10px"},
        )

        return html.Div([
            html.H3("Coyoacán — Resumen Ejecutivo", className="mb-1"),
            html.P("Análisis territorial integral de la alcaldía",
                   className="text-muted mb-3"),
            html.Hr(),
            kpi_cards,
            charts_row,
            hallazgos_card,
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

    def create_comparador_page(self, colonias: List[str]) -> html.Div:
        """
        Construye la página del comparador de colonias con dropdown
        multi-select, radar chart y tabla comparativa.
        """
        return html.Div([
            html.H3("Comparador de Colonias"),
            html.P("Selecciona 2-3 colonias para comparar sus indicadores",
                   className="text-muted mb-3"),
            dcc.Dropdown(
                id="comparador-colonias",
                options=[{'label': c, 'value': c} for c in colonias],
                value=colonias[:2] if len(colonias) >= 2 else colonias,
                multi=True,
                placeholder="Selecciona colonias...",
                style={"marginBottom": "20px"},
            ),
            dbc.Row([
                dbc.Col(html.Div(id="comparador-radar"), md=6),
                dbc.Col(html.Div(id="comparador-tabla"), md=6),
            ]),
        ])

    def create_capas_page(
        self,
        metricas_base: List[dict],
        capas_infra: List[str],
        capas_recursos: List[str],
    ) -> html.Div:
        """
        Construye la página de capas superpuestas con controles para
        capa base (coropleta) y overlays (infraestructura/recursos).
        """
        control_panel = dbc.Card(dbc.CardBody([
            html.H6("Capa base (coropleta)", className="mb-2"),
            dcc.RadioItems(
                id="capa-base-metrica",
                options=metricas_base,
                value=metricas_base[0]['value'],
                labelStyle={'display': 'block', 'marginBottom': '4px',
                            'fontSize': '0.85rem'},
            ),
            html.Hr(),
            html.H6("Opacidad base", className="mb-2"),
            dcc.Slider(
                id="opacidad-base", min=0.1, max=1.0, value=0.6, step=0.1,
                marks={0.1: '10%', 0.5: '50%', 1.0: '100%'},
            ),
            html.Hr(),
            html.H6("Infraestructura", className="mb-2"),
            dcc.Checklist(
                id="overlay-infra",
                options=[{'label': c.replace('_', ' ').title(), 'value': c}
                         for c in capas_infra],
                value=[],
                labelStyle={'display': 'block', 'marginBottom': '4px',
                            'fontSize': '0.85rem'},
            ),
            html.Hr(),
            html.H6("Recursos Naturales", className="mb-2"),
            dcc.Checklist(
                id="overlay-recursos",
                options=[{'label': c.replace('_', ' ').title(), 'value': c}
                         for c in capas_recursos],
                value=[],
                labelStyle={'display': 'block', 'marginBottom': '4px',
                            'fontSize': '0.85rem'},
            ),
        ]), className="shadow-sm", style={"borderRadius": "10px"})

        return html.Div([
            html.H3("Capas Superpuestas"),
            html.P("Combina la coropleta base con capas de puntos",
                   className="text-muted mb-3"),
            dbc.Row([
                dbc.Col(control_panel, md=3),
                dbc.Col(html.Div(id="mapa-capas"), md=9),
            ]),
        ])

    def create_vulnerabilidad_page(self, componentes: List[dict]) -> html.Div:
        """
        Construye la página del índice de vulnerabilidad territorial con
        mapa coroplético, tabla de ranking y panel de desglose por componentes.
        componentes: lista de dicts con 'label', 'variable', 'peso', 'invertir'
        """
        pesos_panel = dbc.Card(dbc.CardBody([
            html.H6("Ponderación de componentes", className="mb-3"),
            *[
                html.Div([
                    html.Div([
                        html.Span(c['label'], style={"fontSize": "0.82rem"}),
                        html.Span(
                            f"{int(c['peso'] * 100)}%",
                            className="text-muted",
                            style={"fontSize": "0.78rem", "float": "right"},
                        ),
                    ]),
                    dcc.Slider(
                        id={"type": "peso-vuln", "index": i},
                        min=0, max=40, value=int(c['peso'] * 100), step=5,
                        marks={0: '0', 20: '20', 40: '40'},
                        tooltip={"placement": "bottom", "always_visible": False},
                    ),
                ], className="mb-2")
                for i, c in enumerate(componentes)
            ],
            html.Hr(),
            dbc.Button("Recalcular", id="btn-recalcular-vuln",
                       color="primary", size="sm", className="w-100"),
        ]), className="shadow-sm", style={"borderRadius": "10px"})

        return html.Div([
            html.H3("Índice de Vulnerabilidad Territorial"),
            html.P("Score compuesto 0-100 por colonia — quintiles de vulnerabilidad",
                   className="text-muted mb-3"),
            dbc.Row([
                dbc.Col(pesos_panel, md=3),
                dbc.Col([
                    html.Div(id="mapa-vulnerabilidad"),
                    html.Div(id="desglose-vulnerabilidad", className="mt-3"),
                ], md=9),
            ]),
            html.Hr(),
            html.Div(id="tabla-ranking-vulnerabilidad"),
        ])

    def create_infraestructura_page(self, categorias: List[str]) -> html.Div:
        return html.Div([
            html.H3("Rubro: Infraestructura"),
            self._create_category_filter(categorias, "cat-infra"),
            html.Div(id="mapa-categorico")
        ])

    def create_recursos_naturales_page(self, categorias: List[str]) -> html.Div:
        return html.Div([
            html.H3("Rubro: Recursos Naturales"),
            self._create_category_filter(categorias, "cat-recursos"),
            html.Div(id="mapa-categorico")
        ])

    def _create_category_filter(self, categorias: List[str], dropdown_id: str) -> html.Div:
        opciones = [
            {"label": c.replace('_', ' ').title(), "value": c}
            for c in categorias
        ]
        return html.Div([
            html.Div([
                html.Label("Categorías:"),
                dcc.Dropdown(
                    id=dropdown_id,
                    options=opciones,
                    value=[c["value"] for c in opciones],
                    multi=True
                )
            ], style={"width": "50%", "display": "inline-block"})
        ], style={"display": "flex", "flexDirection": "row", "marginBottom": "10px"})

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
