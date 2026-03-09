#!/usr/bin/env python3
# scripts/etl_electorales.py

"""
ETL para datos electorales INE (secciones electorales).

Carga el shapefile SECCION.shp del Marco Geostadistico Electoral del INE,
filtra las secciones de Coyoacan (municipio==3) y las sube a Neon PostGIS.

Uso:
    python scripts/etl_electorales.py "data/electoral/09 CIUDAD DE MEXICO/SECCION.shp"
    python scripts/etl_electorales.py "data/electoral/09 CIUDAD DE MEXICO/SECCION.shp" --reemplazar

Estructura esperada:
    - SECCION.shp con columnas: id, entidad, distrito_f, distrito_l,
      municipio, seccion, tipo, control, geometry
    - CRS original: EPSG:32614 (UTM 14N)

Requiere:
    - Archivo .env en la raiz del proyecto con DATABASE_URI
    - Python con geopandas, sqlalchemy, psycopg2-binary, geoalchemy2, python-dotenv
"""

import sys
import os
import argparse
import logging
import geopandas as gpd
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
TABLA_DESTINO = "datos_electorales"
CRS_ALMACENAMIENTO = "EPSG:4326"   # WGS84 para almacenamiento
CVE_MUN_COYOACAN = 3               # Codigo de municipio Coyoacan en CDMX
ANIO = 2024                        # Anio del marco geoelectoral
TERRITORIO = "coyoacan"

# Columnas finales para el dashboard
COLUMNAS_FINALES = [
    'seccion',
    'distrito_federal',
    'distrito_local',
    'tipo_seccion',
    'control',
    'area_km2',
    'anio',
    'territorio',
    'geometry'
]


# ──────────────────────────────────────────────
# Funciones principales del ETL
# ──────────────────────────────────────────────
def cargar_shapefile_secciones(ruta_shapefile):
    """
    Paso 1: Carga el shapefile SECCION.shp del INE.
    """
    logger.info(f"Cargando shapefile de secciones: {ruta_shapefile}")

    if not os.path.exists(ruta_shapefile):
        logger.error(f"Archivo no encontrado: {ruta_shapefile}")
        sys.exit(1)

    gdf = gpd.read_file(ruta_shapefile)

    logger.info(f"  Registros cargados: {len(gdf)}")
    logger.info(f"  Columnas: {list(gdf.columns)}")
    logger.info(f"  CRS original: {gdf.crs}")

    return gdf


def filtrar_coyoacan(gdf):
    """
    Paso 2: Filtra solo las secciones del municipio de Coyoacan.
    En la CDMX, Coyoacan tiene el codigo de municipio 3.
    """
    logger.info(f"Filtrando secciones de Coyoacan (municipio=={CVE_MUN_COYOACAN})...")

    # La columna puede ser int o string, normalizamos
    if gdf['municipio'].dtype == 'object':
        gdf_coyoacan = gdf[gdf['municipio'].astype(int) == CVE_MUN_COYOACAN].copy()
    else:
        gdf_coyoacan = gdf[gdf['municipio'] == CVE_MUN_COYOACAN].copy()

    logger.info(f"  Secciones en CDMX: {len(gdf)}")
    logger.info(f"  Secciones en Coyoacan: {len(gdf_coyoacan)}")

    # Mostrar distritos presentes
    if 'distrito_f' in gdf_coyoacan.columns:
        distritos_f = sorted(gdf_coyoacan['distrito_f'].unique())
        logger.info(f"  Distritos federales: {distritos_f}")

    if 'distrito_l' in gdf_coyoacan.columns:
        distritos_l = sorted(gdf_coyoacan['distrito_l'].unique())
        logger.info(f"  Distritos locales: {distritos_l}")

    return gdf_coyoacan


def reproyectar(gdf):
    """
    Paso 3: Reproyecta de UTM 14N (EPSG:32614) a WGS84 (EPSG:4326).
    """
    crs_original = gdf.crs
    logger.info(f"Reproyectando de {crs_original} a {CRS_ALMACENAMIENTO}...")

    if str(crs_original) != CRS_ALMACENAMIENTO:
        gdf = gdf.to_crs(CRS_ALMACENAMIENTO)
        logger.info(f"  CRS final: {gdf.crs}")
    else:
        logger.info("  Ya esta en WGS84, no se requiere reproyeccion.")

    return gdf


