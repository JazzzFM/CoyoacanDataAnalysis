#!/usr/bin/env python3
# scripts/etl_demograficos.py

"""
ETL para datos demograficos del censo INEGI 2020.

Carga los shapefiles de poblacion (total, hombres, mujeres) a nivel AGEB,
aplica las transformaciones de limpieza del notebook EDADemografia.ipynb
y sube los datos procesados a la tabla `datos_demograficos_particionada`
en Neon PostGIS.

Uso:
    python scripts/etl_demograficos.py /ruta/a/directorio/demografico/2020 /ruta/a/alcaldias/poligonos_alcaldias_cdmx.shp

Estructura esperada del directorio de datos:
    directorio/
        total.shp (y archivos auxiliares .dbf, .shx, .prj)
        hombres.shp
        mujeres.shp

Requiere:
    - Archivo .env en la raiz del proyecto con DATABASE_URI
    - Python con geopandas, sqlalchemy, psycopg2-binary, python-dotenv
"""

import sys
import os
import argparse
import logging
import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon, GeometryCollection
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
TABLA_DESTINO = "datos_demograficos_particionada"
CRS_ALMACENAMIENTO = "EPSG:4326"   # WGS84 para almacenamiento
CRS_CALCULO = "EPSG:32614"         # UTM 14N para calculos metricos
AREA_MINIMA_KM2 = 0.001            # Umbral minimo de area en km2
PERCENTIL_OUTLIERS = 0.99          # Percentil para filtrar outliers de densidad
ANIO = 2020                        # Anio del censo


# ──────────────────────────────────────────────
# Funciones auxiliares de geometria
# ──────────────────────────────────────────────
def a_poligono(geometria):
    """
    Convierte geometrias complejas (MultiPolygon, GeometryCollection)
    al poligono de mayor area. Retorna None si no es posible.
    """
    try:
        if isinstance(geometria, Polygon):
            return geometria
        elif isinstance(geometria, MultiPolygon):
            return max(geometria.geoms, key=lambda g: g.area)
        elif isinstance(geometria, GeometryCollection):
            poligonos = [g for g in geometria.geoms if isinstance(g, Polygon)]
            if poligonos:
                return max(poligonos, key=lambda g: g.area)
            logger.warning("GeometryCollection sin poligonos, se omitira.")
            return None
        else:
            return None
    except Exception as e:
        logger.warning(f"Error procesando geometria: {e}")
        return None


def limpiar_geometrias(gdf):
    """
    Limpia y normaliza geometrias:
    - Filtra solo Polygon, MultiPolygon y GeometryCollection
    - Convierte a Polygon simple (mayor area)
    - Repara geometrias invalidas con buffer(0)
    - Elimina geometrias vacias o nulas
    """
    tipos_validos = ['Polygon', 'MultiPolygon', 'GeometryCollection']
    gdf = gdf[gdf.geometry.type.isin(tipos_validos)].copy()
    gdf['geometry'] = gdf['geometry'].apply(a_poligono)
    gdf = gdf[~gdf['geometry'].isnull()].copy()
    gdf['geometry'] = gdf['geometry'].buffer(0)
    gdf = gdf[~gdf['geometry'].is_empty]
    return gdf


def calcular_area_densidad(gdf, columna_poblacion, columna_densidad):
    """
    Calcula area en km2 y densidad de poblacion.
    Reproyecta a UTM 14N para calculos metricos.
    """
    gdf = gdf.to_crs(CRS_CALCULO)
    gdf['area_km2'] = gdf.geometry.area / 1e6
    gdf['area_km2'] = gdf['area_km2'].replace(0, np.nan)
    gdf[columna_densidad] = gdf[columna_poblacion] / gdf['area_km2']
    gdf[columna_densidad] = gdf[columna_densidad].fillna(0)
    return gdf


