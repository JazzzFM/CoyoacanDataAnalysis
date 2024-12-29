# layout.py

"""
Contiene la construcción del layout de Dash, sin callbacks.
Separa la parte visual de la parte lógica (callbacks).
"""

import dash_bootstrap_components as dbc
from dash import html, dcc

def create_sidebar() -> html.Div:
    """
    Construye la barra lateral con enlaces de navegación.
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

    return html.Div([
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

def create_content() -> html.Div:
    """
    Contenedor principal donde se inyectan las páginas dinámicas.
    """
    content_style = {
        "margin-left": "18rem",
        "margin-right": "2rem",
        "padding": "2rem 1rem",
    }
    return html.Div(id="page-content", style=content_style)

def create_layout() -> html.Div:
    """
    Devuelve el layout completo (sidebar + content + dcc.Location).
    """
    return html.Div([
        dcc.Location(id="url"),
        create_sidebar(),
        create_content()
    ])
