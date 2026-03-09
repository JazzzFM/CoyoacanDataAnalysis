#!/usr/bin/env python3
# scripts/etl_denue.py

"""
ETL para datos del DENUE (Directorio Estadistico Nacional de Unidades Economicas).

Carga el CSV del DENUE para CDMX, filtra Coyoacan, categoriza por SCIAN,
convierte coordenadas a geometria POINT y sube a la tabla `datos_servicios`
en Neon PostGIS.

Uso:
    python scripts/etl_denue.py data/denue/conjunto_de_datos/denue_inegi_09_.csv

Requiere:
    - Archivo .env en la raiz del proyecto con DATABASE_URI
    - Python con geopandas, pandas, sqlalchemy, psycopg2-binary, python-dotenv
"""

import sys
import os
import argparse
import logging
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# ──────────────────────────────────────────────
# Configuracion de logging
# ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Constantes
# ──────────────────────────────────────────────
TABLA_DESTINO = "datos_servicios"
CRS_ALMACENAMIENTO = "EPSG:4326"
CVE_MUN_COYOACAN = "003"
ANIO = 2024

# Categorizacion por codigo SCIAN (primeros 3 digitos)
CATEGORIAS_SCIAN = {
    'salud': ['621', '622', '623'],
    'educacion': ['611'],
    'comercio': ['461', '462', '463', '464', '465', '466', '467', '468', '469'],
    'alimentacion': ['722'],
    'industria': ['311', '312', '313', '314', '315', '316', '321', '322', '323',
                  '324', '325', '326', '327', '331', '332', '333', '334', '335',
                  '336', '337', '339'],
    'servicios_financieros': ['521', '522', '523', '524'],
    'transporte': ['481', '482', '483', '484', '485', '486', '487', '488', '491', '492', '493'],
    'gobierno': ['931', '932', '933'],
}


def clasificar_actividad(codigo_act):
    """Clasifica un codigo SCIAN en una categoria."""
    codigo = str(codigo_act).strip()[:3]
    for categoria, prefijos in CATEGORIAS_SCIAN.items():
        if codigo in prefijos:
            return categoria
    return 'otro'


# ──────────────────────────────────────────────
# Funciones principales del ETL
# ──────────────────────────────────────────────
def cargar_y_filtrar_csv(ruta_csv):
    """
    Paso 1: Carga el CSV del DENUE y filtra a Coyoacan.
    """
    logger.info(f"Cargando CSV del DENUE: {ruta_csv}")

    if not os.path.exists(ruta_csv):
        logger.error(f"Archivo no encontrado: {ruta_csv}")
        sys.exit(1)

    df = pd.read_csv(ruta_csv, encoding='latin1', dtype={
        'cve_ent': str, 'cve_mun': str, 'codigo_act': str,
        'latitud': str, 'longitud': str
    }, low_memory=False)
    logger.info(f"  Total registros CDMX: {len(df)}")

    # Normalizar cve_mun a 3 digitos
    df['cve_mun'] = df['cve_mun'].str.zfill(3)

    # Filtrar Coyoacan
    df_coyoacan = df[df['cve_mun'] == CVE_MUN_COYOACAN].copy()
    logger.info(f"  Registros en Coyoacan: {len(df_coyoacan)}")

    return df_coyoacan


def limpiar_y_categorizar(df):
    """
    Paso 2: Limpieza de datos y categorizacion por SCIAN.
    """
    logger.info("Limpiando y categorizando datos...")

    # Convertir coordenadas a numerico
    df['latitud'] = pd.to_numeric(df['latitud'], errors='coerce')
    df['longitud'] = pd.to_numeric(df['longitud'], errors='coerce')

    # Eliminar registros sin coordenadas validas
    antes = len(df)
    df = df.dropna(subset=['latitud', 'longitud'])
    logger.info(f"  Registros eliminados por coordenadas nulas: {antes - len(df)}")

    # Filtrar coordenadas fuera de rango razonable para Coyoacan
    df = df[
        (df['latitud'] > 19.2) & (df['latitud'] < 19.4) &
        (df['longitud'] > -99.25) & (df['longitud'] < -99.05)
    ]
    logger.info(f"  Registros despues de filtrar coordenadas: {len(df)}")

    # Categorizar actividad economica
    df['categoria'] = df['codigo_act'].apply(clasificar_actividad)

    # Mostrar distribucion de categorias
    distribucion = df['categoria'].value_counts()
    logger.info("  Distribucion de categorias:")
    for cat, conteo in distribucion.items():
        logger.info(f"    - {cat}: {conteo}")

    return df


