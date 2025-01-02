import geopandas as gpd
import folium
from shapely.geometry import Point, Polygon
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

# Cargar archivos shapefile de manzanas y uso de suelo
manzanas_gdf = gpd.read_file("data/manzanas/090030001m.shp")
uso_suelo_gdf = gpd.read_file("data/uso_suelo/uso-de-suelo.shp")

# Realizar la unión espacial para asignar uso de suelo a cada manzana
gdf_union = gpd.sjoin(manzanas_gdf, uso_suelo_gdf, how="left", predicate="intersects")
uso_suelo_por_manzana = gdf_union.groupby(['IDENTIFICA', 'us_dscr']).size().reset_index(name='counts')
idx_max = uso_suelo_por_manzana.groupby('IDENTIFICA')['counts'].idxmax()
uso_suelo_predominante = uso_suelo_por_manzana.loc[idx_max]
manzanas_gdf = manzanas_gdf.merge(uso_suelo_predominante[['IDENTIFICA', 'us_dscr']], on="IDENTIFICA", how="left")
manzanas_gdf['us_dscr'] = manzanas_gdf['us_dscr'].fillna('Sin Datos')

# Calcular el centro del mapa para enfocar Coyoacán
centro_lat = manzanas_gdf.geometry.centroid.y.mean()
centro_lon = manzanas_gdf.geometry.centroid.x.mean()

# Crear una paleta de colores para cada tipo de uso de suelo
tipos_uso_suelo = manzanas_gdf['us_dscr'].unique()
colores = ['#4e41cc', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#ffff33', '#a65628', '#f781bf', '#999999']
color_dict = dict(zip(tipos_uso_suelo, colores[:len(tipos_uso_suelo)]))

# Crear el mapa en Folium
m = folium.Map(location=[centro_lat, centro_lon], zoom_start=13)

# Función para definir el estilo de cada manzana según el uso de suelo
def style_function(feature):
    uso = feature['properties']['us_dscr']
    return {
        'fillColor': color_dict.get(uso, 'gray'),
        'color': 'black',
        'weight': 0.5,
        'fillOpacity': 0.7,
    }

# Añadir las manzanas con su uso de suelo al mapa
folium.GeoJson(
    manzanas_gdf,
    style_function=style_function,
    tooltip=folium.GeoJsonTooltip(fields=['us_dscr'], aliases=['Uso de Suelo:'])
).add_to(m)

# Generar la leyenda
def generate_legend_html(color_dict):
    html = '<div style="position: fixed; bottom: 50px; left: 50px; width: 300px; background-color: white; border:2px solid grey; z-index:9999; font-size:12px;">'
    html += '<b>Usos de Suelo</b><br>'
    for uso, color in color_dict.items():
        html += f'<i style="background:{color};width:12px;height:12px;float:left;margin-right:8px;"></i>{uso}<br>'
    html += '</div>'
    return html

legend_html = generate_legend_html(color_dict)
m.get_root().html.add_child(folium.Element(legend_html))

# Guardar el mapa temporalmente
m.save('mapa_uso_suelo_coyoacan_manzanas.html')

