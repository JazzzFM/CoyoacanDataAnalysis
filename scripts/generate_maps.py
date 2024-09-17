#!/usr/bin/env python
# coding: utf-8

# Importar bibliotecas necesarias
import geopandas as gpd
import matplotlib.pyplot as plt
import folium
import pandas as pd
from shapely.geometry import Point
from dataclasses import dataclass
from typing import Optional
import re
import os

# Obtener la ruta absoluta del directorio del script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Definir el directorio de datos relativo al script
DATA_DIR = os.path.join(SCRIPT_DIR, '..', 'data')


# Función para convertir coordenadas DMS a decimal
def dms_to_decimal(dms: str) -> Optional[float]:
    """Convierte una coordenada DMS a decimal."""
    if pd.isna(dms) or not isinstance(dms, str):
        return None
    pattern = r"(\d+)\s*°\s*(\d+)\s*'\s*(\d+\.?\d*)\s*\"?\s*([NSEW])"
    match = re.match(pattern, dms.strip())
    if not match:
        return None
    degrees, minutes, seconds, direction = match.groups()
    decimal = float(degrees) + float(minutes) / 60 + float(seconds) / 3600
    if direction in ['S', 'W']:
        decimal *= -1
    return decimal

# Clase para manejar los datos geoespaciales
@dataclass
class GeoDataHandler:
    data_dir: str

    def load_demography_data(self) -> gpd.GeoDataFrame:
        """Carga y procesa los datos de demografía."""
        # Ruta al archivo CSV
        csv_path = f"{self.data_dir}demografia/iter_09_cpv2020/conjunto_de_datos/conjunto_de_datos_iter_09CSV20.csv"
        # Cargar datos
        demography_data = pd.read_csv(csv_path)

        # Convertir coordenadas DMS a decimal
        demography_data['LONGITUD'] = demography_data['LONGITUD'].apply(dms_to_decimal)
        demography_data['LATITUD'] = demography_data['LATITUD'].apply(dms_to_decimal)

        # Filtrar datos válidos
        valid_data = demography_data.dropna(subset=['LONGITUD', 'LATITUD'])
        valid_data = valid_data[
            (valid_data['LONGITUD'].apply(lambda x: isinstance(x, float))) &
            (valid_data['LATITUD'].apply(lambda x: isinstance(x, float)))
        ]

        # Crear GeoDataFrame
        gdf = gpd.GeoDataFrame(
            valid_data,
            geometry=gpd.points_from_xy(valid_data['LONGITUD'], valid_data['LATITUD']),
            crs='EPSG:4326'
        )
        return gdf

    def load_coyoacan_boundary(self) -> gpd.GeoDataFrame:
        """Carga los límites de Coyoacán."""
        shp_path = os.path.join(self.data_dir, 'limites', 'poligonos_alcaldias_cdmx.shp')
        gdf = gpd.read_file(shp_path)
        coyoacan_boundary = gdf[gdf['NOMGEO'] == 'Coyoacán']
        return coyoacan_boundary

    def load_land_use(self) -> gpd.GeoDataFrame:
        """Carga los datos de uso de suelo."""
        shp_path = os.path.join(self.data_dir, 'uso_suelo', 'uso-de-suelo.shp')
        gdf = gpd.read_file(shp_path, encoding='latin1')
        return gdf

    def load_manzanas(self) -> gpd.GeoDataFrame:
        """Carga los datos de manzanas."""
        shp_path = os.path.join(self.data_dir, 'manzanas', '090030001m.shp')
        gdf = gpd.read_file(shp_path)
        return gdf