def construir_geodataframe(df, anio=ANIO):
    """
    Paso 3: Convierte el DataFrame a GeoDataFrame con geometrias POINT.
    Selecciona las columnas finales para la tabla datos_servicios.
    """
    logger.info("Construyendo GeoDataFrame con geometrias POINT...")

    geometry = [Point(xy) for xy in zip(df['longitud'], df['latitud'])]
    gdf = gpd.GeoDataFrame(
        df,
        geometry=geometry,
        crs=CRS_ALMACENAMIENTO
    )

    # Seleccionar y renombrar columnas finales
    gdf = gdf.rename(columns={
        'nom_estab': 'nombre',
        'nombre_act': 'subcategoria',
        'codigo_act': 'codigo_scian',
        'per_ocu': 'personal_ocupado',
    })

    columnas_finales = [
        'nombre', 'categoria', 'subcategoria', 'codigo_scian',
        'personal_ocupado', 'geometry'
    ]
    gdf = gdf[columnas_finales].copy()
    gdf['anio'] = anio

    logger.info(f"  Columnas finales: {list(gdf.columns)}")
    logger.info(f"  Total registros: {len(gdf)}")

    return gdf


def subir_a_neon(gdf, engine, modo='append'):
    """
    Paso 4: Sube el GeoDataFrame a Neon PostGIS.
    """
    logger.info(f"Subiendo {len(gdf)} registros a '{TABLA_DESTINO}' (modo: {modo})...")

    try:
        gdf.to_postgis(
            name=TABLA_DESTINO,
            con=engine,
            if_exists=modo,
            index=False
        )
        logger.info(f"  Datos subidos exitosamente a '{TABLA_DESTINO}'.")
    except Exception as e:
        logger.error(f"  Error al subir datos: {e}")
        raise


# ──────────────────────────────────────────────
# Punto de entrada
# ──────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="ETL de datos DENUE para Coyoacan -> Neon PostGIS"
    )
    parser.add_argument(
        "ruta_csv",
        help="Ruta al CSV del DENUE (denue_inegi_09_.csv)"
    )
    parser.add_argument(
        "--anio",
        type=int,
        default=ANIO,
        help=f"Anio de los datos (por defecto: {ANIO})"
    )
    parser.add_argument(
        "--reemplazar",
        action="store_true",
        help="Si se especifica, reemplaza los datos existentes en la tabla."
    )

    args = parser.parse_args()

    # Cargar variables de entorno
    ruta_proyecto = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ruta_env = os.path.join(ruta_proyecto, '.env')
    load_dotenv(ruta_env)
    logger.info(f"Archivo .env cargado desde: {ruta_env}")

    # Construir URI de conexion
    database_uri = os.getenv('DATABASE_URI')
    if not database_uri:
        db_user = os.getenv('DB_USER', 'neondb_owner')
        db_password = os.getenv('DB_PASSWORD')
        db_host = os.getenv('DB_HOST')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME', 'neondb')

        if not db_password or not db_host:
            logger.error("Faltan variables de entorno: DB_PASSWORD y/o DB_HOST.")
            sys.exit(1)

        database_uri = (
            f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            f"?sslmode=require"
        )

    logger.info("Conectando a la base de datos...")
    engine = create_engine(database_uri)

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("  Conexion exitosa a Neon PostGIS.")
    except Exception as e:
        logger.error(f"  No se pudo conectar a la base de datos: {e}")
        sys.exit(1)

    anio = args.anio

    # ── Pipeline ETL ──
    logger.info("=" * 60)
    logger.info(f"INICIO ETL DENUE - Unidades Economicas {anio}")
    logger.info(f"CSV de datos: {args.ruta_csv}")
    logger.info("=" * 60)

    # 1. Cargar y filtrar CSV
    df = cargar_y_filtrar_csv(args.ruta_csv)

    # 2. Limpiar y categorizar
    df = limpiar_y_categorizar(df)

    # 3. Construir GeoDataFrame
    gdf = construir_geodataframe(df, anio=anio)

    # 4. Subir a Neon
    modo = 'replace' if args.reemplazar else 'append'
    if args.reemplazar:
        logger.warning("Modo REEMPLAZAR activado: se eliminaran datos previos de la tabla.")
    subir_a_neon(gdf, engine, modo)

    logger.info("=" * 60)
    logger.info("ETL DENUE COMPLETADO EXITOSAMENTE")
    logger.info(f"  Registros cargados: {len(gdf)}")
    logger.info(f"  Tabla destino: {TABLA_DESTINO}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
