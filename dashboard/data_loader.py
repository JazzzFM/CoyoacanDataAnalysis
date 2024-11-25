# data_loader.py

import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="geopandas")

# Configuración del motor de la base de datos
engine = create_engine('postgresql://postgres:MelonSK998@localhost:5432/Poligonos')

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

# Nueva función para convertir CRS
def convert_crs(gdf, crs_target):
    if gdf.crs != crs_target:
        print(f"[DATA LOADER] Reproyectando a {crs_target}...")
        gdf = gdf.to_crs(crs_target)
        print("[DATA LOADER] Reproyección completada.")
    return gdf

# Nueva función para realizar uniones espaciales
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
