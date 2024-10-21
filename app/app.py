# app/app.py

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
import plotly.express as px
import pandas as pd
from sqlalchemy import create_engine
import geopandas as gpd
import os
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask import Flask, redirect, request, url_for

# Configuración de Flask
server = Flask(__name__)
server.secret_key = os.getenv('SECRET_KEY', 'supersecretkey')  # Define SECRET_KEY en .env

# Configuración de Flask-Login
login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = '/login'

# Configurar conexión a la base de datos
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_DB = os.getenv('POSTGRES_DB')
DB_HOST = os.getenv('DB_HOST')
POSTGRES_PORT = os.getenv('POSTGRES_PORT')

engine = create_engine(f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DB_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}')

# Definir el modelo de usuario
from users import User  # Asegúrate de que users.py está en la carpeta app

class UserModel(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id};"
    user = pd.read_sql(query, engine)
    if not user.empty:
        return UserModel(user.iloc[0]['id'], user.iloc[0]['username'], user.iloc[0]['password'])
    return None

# Crear la aplicación Dash con Flask server
app = dash.Dash(__name__, 
                external_stylesheets = [dbc.themes.CYBORG],
                server = server, 
                suppress_callback_exceptions=True)

# Definir la página de login
@server.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}';"
        user = pd.read_sql(query, engine)
        if not user.empty:
            user_obj = UserModel(user.iloc[0]['id'], user.iloc[0]['username'], user.iloc[0]['password'])
            login_user(user_obj)
            return redirect('/')

    return '''
        <form method="post">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <input type="submit" value="Login">
        </form>
    '''

# Definir la página de logout
@server.route('/logout')
def logout():
    logout_user()
    return redirect('/login')

# Definir el layout principal con autenticación
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# Definir la página principal
@app.callback(
    dash.dependencies.Output('page-content', 'children'),
    [dash.dependencies.Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/login':
        return redirect('/login')
    if not current_user.is_authenticated:
        return redirect('/login')
    # Contenido del dashboard
    limites = gpd.read_postgis("SELECT * FROM limites_alcaldias", engine, geom_col='geom')
    manzanas = gpd.read_postgis("SELECT * FROM manzanas", engine, geom_col='geom')
    uso_suelo = gpd.read_postgis("SELECT * FROM uso_suelo", engine, geom_col='geom')

    demografia = pd.read_sql("SELECT * FROM demografia", engine)
    economia = pd.read_sql("SELECT * FROM economia", engine)

    fig_demografia = px.bar(economia, x='sector', y='ingresos', title='Ingresos por Sector Económico en Coyoacán')
    fig_accesibilidad = px.choropleth_mapbox(
        manzanas,
        geojson=manzanas.geometry.__geo_interface__,
        locations=manzanas.index,
        color='distancia_min_hospital',
        mapbox_style="carto-positron",
        zoom=12,
        center={"lat": 19.3467, "lon": -99.1617},
        opacity=0.5,
        title='Distancia Mínima a Hospitales por Manzana'
    )

    return dbc.Container([
    dbc.NavbarSimple(
        brand="Coyoacán Data Analysis",
        brand_href="#",
        color="dark",
        dark=True,
        fluid=True,
        children=[
            dbc.NavItem(dbc.NavLink("Logout", href="/logout"))
        ]
    ),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Ingresos por Sector Económico"),
                dbc.CardBody([
                    dcc.Graph(figure=fig_demografia)
                ])
            ], color="light", inverse=False)
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Distancia a Hospitales"),
                dbc.CardBody([
                    dcc.Graph(figure=fig_accesibilidad)
                ])
            ], color="light", inverse=False)
        ], width=6),
    ]),
    # Agrega más filas y columnas con componentes modernos
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Otras Visualizaciones"),
                dbc.CardBody([
                    # Inserta más gráficos aquí
                ])
            ], color="light", inverse=False)
        ], width=12),
    ]),
    dbc.Row([
        dbc.Col([
            html.Footer(
                "© 2024 Coyoacán Data Analysis",
                style={'textAlign': 'center', 
                       'padding': '10px', 
                       'backgroundColor': '#343a40', 
                       'color': 'white'}
            )
        ], width=12)
     ])
    ], fluid=True)

if __name__ == '__main__':
    app.run_server(debug=False, host='0.0.0.0', port=8050)
