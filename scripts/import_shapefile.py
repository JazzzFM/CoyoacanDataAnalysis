# dashboard/import_shapefile.py

import geopandas as gpd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

# Cargar variables de entorno desde .env
load_dotenv()

DB_NAME = os.getenv('DB_NAME', 'Poligonos')
DB_USER = os.getenv('DB_USER', 'developer')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'MelonSK998')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')

# Crear la cadena de conexión
DATABASE_URL = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

# Crear el motor de SQLAlchemy
engine = create_engine(DATABASE_URL)

def importar_shapefile(ruta_shapefile, nombre_tabla):
    """
    Importa un shapefile a PostGIS.

    Args:
        ruta_shapefile (str): Ruta al shapefile.
        nombre_tabla (str): Nombre de la tabla en la base de datos.
    """
    try:
        # Cargar el shapefile en un GeoDataFrame
        gdf = gpd.read_file(ruta_shapefile)

        # Verificar que la columna geométrica se llama 'geom' o 'geometry'
        if 'geometry' not in gdf.columns and 'geom' not in gdf.columns:
            raise ValueError("El shapefile no contiene una columna 'geometry' ni 'geom'.")

        # Determinar el nombre de la columna geométrica
        if 'geometry' in gdf.columns:
            geom_col = 'geometry'
        else:
            geom_col = 'geom'

        # Reproyectar al CRS deseado si es necesario
        gdf = gdf.to_crs("EPSG:4326")

        # Escribir el GeoDataFrame en PostgreSQL
        gdf.to_postgis(name=nombre_tabla, con=engine, if_exists='replace', index=False)

        print(f"Shapefile '{ruta_shapefile}' importado exitosamente a la tabla '{nombre_tabla}'.")
    except Exception as e:
        print(f"[ERROR] Error al importar el shapefile '{ruta_shapefile}': {e}")
        raise e

if __name__ == "__main__":
    # Ejemplo de uso
    rutas_y_tablas = [
        ("../data/uso_suelo/uso-de-suelo.shp", "uso_suelo"),
        # Añade más shapefiles y tablas según sea necesario
    ]

    for ruta, tabla in rutas_y_tablas:
        importar_shapefile(ruta, tabla)

