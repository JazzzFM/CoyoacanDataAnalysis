# data_loader.py

import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="geopandas")

# Configuración del motor de la base de datos
# Asegúrate de reemplazar 'your_password' con tu contraseña real
engine = create_engine('postgresql://postgres:your_password@localhost:5432/Poligonos')

def cargar_tabla(nombre_tabla):
    """
    Carga una tabla geoespacial desde la base de datos y la devuelve como GeoDataFrame.
    """
    query = f"SELECT * FROM {nombre_tabla};"
    gdf = gpd.read_postgis(query, engine, geom_col='geom')
    return gdf

def load_data(file_path):
    """
    Carga datos demográficos desde un archivo GeoJSON y calcula métricas adicionales.
    """
    print(f"[DATA LOADER] Intentando cargar datos desde: {file_path}")
    gdf = gpd.read_file(file_path)

    if gdf.crs != "EPSG:4326":
        gdf = convert_crs(gdf, "EPSG:4326")

    print(f"[DATA LOADER] Archivo cargado correctamente. Total de registros: {len(gdf)}")
    print("[DATA LOADER] Columnas disponibles en el archivo:", list(gdf.columns))
    print("[DATA LOADER] Calculando métricas adicionales...")
    gdf["relacion_genero"] = gdf["densidad_hombres"] / gdf["densidad_mujeres"]
    gdf["dependencia_infantil"] = gdf["p_3ymas"] / gdf["pob_total"]
    print("[DATA LOADER] Nuevas métricas calculadas exitosamente.")

    # Ajustar IDs para coincidir con las otras tablas
    gdf["id_ageb"] = gdf["ageb"].str[-4:]

    return gdf

def load_land_use_data():
    """
    Carga y procesa los datos de uso de suelo y los integra con las manzanas de Coyoacán.
    """
    try:
        # Cargar manzanas
        manzanas_shp = '../data/manzanas/090030001m.shp'
        gdf_manzanas = gpd.read_file(manzanas_shp)[['IDENTIFICA', 'geometry']]

        # Cargar polígono de Coyoacán
        coyoacan_polygon = gpd.read_file('../data/limites/poligonos_alcaldias_cdmx.shp')
        coyoacan_polygon = coyoacan_polygon[coyoacan_polygon['NOMGEO'] == 'Coyoacán']

        # Cargar uso de suelo
        shapefile_path = '../data/uso_suelo/uso-de-suelo.shp'
        gdf_uso_suelo = gpd.read_file(shapefile_path, encoding='latin1')[['us_dscr', 'geometry']]

        # Eliminar registros con NaN en 'us_dscr'
        gdf_uso_suelo = gdf_uso_suelo.dropna(subset=['us_dscr'])

        # Alinear CRS
        common_crs = coyoacan_polygon.crs
        gdf_manzanas = convert_crs(gdf_manzanas, common_crs)
        gdf_uso_suelo = convert_crs(gdf_uso_suelo, common_crs)

        # Recortar al área de Coyoacán
        gdf_manzanas_coyoacan = gpd.clip(gdf_manzanas, coyoacan_polygon)
        gdf_uso_suelo_coyoacan = gpd.clip(gdf_uso_suelo, coyoacan_polygon)

        # Unión espacial para asignar uso de suelo a manzanas
        gdf_union = spatial_join(
            gdf_left=gdf_manzanas_coyoacan,
            gdf_right=gdf_uso_suelo_coyoacan,
            how='left',
            predicate='intersects',
            lsuffix='manzana',
            rsuffix='uso_suelo'
        )

        # Eliminar filas con NaN en 'us_dscr' después de la unión
        gdf_union = gdf_union.dropna(subset=['us_dscr'])

        # Determinar uso de suelo predominante por manzana
        uso_suelo_por_manzana = gdf_union.groupby(['IDENTIFICA', 'us_dscr'])\
                                         .size()\
                                         .reset_index(name='counts')

        uso_suelo_predominante = uso_suelo_por_manzana.sort_values('counts', ascending=False)\
                                                      .drop_duplicates('IDENTIFICA')

        # Unir el uso de suelo predominante a las manzanas
        gdf_manzanas_coyoacan = gdf_manzanas_coyoacan.merge(
            uso_suelo_predominante[['IDENTIFICA', 'us_dscr']],
            on='IDENTIFICA',
            how='left'
        )

        # Asignar 'Sin Datos' a manzanas sin información de uso de suelo
        gdf_manzanas_coyoacan['us_dscr'] = gdf_manzanas_coyoacan['us_dscr'].fillna('Sin Datos')

        # Simplificar geometrías (opcional)
        gdf_manzanas_coyoacan['geometry'] = gdf_manzanas_coyoacan['geometry'].simplify(
            tolerance=0.0001, preserve_topology=True
        )

        print("[INFO] Datos de uso de suelo cargados y procesados exitosamente.")
        return gdf_manzanas_coyoacan

    except Exception as e:
        print(f"[ERROR] Error al cargar y procesar datos de uso de suelo: {e}")
        raise e