# Función para crear un mapa interactivo con Folium
def create_interactive_map(
    gdf: gpd.GeoDataFrame,
    column_name: str,
    output_file: str,
    legend_title: str
) -> None:
    """Crea un mapa interactivo utilizando Folium."""
    # Reproyectar a CRS proyectado para cálculos geométricos
    gdf_proj = gdf.to_crs(epsg=32614)
    # Calcular el centro del mapa
    centroide = gdf_proj.geometry.centroid.union_all().centroid
    centroide_wgs84 = gpd.GeoSeries([centroide], crs='EPSG:32614').to_crs(epsg=4326)
    centro_lat = centroide_wgs84.geometry.y.iloc[0]
    centro_lon = centroide_wgs84.geometry.x.iloc[0]

    # Crear el mapa
    m = folium.Map(location=[centro_lat, centro_lon], zoom_start=13)

    # Preparar la paleta de colores
    tipos = gdf[column_name].unique()
    colores = [
        '#e41a1c', '#377eb8', '#4daf4a', '#984ea3',
        '#ff7f00', '#ffff33', '#a65628', '#f781bf', '#999999',
        '#a6cee3', '#1f78b4', '#b2df8a', '#33a02c',
        '#fb9a99', '#e31a1c', '#fdbf6f', '#ff7f00',
        '#cab2d6', '#6a3d9a', '#ffff99'
    ] * 10  # Asegurar suficientes colores
    color_dict = dict(zip(tipos, colores[:len(tipos)]))

    # Añadir los polígonos al mapa
    folium.GeoJson(
        gdf,
        style_function=lambda feature: {
            'fillColor': color_dict.get(feature['properties'][column_name], 'gray'),
            'color': 'black',
            'weight': 0.5,
            'fillOpacity': 0.7,
        },
        tooltip=folium.GeoJsonTooltip(fields=[column_name], aliases=[legend_title])
    ).add_to(m)

    # Añadir la leyenda
    legend_html = generate_legend_html(color_dict, legend_title)
    m.get_root().html.add_child(folium.Element(legend_html))

    # Ajustar el mapa a los límites de los datos
    bounds = gdf.total_bounds
    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    # Construir la ruta de salida relativa al script
    output_path = os.path.join(SCRIPT_DIR, '..', 'outputs', output_file)

    # Guardar el mapa
    m.save(output_path)

# Función para generar la leyenda del mapa
def generate_legend_html(color_dict: dict, legend_title: str) -> str:
    """Genera el HTML para la leyenda del mapa."""
    html = f'''
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
        <b>{legend_title}</b><br>
    '''
    for tipo, color in color_dict.items():
        html += f'<i style="background:{color};width:12px;height:12px;float:left;margin-right:8px;"></i>{tipo}<br>'
    html += '</div>'
    return html

# Función principal
def main():
    # Crear una instancia del manejador de datos
    geo_handler = GeoDataHandler(data_dir=DATA_DIR)

    # Cargar los datos
    coyoacan_boundary = geo_handler.load_coyoacan_boundary()
    uso_suelo = geo_handler.load_land_use()
    manzanas = geo_handler.load_manzanas()

    # Asegurar que los CRS coincidan
    if coyoacan_boundary.crs != uso_suelo.crs:
        coyoacan_boundary = coyoacan_boundary.to_crs(uso_suelo.crs)
    if manzanas.crs != uso_suelo.crs:
        manzanas = manzanas.to_crs(uso_suelo.crs)

    # Recortar los datos al área de Coyoacán
    uso_suelo_coyoacan = gpd.clip(uso_suelo, coyoacan_boundary)
    manzanas_coyoacan = gpd.clip(manzanas, coyoacan_boundary)

    # Realizar la unión espacial entre manzanas y uso de suelo
    gdf_union = gpd.sjoin(
        manzanas_coyoacan,
        uso_suelo_coyoacan,
        how='left',
        predicate='contains'
    )

    # Determinar el uso de suelo predominante en cada manzana
    uso_suelo_por_manzana = gdf_union.groupby(['IDENTIFICA', 'us_dscr']).size().reset_index(name='counts')
    idx_max = uso_suelo_por_manzana.groupby('IDENTIFICA')['counts'].idxmax()
    uso_suelo_predominante = uso_suelo_por_manzana.loc[idx_max]

    # Unir el uso de suelo predominante al GeoDataFrame de manzanas
    manzanas_coyoacan = manzanas_coyoacan.merge(
        uso_suelo_predominante[['IDENTIFICA', 'us_dscr']],
        on='IDENTIFICA',
        how='left'
    )
    # Manejar manzanas sin datos
    manzanas_coyoacan['us_dscr'] = manzanas_coyoacan['us_dscr'].fillna('Sin Datos')

    # Crear el mapa de uso de suelo por manzana
    create_interactive_map(
        gdf=manzanas_coyoacan,
        column_name='us_dscr',
        output_file='mapa_uso_suelo_coyoacan_manzanas.html',
        legend_title='Uso de Suelo por Manzana'
    )

# Ejecutar la función principal
if __name__ == '__main__':
    main()