# ──────────────────────────────────────────────
# Funciones principales del ETL
# ──────────────────────────────────────────────
def cargar_shapefiles(directorio_datos):
    """
    Paso 1: Carga los tres shapefiles de poblacion.
    Retorna un GeoDataFrame con columnas pob_total, pob_hombres, pob_mujeres.
    """
    total_shp = os.path.join(directorio_datos, "total.shp")
    hombres_shp = os.path.join(directorio_datos, "hombres.shp")
    mujeres_shp = os.path.join(directorio_datos, "mujeres.shp")

    # Verificar que existan los archivos
    for archivo in [total_shp, hombres_shp, mujeres_shp]:
        if not os.path.exists(archivo):
            logger.error(f"Archivo no encontrado: {archivo}")
            sys.exit(1)

    logger.info("Cargando shapefiles de poblacion...")
    gdf_total = gpd.read_file(total_shp).rename(columns={'pob': 'pob_total'})
    gdf_hombres = gpd.read_file(hombres_shp).rename(columns={'pob': 'pob_hombres'})
    gdf_mujeres = gpd.read_file(mujeres_shp).rename(columns={'pob': 'pob_mujeres'})

    logger.info(f"  total.shp: {len(gdf_total)} registros")
    logger.info(f"  hombres.shp: {len(gdf_hombres)} registros")
    logger.info(f"  mujeres.shp: {len(gdf_mujeres)} registros")

    # Merge por columna 'ageb'
    logger.info("Uniendo datos de poblacion por 'ageb'...")
    gdf = gdf_total.merge(
        gdf_hombres[['ageb', 'pob_hombres']], on='ageb', how='left'
    )
    gdf = gdf.merge(
        gdf_mujeres[['ageb', 'pob_mujeres']], on='ageb', how='left'
    )
    logger.info(f"  Registros despues de unir: {len(gdf)}")

    return gdf


def limpiar_datos_poblacion(gdf):
    """
    Pasos 3-5: Limpieza de datos de poblacion.
    - Elimina nulos
    - Verifica consistencia hombres + mujeres = total
    - Elimina duplicados
    """
    logger.info("Limpiando datos de poblacion...")

    # Eliminar nulos en columnas de poblacion
    antes = len(gdf)
    gdf = gdf.dropna(subset=['pob_total', 'pob_hombres', 'pob_mujeres'])
    logger.info(f"  Registros eliminados por nulos: {antes - len(gdf)}")

    # Convertir a enteros
    gdf[['pob_total', 'pob_hombres', 'pob_mujeres']] = \
        gdf[['pob_total', 'pob_hombres', 'pob_mujeres']].astype(int)

    # Verificar consistencia: pob_total == pob_hombres + pob_mujeres
    gdf['pob_total_calc'] = gdf['pob_hombres'] + gdf['pob_mujeres']
    inconsistentes = len(gdf[gdf['pob_total'] != gdf['pob_total_calc']])
    if inconsistentes > 0:
        logger.warning(f"  Registros con inconsistencia en poblacion: {inconsistentes}")
        logger.info("  Ajustando pob_total = pob_hombres + pob_mujeres")
        gdf.loc[
            gdf['pob_total'] != gdf['pob_total_calc'],
            'pob_total'
        ] = gdf['pob_total_calc']
    gdf = gdf.drop(columns=['pob_total_calc'])

    # Eliminar duplicados por AGEB
    antes = len(gdf)
    gdf = gdf.drop_duplicates(subset='ageb')
    logger.info(f"  Duplicados eliminados: {antes - len(gdf)}")
    logger.info(f"  Registros finales: {len(gdf)}")

    return gdf