def load_static_data():
    """
    Carga las capas geoespaciales y los datos demográficos, realiza uniones espaciales y prepara los datos.
    """
    try:
        # Cargar capas geoespaciales desde la base de datos
        gdf_manzana = cargar_tabla("manzana")
        gdf_colonia = cargar_tabla("colonia")
        gdf_ageb = cargar_tabla("ageb")

        # Cargar datos demográficos desde el archivo GeoJSON
        datos_demograficos = load_data("../clean_data/coyoacan_poblacion_2020_clean.geojson")

        # Asegurar que todos los GeoDataFrames están en el mismo CRS
        crs_target = "EPSG:4326"
        gdf_manzana = convert_crs(gdf_manzana, crs_target)
        gdf_colonia = convert_crs(gdf_colonia, crs_target)
        gdf_ageb = convert_crs(gdf_ageb, crs_target)
        datos_demograficos = convert_crs(datos_demograficos, crs_target)

        # Unión espacial entre AGEB y manzanas
        ageb_to_manzanas = spatial_join(
            gdf_left=gdf_ageb,
            gdf_right=gdf_manzana,
            how="inner",
            predicate="intersects",
            lsuffix='ageb',
            rsuffix='manzana'
        )
        print("[INFO] Unión espacial entre AGEB y manzanas completada.")

        # Eliminar columnas de índice generadas automáticamente
        ageb_to_manzanas = ageb_to_manzanas.drop(columns=['index_ageb', 'index_manzana'], errors='ignore')

        # Combinar datos demográficos con las manzanas
        datos_con_manzanas = ageb_to_manzanas.merge(
            datos_demograficos,
            on="id_ageb"
        )
        print("[INFO] Datos demográficos combinados con manzanas.")

        # Unión espacial con colonias
        datos_con_colonias = spatial_join(
            gdf_left=datos_con_manzanas,
            gdf_right=gdf_colonia,
            how="inner",
            predicate="intersects",
            lsuffix='manzana',
            rsuffix='colonia'
        )
        print("[INFO] Unión espacial con colonias completada.")

        # Preparar los datos para cada nivel de granularidad
        datos = {
            "manzana": datos_con_colonias,
            "ageb": datos_con_manzanas,
            "colonia": datos_con_colonias
        }

        # Cargar y procesar datos de uso de suelo
        gdf_uso_suelo_manzanas = load_land_use_data()

        # Añadir los datos de uso de suelo al diccionario de datos
        datos['uso_suelo'] = gdf_uso_suelo_manzanas

        # Mostrar información de las tablas cargadas
        for nombre, gdf in datos.items():
            print(f"[INFO] Tabla '{nombre}' preparada con {len(gdf)} registros.")
            print(f"[INFO] Columnas disponibles en '{nombre}': {gdf.columns.tolist()}")

        return datos

    except Exception as e:
        print(f"[ERROR] Error al cargar y procesar los datos: {e}")
        raise e

def validate_geometries(gdf):
    """
    Verifica la validez de las geometrías y las corrige si es posible.
    """
    invalid_geometries = gdf[~gdf.is_valid]
    print(f"[VALIDACIÓN GEOMETRÍAS] Total de geometrías inválidas: {len(invalid_geometries)}")
    if len(invalid_geometries) > 0:
        # Intentar corregir las geometrías inválidas
        gdf['geometry'] = gdf['geometry'].buffer(0)
        invalid_geometries = gdf[~gdf.is_valid]
        if len(invalid_geometries) > 0:
            print("[VALIDACIÓN GEOMETRÍAS] No se pudieron corregir todas las geometrías inválidas.")
        else:
            print("[VALIDACIÓN GEOMETRÍAS] Todas las geometrías inválidas fueron corregidas.")
    else:
        print("[VALIDACIÓN GEOMETRÍAS] Todas las geometrías son válidas")

def convert_crs(gdf, crs_target):
    if gdf.crs != crs_target:
        print(f"[DATA LOADER] Reproyectando a {crs_target}...")
        gdf = gdf.to_crs(crs_target)
        print("[DATA LOADER] Reproyección completada.")
    return gdf

def spatial_join(gdf_left, gdf_right, how="inner", predicate="intersects", lsuffix='left', rsuffix='right'):
    gdf_joined = gpd.sjoin(
        gdf_left,
        gdf_right,
        how=how,
        predicate=predicate,
        lsuffix=lsuffix,
        rsuffix=rsuffix
    )
    # Eliminar columnas de índice generadas automáticamente
    index_cols = [col for col in ['index_'+lsuffix, 'index_'+rsuffix] if col in gdf_joined.columns]
    if index_cols:
        gdf_joined = gdf_joined.drop(columns=index_cols)
    return gdf_joined
