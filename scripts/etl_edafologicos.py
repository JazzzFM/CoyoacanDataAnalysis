#!/usr/bin/env python3
# scripts/etl_edafologicos.py

"""
ETL para datos edafologicos / uso de suelo SEDUVI 2017.

Carga el shapefile de uso de suelo de la CDMX, realiza un cruce espacial
con los poligonos de manzanas de Coyoacan (desde Neon PostGIS), y sube los
datos procesados a la tabla `datos_edafologicos_particionada`.

Replica la logica del notebook: notebooks/ManzanasUsuoSueloEDA.ipynb

Uso:
    python scripts/etl_edafologicos.py /ruta/a/uso-de-suelo.shp

Estructura esperada:
    - El shapefile de uso de suelo (uso-de-suelo.shp y archivos auxiliares)
    - La tabla `poligonos_manzanas_agebs_colonias` debe existir en Neon con datos

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
TABLA_DESTINO = "datos_edafologicos_particionada"
TABLA_POLIGONOS = "poligonos_manzanas_agebs_colonias"
CRS_ALMACENAMIENTO = "EPSG:4326"   # WGS84 para almacenamiento
ANIO = 2017                        # Anio de los datos SEDUVI
TERRITORIO = "coyoacan"

# Columnas finales esperadas por el dashboard
# (ver callback_register.py y domain_models.py)
COLUMNAS_FINALES = [
    'ID_MANZANA',
    'GEOM_MANZANA',
    'USO_SUELO',
    'SUPERFICIE',
    'DNSDD_D',
    'NIVELES',
    'ALTURA',
    'anio',
    'territorio'
]


# ──────────────────────────────────────────────
# Funciones principales del ETL
# ──────────────────────────────────────────────
def cargar_shapefile_uso_suelo(ruta_shapefile):
    """
    Paso 1: Carga el shapefile de uso de suelo SEDUVI.
    Filtra registros sin descripcion de uso de suelo (us_dscr).
    """
    logger.info(f"Cargando shapefile de uso de suelo: {ruta_shapefile}")

    if not os.path.exists(ruta_shapefile):
        logger.error(f"Archivo no encontrado: {ruta_shapefile}")
        sys.exit(1)

    # Intentar leer con encoding latin1 (datos SEDUVI usan caracteres especiales)
    try:
        gdf = gpd.read_file(ruta_shapefile, encoding='latin1')
    except Exception:
        logger.warning("No se pudo leer con encoding latin1, intentando sin encoding...")
        gdf = gpd.read_file(ruta_shapefile)

    logger.info(f"  Registros cargados: {len(gdf)}")
    logger.info(f"  Columnas: {list(gdf.columns)}")
    logger.info(f"  CRS original: {gdf.crs}")

    # Eliminar registros sin descripcion de uso de suelo
    antes = len(gdf)
    gdf = gdf.dropna(subset=['us_dscr'])
    logger.info(f"  Registros eliminados por us_dscr nulo: {antes - len(gdf)}")
    logger.info(f"  Registros validos: {len(gdf)}")

    # Mostrar tipos de uso de suelo encontrados
    tipos_uso = gdf['us_dscr'].value_counts()
    logger.info("  Tipos de uso de suelo encontrados:")
    for tipo, conteo in tipos_uso.items():
        logger.info(f"    - {tipo}: {conteo}")

    return gdf


def cargar_poligonos_manzanas(engine):
    """
    Paso 2: Carga los poligonos de manzanas de Coyoacan desde Neon PostGIS.
    Solo se necesita ID_MANZANA y GEOM_MANZANA para el cruce espacial.
    """
    logger.info(f"Cargando poligonos de manzanas desde '{TABLA_POLIGONOS}'...")

    try:
        query = f'SELECT "ID_MANZANA", "GEOM_MANZANA" FROM {TABLA_POLIGONOS}'
        gdf_manzanas = gpd.read_postgis(
            query,
            con=engine,
            geom_col="GEOM_MANZANA"
        )
        logger.info(f"  Poligonos cargados: {len(gdf_manzanas)}")
        logger.info(f"  CRS: {gdf_manzanas.crs}")
        return gdf_manzanas
    except Exception as e:
        logger.error(f"  Error al cargar poligonos: {e}")
        raise


def filtrar_coyoacan(gdf_uso_suelo, gdf_manzanas):
    """
    Paso 3: Filtra el uso de suelo al area de Coyoacan.
    Usa los poligonos de manzanas como referencia para el recorte espacial.
    """
    logger.info("Filtrando uso de suelo al area de Coyoacan...")

    # Alinear CRS
    crs_comun = gdf_manzanas.crs
    if gdf_uso_suelo.crs != crs_comun:
        logger.info(f"  Reproyectando uso de suelo de {gdf_uso_suelo.crs} a {crs_comun}")
        gdf_uso_suelo = gdf_uso_suelo.to_crs(crs_comun)

    # Obtener el bounding box de las manzanas para un clip eficiente
    # Usamos unary_union para crear un solo poligono de Coyoacan
    poligono_coyoacan = gdf_manzanas.unary_union.convex_hull
    gdf_coyoacan = gpd.GeoDataFrame(
        geometry=[poligono_coyoacan],
        crs=crs_comun
    )

    gdf_uso_suelo_coyoacan = gpd.clip(gdf_uso_suelo, gdf_coyoacan)
    logger.info(f"  Registros de uso de suelo en Coyoacan: {len(gdf_uso_suelo_coyoacan)}")

    return gdf_uso_suelo_coyoacan


def cruce_espacial_manzanas(gdf_manzanas, gdf_uso_suelo):
    """
    Paso 4: Realiza el cruce espacial entre manzanas y uso de suelo.
    Una manzana 'contains' un punto de uso de suelo.
    """
    logger.info("Realizando cruce espacial manzanas <-> uso de suelo...")

    # El shapefile SEDUVI tiene puntos o poligonos; usamos 'contains' como en el notebook
    gdf_union = gpd.sjoin(
        gdf_manzanas,
        gdf_uso_suelo,
        how='left',
        predicate='contains'
    )

    logger.info(f"  Registros despues del cruce: {len(gdf_union)}")

    # Contar manzanas con datos de uso de suelo
    con_datos = gdf_union.dropna(subset=['us_dscr'])
    logger.info(f"  Manzanas con datos de uso de suelo: {len(con_datos)}")
    logger.info(f"  Manzanas sin datos: {len(gdf_union) - len(con_datos)}")

    # Eliminar registros sin uso de suelo (como en el notebook)
    gdf_union = gdf_union.dropna(subset=['us_dscr'])

    return gdf_union


def renombrar_y_seleccionar_columnas(gdf, anio=ANIO):
    """
    Paso 5: Renombra columnas y selecciona solo las necesarias.
    Mapeo de nombres del shapefile SEDUVI -> nombres del dashboard.
    """
    logger.info("Renombrando columnas y seleccionando las requeridas...")

    # Renombrar columnas segun el notebook y el dashboard
    mapeo_columnas = {
        'us_dscr': 'USO_SUELO',
        'superfc': 'SUPERFICIE',
        'dnsdd_d': 'DNSDD_D',
        'niveles': 'NIVELES',
        'altura': 'ALTURA',
    }

    gdf = gdf.rename(columns=mapeo_columnas)

    # Agregar columnas de metadatos
    gdf['anio'] = str(anio)
    gdf['territorio'] = TERRITORIO

    # Seleccionar solo las columnas necesarias
    columnas_disponibles = [col for col in COLUMNAS_FINALES if col in gdf.columns]
    columnas_faltantes = [col for col in COLUMNAS_FINALES if col not in gdf.columns]

    if columnas_faltantes:
        logger.warning(f"  Columnas faltantes: {columnas_faltantes}")

    gdf = gdf[columnas_disponibles].copy()

    logger.info(f"  Columnas seleccionadas: {list(gdf.columns)}")
    logger.info(f"  Registros: {len(gdf)}")

    return gdf


def preparar_para_carga(gdf):
    """
    Paso 6: Preparacion final antes de subir a PostGIS.
    - Asegurar CRS correcto (WGS84)
    - Verificar geometrias
    """
    logger.info("Preparando datos para carga a PostGIS...")

    # Asegurar CRS WGS84
    if gdf.crs and str(gdf.crs) != CRS_ALMACENAMIENTO:
        logger.info(f"  Reproyectando de {gdf.crs} a {CRS_ALMACENAMIENTO}")
        gdf = gdf.to_crs(CRS_ALMACENAMIENTO)

    # Configurar la columna de geometria activa como GEOM_MANZANA
    if 'GEOM_MANZANA' in gdf.columns:
        gdf = gdf.set_geometry('GEOM_MANZANA')

    # Estadisticas resumidas
    logger.info(f"  CRS final: {gdf.crs}")
    logger.info(f"  Total de registros: {len(gdf)}")

    if 'USO_SUELO' in gdf.columns:
        logger.info("  --- Distribucion de uso de suelo ---")
        distribucion = gdf['USO_SUELO'].value_counts()
        for tipo, conteo in distribucion.head(10).items():
            logger.info(f"    - {tipo}: {conteo}")
        if len(distribucion) > 10:
            logger.info(f"    ... y {len(distribucion) - 10} tipos mas")

    if 'SUPERFICIE' in gdf.columns:
        logger.info(f"  Superficie: min={gdf['SUPERFICIE'].min():.1f}, "
                    f"max={gdf['SUPERFICIE'].max():.1f}, "
                    f"media={gdf['SUPERFICIE'].mean():.1f}")

    if 'NIVELES' in gdf.columns:
        logger.info(f"  Niveles: min={gdf['NIVELES'].min()}, "
                    f"max={gdf['NIVELES'].max()}, "
                    f"media={gdf['NIVELES'].mean():.1f}")

    return gdf


def subir_a_neon(gdf, engine, modo='append'):
    """
    Paso 7: Sube el GeoDataFrame a Neon PostGIS.
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
        description="ETL de datos edafologicos/uso de suelo SEDUVI -> Neon PostGIS"
    )
    parser.add_argument(
        "ruta_shapefile",
        help="Ruta al shapefile de uso de suelo SEDUVI (uso-de-suelo.shp)"
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
        help="Si se especifica, reemplaza los datos existentes en la tabla (if_exists='replace'). "
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

    # Verificar que exista la tabla de poligonos con datos
    try:
        with engine.connect() as conn:
            resultado = conn.execute(
                text(f"SELECT COUNT(*) FROM {TABLA_POLIGONOS}")
            )
            conteo = resultado.scalar()
            if conteo == 0:
                logger.error(
                    f"La tabla '{TABLA_POLIGONOS}' esta vacia. "
                    "Primero cargue los poligonos de manzanas."
                )
                sys.exit(1)
            logger.info(f"  Tabla '{TABLA_POLIGONOS}' tiene {conteo} registros.")
    except Exception as e:
        logger.error(f"  Error al verificar tabla de poligonos: {e}")
        sys.exit(1)

    # Actualizar anio si se especifico
    anio = args.anio

    # ── Pipeline ETL ──
    logger.info("=" * 60)
    logger.info(f"INICIO ETL EDAFOLOGICOS - Uso de Suelo SEDUVI {anio}")
    logger.info(f"Shapefile de uso de suelo: {args.ruta_shapefile}")
    logger.info("=" * 60)

    # 1. Cargar shapefile de uso de suelo
    gdf_uso_suelo = cargar_shapefile_uso_suelo(args.ruta_shapefile)

    # 2. Cargar poligonos de manzanas desde Neon
    gdf_manzanas = cargar_poligonos_manzanas(engine)

    # 3. Filtrar uso de suelo al area de Coyoacan
    gdf_uso_suelo = filtrar_coyoacan(gdf_uso_suelo, gdf_manzanas)

    # 4. Cruce espacial: manzanas <-> uso de suelo
    gdf_union = cruce_espacial_manzanas(gdf_manzanas, gdf_uso_suelo)

    # 5. Renombrar y seleccionar columnas
    gdf_union = renombrar_y_seleccionar_columnas(gdf_union, anio=anio)

    # 6. Preparar para carga
    gdf_final = preparar_para_carga(gdf_union)

    # 7. Subir a Neon
    modo = 'replace' if args.reemplazar else 'append'
    if args.reemplazar:
        logger.warning("Modo REEMPLAZAR activado: se eliminaran datos previos de la tabla.")
    subir_a_neon(gdf_final, engine, modo)

    logger.info("=" * 60)
    logger.info("ETL EDAFOLOGICOS COMPLETADO EXITOSAMENTE")
    logger.info(f"  Registros cargados: {len(gdf_final)}")
    logger.info(f"  Tabla destino: {TABLA_DESTINO}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