def filtrar_coyoacan(gdf, ruta_alcaldias):
    """
    Paso 6: Filtra datos al poligono de Coyoacan mediante clip espacial.
    """
    logger.info("Filtrando datos al poligono de Coyoacan...")

    if not os.path.exists(ruta_alcaldias):
        logger.error(f"Shapefile de alcaldias no encontrado: {ruta_alcaldias}")
        sys.exit(1)

    gdf_alcaldias = gpd.read_file(ruta_alcaldias)
    gdf_coyoacan = gdf_alcaldias[gdf_alcaldias['NOMGEO'] == 'Coyoacan']

    if gdf_coyoacan.empty:
        # Intentar con acento
        gdf_coyoacan = gdf_alcaldias[gdf_alcaldias['NOMGEO'] == 'Coyoacán']

    if gdf_coyoacan.empty:
        logger.error("No se encontro el poligono de Coyoacan en el shapefile de alcaldias.")
        logger.info(f"  Valores disponibles en NOMGEO: {gdf_alcaldias['NOMGEO'].unique()}")
        sys.exit(1)

    # Asegurar CRS compatibles
    if gdf.crs != gdf_coyoacan.crs:
        gdf_coyoacan = gdf_coyoacan.to_crs(gdf.crs)

    gdf_clipped = gpd.clip(gdf, gdf_coyoacan)
    logger.info(f"  Registros despues de filtrar a Coyoacan: {len(gdf_clipped)}")

    return gdf_clipped


def procesar_geometrias_y_densidades(gdf):
    """
    Pasos 7-10: Limpieza de geometrias, calculo de densidades,
    filtrado por area minima y outliers.
    """
    # Limpiar geometrias
    logger.info("Limpiando geometrias...")
    gdf = limpiar_geometrias(gdf)
    logger.info(f"  Registros despues de limpiar geometrias: {len(gdf)}")

    # Calcular area y densidades
    logger.info("Calculando area y densidades de poblacion...")
    gdf = calcular_area_densidad(gdf, 'pob_total', 'densidad_pob_total')
    gdf = calcular_area_densidad(gdf, 'pob_hombres', 'densidad_hombres')
    gdf = calcular_area_densidad(gdf, 'pob_mujeres', 'densidad_mujeres')

    # Filtrar por area minima
    antes = len(gdf)
    gdf = gdf[gdf['area_km2'] > AREA_MINIMA_KM2]
    logger.info(f"  Registros eliminados por area < {AREA_MINIMA_KM2} km2: {antes - len(gdf)}")

    # Recalcular densidades despues de filtrar
    gdf = calcular_area_densidad(gdf, 'pob_total', 'densidad_pob_total')
    gdf = calcular_area_densidad(gdf, 'pob_hombres', 'densidad_hombres')
    gdf = calcular_area_densidad(gdf, 'pob_mujeres', 'densidad_mujeres')

    # Filtrar outliers de densidad (percentil 99)
    umbral_densidad = gdf['densidad_pob_total'].quantile(PERCENTIL_OUTLIERS)
    antes = len(gdf)
    gdf = gdf[gdf['densidad_pob_total'] <= umbral_densidad]
    logger.info(f"  Registros eliminados por outliers de densidad (>{umbral_densidad:.0f}): {antes - len(gdf)}")

    logger.info(f"  Registros finales: {len(gdf)}")
    return gdf


def preparar_para_carga(gdf, anio=ANIO):
    """
    Paso 11: Prepara el GeoDataFrame para subir a PostGIS.
    - Agrega columna anio
    - Reproyecta a WGS84 (EPSG:4326) para almacenamiento
    - Asegura que la columna de join sea 'ageb'
    """
    logger.info("Preparando datos para carga a PostGIS...")

    # Agregar anio
    gdf['anio'] = anio

    # Reproyectar a WGS84 para almacenamiento
    gdf = gdf.to_crs(CRS_ALMACENAMIENTO)

    # Verificar que la columna 'ageb' exista (clave de join con poligonos)
    if 'ageb' not in gdf.columns:
        # Puede que se llame CVE_AGEB en los datos originales
        if 'CVE_AGEB' in gdf.columns:
            logger.info("  Renombrando CVE_AGEB -> ageb para compatibilidad")
            gdf = gdf.rename(columns={'CVE_AGEB': 'ageb'})

    # Mostrar columnas finales
    logger.info(f"  Columnas finales: {list(gdf.columns)}")
    logger.info(f"  CRS: {gdf.crs}")
    logger.info(f"  Total de registros: {len(gdf)}")

    # Estadisticas resumidas
    logger.info("  --- Estadisticas de poblacion ---")
    for col in ['pob_total', 'pob_hombres', 'pob_mujeres']:
        if col in gdf.columns:
            logger.info(f"    {col}: min={gdf[col].min()}, max={gdf[col].max()}, "
                        f"media={gdf[col].mean():.1f}")

    logger.info("  --- Estadisticas de densidad ---")
    for col in ['densidad_pob_total', 'densidad_hombres', 'densidad_mujeres']:
        if col in gdf.columns:
            logger.info(f"    {col}: min={gdf[col].min():.1f}, max={gdf[col].max():.1f}, "
                        f"media={gdf[col].mean():.1f}")

    return gdf