def calcular_area(gdf):
    """
    Paso 4: Calcula el area de cada seccion en km2.
    Reproyecta temporalmente a UTM para calculo metrico preciso.
    """
    logger.info("Calculando area de secciones en km2...")

    gdf_utm = gdf.to_crs("EPSG:32614")
    gdf['area_km2'] = (gdf_utm.geometry.area / 1_000_000).round(4)

    logger.info(f"  Area min: {gdf['area_km2'].min():.4f} km2")
    logger.info(f"  Area max: {gdf['area_km2'].max():.4f} km2")
    logger.info(f"  Area media: {gdf['area_km2'].mean():.4f} km2")
    logger.info(f"  Area total: {gdf['area_km2'].sum():.2f} km2")

    return gdf


def renombrar_y_seleccionar(gdf, anio):
    """
    Paso 5: Renombra columnas y selecciona las necesarias.
    """
    logger.info("Renombrando columnas...")

    mapeo_columnas = {
        'distrito_f': 'distrito_federal',
        'distrito_l': 'distrito_local',
        'tipo': 'tipo_seccion',
    }

    gdf = gdf.rename(columns=mapeo_columnas)

    # Agregar metadatos
    gdf['anio'] = str(anio)
    gdf['territorio'] = TERRITORIO

    # Seleccionar columnas finales
    columnas_disponibles = [col for col in COLUMNAS_FINALES if col in gdf.columns]
    columnas_faltantes = [col for col in COLUMNAS_FINALES if col not in gdf.columns]

    if columnas_faltantes:
        logger.warning(f"  Columnas faltantes: {columnas_faltantes}")

    gdf = gdf[columnas_disponibles].copy()

    logger.info(f"  Columnas seleccionadas: {list(gdf.columns)}")
    logger.info(f"  Registros: {len(gdf)}")

    # Distribucion por tipo de seccion
    if 'tipo_seccion' in gdf.columns:
        logger.info("  --- Distribucion por tipo de seccion ---")
        for tipo, conteo in gdf['tipo_seccion'].value_counts().items():
            logger.info(f"    - {tipo}: {conteo}")

    return gdf


def subir_a_neon(gdf, engine, modo='append'):
    """
    Paso 6: Sube el GeoDataFrame a Neon PostGIS.
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
        description="ETL de secciones electorales INE -> Neon PostGIS"
    )
    parser.add_argument(
        "ruta_shapefile",
        help="Ruta al shapefile SECCION.shp del INE"
    )
    parser.add_argument(
        "--anio",
        type=int,
        default=ANIO,
        help=f"Anio del marco geoelectoral (por defecto: {ANIO})"
    )
    parser.add_argument(
        "--reemplazar",
        action="store_true",
        help="Reemplaza datos existentes en la tabla (if_exists='replace'). "
             "Por defecto agrega (append)."
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
            logger.error("Configure el archivo .env o establezca DATABASE_URI.")
            sys.exit(1)

        database_uri = (
            f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            f"?sslmode=require"
        )

    logger.info("Conectando a la base de datos...")
    engine = create_engine(database_uri)

    # Verificar conexion
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
    logger.info(f"INICIO ETL ELECTORALES - Secciones INE {anio}")
    logger.info(f"Shapefile: {args.ruta_shapefile}")
    logger.info("=" * 60)

    # 1. Cargar shapefile
    gdf = cargar_shapefile_secciones(args.ruta_shapefile)

    # 2. Filtrar Coyoacan
    gdf = filtrar_coyoacan(gdf)

    # 3. Reproyectar a WGS84
    gdf = reproyectar(gdf)

    # 4. Calcular area en km2
    gdf = calcular_area(gdf)

    # 5. Renombrar y seleccionar columnas
    gdf = renombrar_y_seleccionar(gdf, anio=anio)

    # 6. Subir a Neon
    modo = 'replace' if args.reemplazar else 'append'
    if args.reemplazar:
        logger.warning("Modo REEMPLAZAR activado: se eliminaran datos previos.")
    subir_a_neon(gdf, engine, modo)

    logger.info("=" * 60)
    logger.info("ETL ELECTORALES COMPLETADO EXITOSAMENTE")
    logger.info(f"  Registros cargados: {len(gdf)}")
    logger.info(f"  Tabla destino: {TABLA_DESTINO}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
