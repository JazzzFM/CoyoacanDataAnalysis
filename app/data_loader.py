import geopandas as gpd
from sqlalchemy import create_engine
import logging
import os
from dotenv import load_dotenv

# Configuración básica de logging
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Variables de conexión a la base de datos PostgreSQL
DB_USER = os.getenv('POSTGRES_USER')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD')
DB_HOST = os.getenv('DB_HOST', 'db')  # Host de Postgres en Docker
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB')

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Crear motor de conexión
engine = create_engine(DATABASE_URL)

def load_coyoacan_boundary():
    """
    Carga los límites de Coyoacán desde la base de datos.
    
    Returns:
        GeoDataFrame: GeoDataFrame con los límites de Coyoacán.
    """
    try:
        query = "SELECT * FROM public.limites_alcaldias WHERE nomgeo = 'Coyoacán';"
        gdf = gpd.read_postgis(query, engine, geom_col='geom')
        logger.info("Límites de Coyoacán cargados correctamente.")
        return gdf
    except Exception as e:
        logger.error(f"Error al cargar los límites de Coyoacán: {e}")
        raise

def load_land_use():
    """
    Carga el uso de suelo desde la base de datos.
    
    Returns:
        GeoDataFrame: GeoDataFrame con el uso de suelo.
    """
    try:
        query = "SELECT * FROM public.uso_suelo_coyoacan;"
        gdf = gpd.read_postgis(query, engine, geom_col='geom')
        logger.info("Uso de suelo cargado correctamente.")
        return gdf
    except Exception as e:
        logger.error(f"Error al cargar el uso de suelo: {e}")
        raise

def load_manzanas():
    """
    Carga las manzanas desde la base de datos.
    
    Returns:
        GeoDataFrame: GeoDataFrame con las manzanas.
    """
    try:
        query = "SELECT * FROM public.manzanas_coyoacan;"
        manzanas = gpd.read_postgis(query, engine, geom_col='geom')
        logger.info(f"Manzanas cargadas: {manzanas.shape}")
        logger.debug(manzanas.head())
        
        # Asignar el CRS correcto
        manzanas = manzanas.set_crs(epsg=6362, allow_override=True)
        logger.info("CRS de manzanas asignado a EPSG:6362")
        return manzanas
    except Exception as e:
        logger.error(f"Error al cargar las manzanas: {e}")
        raise

def calcular_uso_suelo_predominante():
    """
    Calcula el uso de suelo predominante por manzana.
    
    Returns:
        GeoDataFrame: GeoDataFrame de manzanas con el uso de suelo predominante.
    """
    try:
        # Cargar los datos
        coyoacan_boundary = load_coyoacan_boundary()
        uso_suelo = load_land_use()
        manzanas = load_manzanas()

        # Asegurar que los CRS coincidan
        common_crs = uso_suelo.crs
        if coyoacan_boundary.crs != common_crs:
            coyoacan_boundary = coyoacan_boundary.to_crs(common_crs)
            logger.info("Reproyectado límites de Coyoacán al CRS común.")
        if manzanas.crs != common_crs:
            manzanas = manzanas.to_crs(common_crs)
            logger.info("Reproyectado manzanas al CRS común.")

        # Recortar los datos al área de Coyoacán
        uso_suelo_coyoacan = gpd.clip(uso_suelo, coyoacan_boundary)
        manzanas_coyoacan = gpd.clip(manzanas, coyoacan_boundary)
        logger.info("Datos recortados al área de Coyoacán.")

        # Realizar la unión espacial entre manzanas y uso de suelo
        gdf_union = gpd.sjoin(
            manzanas_coyoacan,
            uso_suelo_coyoacan,
            how='left',
            predicate='intersects'  # Usar 'intersects' para mayor precisión
        )
        logger.info("Unión espacial completada.")

        # Determinar el uso de suelo predominante en cada manzana
        uso_suelo_por_manzana = gdf_union.groupby(['identifica', 'us_dscr']).size().reset_index(name='counts')
        idx_max = uso_suelo_por_manzana.groupby('identifica')['counts'].idxmax()
        uso_suelo_predominante = uso_suelo_por_manzana.loc[idx_max]
        logger.info("Cálculo del uso de suelo predominante completado.")

        # Unir el uso de suelo predominante al GeoDataFrame de manzanas
        manzanas_coyoacan = manzanas_coyoacan.merge(
            uso_suelo_predominante[['identifica', 'us_dscr']],
            on='identifica',
            how='left'
        )
        manzanas_coyoacan['us_dscr'] = manzanas_coyoacan['us_dscr'].fillna('Sin Datos')
        logger.info("Uso de suelo predominante unido al GeoDataFrame de manzanas.")

        # Asegurar que la columna de geometría está configurada correctamente
        manzanas_coyoacan = manzanas_coyoacan.set_geometry('geom')
        logger.info(f"Columnas en manzanas_coyoacan: {manzanas_coyoacan.columns}")
        logger.info(f"Columna de geometría en manzanas_coyoacan: {manzanas_coyoacan.geometry.name}")

        return manzanas_coyoacan

    except Exception as e:
        logger.error(f"Error al calcular el uso de suelo predominante: {e}")
        raise