# ──────────────────────────────────────────────
# Punto de entrada
# ──────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="ETL de datos demograficos INEGI 2020 para Coyoacan -> Neon PostGIS"
    )
    parser.add_argument(
        "directorio_datos",
        help="Ruta al directorio con shapefiles INEGI (total.shp, hombres.shp, mujeres.shp)"
    )
    parser.add_argument(
        "ruta_alcaldias",
        help="Ruta al shapefile de alcaldias de la CDMX (poligonos_alcaldias_cdmx.shp)"
    )
    parser.add_argument(
        "--anio",
        type=int,
        default=ANIO,
        help=f"Anio del censo (por defecto: {ANIO})"
    )
    parser.add_argument(
        "--reemplazar",
        action="store_true",
        help="Si se especifica, reemplaza los datos existentes en la tabla (if_exists='replace'). "
             "Por defecto agrega (append)."
    )

    args = parser.parse_args()

    # Cargar variables de entorno
    # Buscar .env en la raiz del proyecto
    ruta_proyecto = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ruta_env = os.path.join(ruta_proyecto, '.env')
    load_dotenv(ruta_env)
    logger.info(f"Archivo .env cargado desde: {ruta_env}")

    # Construir URI de conexion
    database_uri = os.getenv('DATABASE_URI')
    if not database_uri:
        # Construir desde variables individuales
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

    logger.info(f"Conectando a la base de datos...")
    engine = create_engine(database_uri)

    # Verificar conexion
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("  Conexion exitosa a Neon PostGIS.")
    except Exception as e:
        logger.error(f"  No se pudo conectar a la base de datos: {e}")
        sys.exit(1)

    # Actualizar anio si se especifico
    anio = args.anio

    # ── Pipeline ETL ──
    logger.info("=" * 60)
    logger.info(f"INICIO ETL DEMOGRAFICOS - Censo INEGI {anio}")
    logger.info(f"Directorio de datos: {args.directorio_datos}")
    logger.info(f"Shapefile de alcaldias: {args.ruta_alcaldias}")
    logger.info("=" * 60)

    # 1. Cargar shapefiles
    gdf = cargar_shapefiles(args.directorio_datos)

    # 2. Limpiar datos de poblacion
    gdf = limpiar_datos_poblacion(gdf)

    # 3. Filtrar a Coyoacan
    gdf = filtrar_coyoacan(gdf, args.ruta_alcaldias)

    # 4. Limpiar geometrias y calcular densidades
    gdf = procesar_geometrias_y_densidades(gdf)

    # 5. Preparar para carga
    gdf = preparar_para_carga(gdf, anio=anio)

    # 6. Subir a Neon
    modo = 'replace' if args.reemplazar else 'append'
    if args.reemplazar:
        logger.warning("Modo REEMPLAZAR activado: se eliminaran datos previos de la tabla.")
    subir_a_neon_con_modo(gdf, engine, modo)

    logger.info("=" * 60)
    logger.info("ETL DEMOGRAFICOS COMPLETADO EXITOSAMENTE")
    logger.info(f"  Registros cargados: {len(gdf)}")
    logger.info(f"  Tabla destino: {TABLA_DESTINO}")
    logger.info("=" * 60)


def subir_a_neon_con_modo(gdf, engine, modo='append'):
    """
    Sube el GeoDataFrame a Neon PostGIS con el modo especificado.
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


if __name__ == "__main__":
    main()
