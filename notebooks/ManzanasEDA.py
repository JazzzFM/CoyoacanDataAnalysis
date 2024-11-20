#!/usr/bin/env python
# coding: utf-8

# In[21]:


import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import folium
import pandas as pd
from shapely.geometry import Point
print("Versión de GeoPandas:", gpd.__version__)


# In[14]:


manzanas_shp = '../data/manzanas/090030001m.shp'
gdf_manzanas = gpd.read_file(manzanas_shp)


# In[16]:


coyoacan_polygon = gpd.read_file('../data/limites/poligonos_alcaldias_cdmx.shp')
coyoacan_polygon = coyoacan_polygon[coyoacan_polygon['NOMGEO'] == 'Coyoacán']


# In[17]:


shapefile_path = '../data/uso_suelo/uso-de-suelo.shp'
gdf_uso_suelo = gpd.read_file(shapefile_path, encoding='latin1')
print("CRS del dataset de uso de suelo:", gdf_uso_suelo.crs)


# In[26]:


# Verificar y alinear el CRS de las manzanas
if gdf_manzanas.crs != coyoacan_polygon.crs:
    gdf_manzanas = gdf_manzanas.to_crs(coyoacan_polygon.crs)

# Verificar y alinear el CRS de los puntos de uso de suelo
if gdf_uso_suelo.crs != coyoacan_polygon.crs:
    gdf_uso_suelo = gdf_uso_suelo.to_crs(coyoacan_polygon.crs)


# In[27]:


gdf_manzanas_coyoacan = gpd.clip(gdf_manzanas, coyoacan_polygon)


# In[28]:


# Verificar si 'IDENTIFICA' es único
es_unico = gdf_manzanas_coyoacan['IDENTIFICA'].is_unique
print(f"'IDENTIFICA' es único: {es_unico}")


# In[29]:


gdf_uso_suelo_coyoacan = gpd.clip(gdf_uso_suelo, coyoacan_polygon)


# In[30]:


# Realizar la unión espacial
gdf_union = gpd.sjoin(
    gdf_manzanas_coyoacan,
    gdf_uso_suelo_coyoacan,
    how='left',
    predicate='contains'
)


# In[31]:


print("Columnas en gdf_union:")
print(gdf_union.columns)


# In[32]:


print("Columnas en gdf_union después de sjoin:")
print(gdf_union.columns)


# In[33]:


uso_suelo_por_manzana = gdf_union.groupby(['IDENTIFICA', 'us_dscr']).size().reset_index(name = 'counts')


# In[34]:


# Obtener el índice del uso de suelo con mayor conteo en cada manzana
idx_max = uso_suelo_por_manzana.groupby('IDENTIFICA')['counts'].idxmax()

# Crear un DataFrame con el uso de suelo predominante por manzana
uso_suelo_predominante = uso_suelo_por_manzana.loc[idx_max]


# In[35]:


# Unir el uso de suelo predominante a las manzanas
gdf_manzanas_coyoacan = gdf_manzanas_coyoacan.merge(
    uso_suelo_predominante[['IDENTIFICA', 'us_dscr']],
    on='IDENTIFICA',
    how='left'
)


# In[36]:


# Asignar 'Sin Datos' a manzanas sin información de uso de suelo
gdf_manzanas_coyoacan['us_dscr'] = gdf_manzanas_coyoacan['us_dscr'].fillna('Sin Datos')


# In[37]:


# Paso 9: Calcular el centro del mapa
centro_lat = gdf_manzanas_coyoacan.geometry.centroid.y.mean()
centro_lon = gdf_manzanas_coyoacan.geometry.centroid.x.mean()

# Paso 10: Crear el mapa
m = folium.Map(location=[centro_lat, centro_lon], zoom_start=13)

# Paso 11: Preparar la paleta de colores
tipos_uso_suelo = gdf_manzanas_coyoacan['us_dscr'].unique()
colores = [
    '#e41a1c', '#377eb8', '#4daf4a', '#984ea3',
    '#ff7f00', '#ffff33', '#a65628', '#f781bf', '#999999',
    '#a6cee3', '#1f78b4', '#b2df8a', '#33a02c',
    '#fb9a99', '#e31a1c', '#fdbf6f', '#ff7f00',
    '#cab2d6', '#6a3d9a', '#ffff99'
] * 10  # Multiplicar para asegurar suficientes colores
color_dict = dict(zip(tipos_uso_suelo, colores[:len(tipos_uso_suelo)]))

# Paso 12: Añadir las manzanas al mapa
def style_function(feature):
    uso = feature['properties']['us_dscr']
    return {
        'fillColor': color_dict.get(uso, 'gray'),
        'color': 'black',
        'weight': 0.5,
        'fillOpacity': 0.7,
    }

folium.GeoJson(
    gdf_manzanas_coyoacan,
    style_function=style_function,
    tooltip=folium.GeoJsonTooltip(fields=['us_dscr'], aliases=['Uso de Suelo:'])
).add_to(m)

# Paso 13: Añadir la leyenda
def generate_legend_html(color_dict):
    html = '''
    <div style="
        position: fixed;
        bottom: 50px;
        left: 50px;
        width: 300px;
        background-color: white;
        border:2px solid grey;
        z-index:9999;
        font-size:12px;
        padding: 10px;
        max-height: 300px;
        overflow-y: auto;
        ">
        <b>Usos de Suelo</b><br>
    '''
    for uso, color in color_dict.items():
        html += f'<i style="background:{color};width:12px;height:12px;float:left;margin-right:8px;"></i>{uso}<br>'
    html += '</div>'
    return html

legend_html = generate_legend_html(color_dict)
m.get_root().html.add_child(folium.Element(legend_html))

# Paso 14: Ajustar el mapa a los límites de los datos
bounds = gdf_manzanas_coyoacan.total_bounds  # [minx, miny, maxx, maxy]
m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

# Paso 15: Guardar el mapa
#m.save('mapa_uso_suelo_coyoacan_manzanas.html')

# Mostrar el mapa si estás en un notebook
m

