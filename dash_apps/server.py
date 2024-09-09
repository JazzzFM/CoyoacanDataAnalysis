# import built-in Python packages
import os

# import third party packages
from dash import Dash, html, Output, Input, ctx, ALL
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import dash_leaflet.express as dlx

# set app parameters
if os.name == "nt":
    # running on Windows
    ROOT = "/".join(os.path.realpath(__file__).split("\\")[:-1])
else:
    # assume running on Linux
    ROOT = "/".join(os.path.realpath(__file__).split("/")[:-1])

THEME_URL = dbc.themes.LUX
THEME_NAME = "lux"  # must be a dbc theme name, lowercase
DBC_CSS = ("https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.2/dbc.min.css")
app = Dash(
    __name__,
    external_stylesheets=[THEME_URL, DBC_CSS],
    suppress_callback_exceptions=True
)

# define app layout major components
navbar = dbc.Navbar([
    # Use row and col to control vertical alignment of logo / brand
    dbc.Row([
        dbc.Col(
            dbc.NavbarBrand("Leaflet Test", className="ms-2 text-white fs-2"),
            width={"size": 3},
            style={"marginLeft": 30}
        ),
    ], align="center"),
], color="primary")

map_page = dbc.Container([
    dbc.Container([
        dbc.Checklist(
            options=[
                {"label": "Place of Birth", "value": "birth"},
                {"label": "Place of Death", "value": "death"},
            ],
            value=["birth"],
            id="place-options",
            inline=True,
            className="mb-2",
        ),
    ], fluid=True),
    dbc.Container(id="map-container", fluid=True)
], fluid=True)

app.layout = html.Div([
    navbar,
    dbc.Tabs([
        dbc.Tab(
            dbc.Card(dbc.CardBody(map_page), style={"border": "none"}),
            label="Map Filter",
            activeTabClassName="fw-bold fst-italic",
            tabClassName="fs-5",
        ),
    ]),

    dbc.Modal("Hello", is_open=False, id="bio-modal"),
])


# return leaflet map so it renders properly when app is started
@app.callback(
    Output("map-container", "children"),
    Input("place-options", "value"),
)
def draw_map(_):
    markers = [{
        "lat": 0,
        "lon": 0,
        "name": "marker0",
        # "id": {"type": "marker-click", "index": 0}
    }]
    markers = dlx.dicts_to_geojson([{**c, **dict(tooltip=c['name'])} for c in markers])
    children = [dl.TileLayer(), dl.GeoJSON(id="geojson_layer", data=markers, cluster=True)]  # zoomToBoundsOnClick=True
    return dl.Map(children, center=[0, 0], zoom=6, style={"height": "78vh", "width": "96vw"}, id="map")


@app.callback(
    Output("bio-modal", "is_open"),
    # Input({"type": "marker-click", "index": ALL}, "clickData"),
    Input("geojson_layer", "clickData"),
    prevent_initial_call=True,
)
def show_modal(click_data):
    print(click_data)
    if click_data is None:
        raise PreventUpdate
        # print(ctx.triggered_id)
    return True


if __name__ == '__main__':
    app.run(debug=True)
