#!/usr/bin/env python3
# scripts/etl_demograficos.py

"""
ETL para datos demograficos del censo INEGI 2020.

Carga el CSV de datos abiertos por AGEB (INEGI) y los poligonos AGEB (CDMX),
hace merge por clave AGEB, filtra Coyoacan, calcula densidades
y sube los datos procesados a `datos_demograficos_particionada` en Neon PostGIS.

Uso:
    python scripts/etl_demograficos.py data/demografico/2020/ageb_mza_urbana_09_cpv2020/conjunto_de_datos/conjunto_de_datos_ageb_urbana_09_cpv2020.csv data/demografico/2020/poligono_ageb_urbanas_cdmx.shp

Requiere:
    - Archivo .env en la raiz del proyecto con DATABASE_URI
    - Python con geopandas, pandas, sqlalchemy, psycopg2-binary, python-dotenv
"""

import sys
import os
import argparse
import logging
import numpy as np
import pandas as pd
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
CVE_ENT_CDMX = "09"
CVE_MUN_COYOACAN = "003"


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
def cargar_csv_y_poligonos(ruta_csv, ruta_shapefile):
    """
    Paso 1: Carga el CSV de datos abiertos INEGI y los poligonos AGEB.
    Filtra a nivel AGEB (NOM_LOC == 'Total AGEB urbana') y Coyoacan (MUN == 003).
    Hace merge con los poligonos por clave AGEB.
    Retorna un GeoDataFrame con columnas pob_total, pob_hombres, pob_mujeres + geometry.
    """
    logger.info(f"Cargando CSV de censo: {ruta_csv}")
    for archivo in [ruta_csv, ruta_shapefile]:
        if not os.path.exists(archivo):
            logger.error(f"Archivo no encontrado: {archivo}")
            sys.exit(1)

    # Cargar CSV y filtrar Coyoacan a nivel AGEB
    df = pd.read_csv(ruta_csv, dtype={'ENTIDAD': str, 'MUN': str, 'AGEB': str})
    logger.info(f"  Total registros CDMX: {len(df)}")

    # Normalizar claves a strings con padding
    df['ENTIDAD'] = df['ENTIDAD'].str.zfill(2)
    df['MUN'] = df['MUN'].str.zfill(3)
    df['AGEB'] = df['AGEB'].str.zfill(4)

    # Filtrar: Coyoacan + nivel AGEB (NOM_LOC == 'Total AGEB urbana')
    df_coyoacan = df[
        (df['ENTIDAD'] == CVE_ENT_CDMX) &
        (df['MUN'] == CVE_MUN_COYOACAN) &
        (df['NOM_LOC'] == 'Total AGEB urbana')
    ].copy()
    logger.info(f"  AGEBs en Coyoacan: {len(df_coyoacan)}")

    # Renombrar columnas de poblacion
    df_coyoacan = df_coyoacan.rename(columns={
        'POBTOT': 'pob_total',
        'POBMAS': 'pob_hombres',
        'POBFEM': 'pob_mujeres',
    })

    # Convertir poblacion a numerico (INEGI usa '*' para datos confidenciales)
    for col in ['pob_total', 'pob_hombres', 'pob_mujeres']:
        df_coyoacan[col] = pd.to_numeric(df_coyoacan[col], errors='coerce')

    # Cargar poligonos AGEB
    logger.info(f"Cargando poligonos AGEB: {ruta_shapefile}")
    gdf_poligonos = gpd.read_file(ruta_shapefile)
    gdf_poligonos_coy = gdf_poligonos[
        gdf_poligonos['CVE_MUN'] == CVE_MUN_COYOACAN
    ].copy()
    logger.info(f"  Poligonos AGEB en Coyoacan: {len(gdf_poligonos_coy)}")

    # Merge: CSV (AGEB) + Poligonos (CVE_AGEB)
    logger.info("Uniendo datos tabulares con poligonos por clave AGEB...")
    gdf = gdf_poligonos_coy.merge(
        df_coyoacan[['AGEB', 'pob_total', 'pob_hombres', 'pob_mujeres']],
        left_on='CVE_AGEB',
        right_on='AGEB',
        how='inner'
    )
    logger.info(f"  Registros despues del merge: {len(gdf)}")

    # Renombrar CVE_AGEB -> ageb para compatibilidad con el dashboard
    gdf = gdf.rename(columns={'CVE_AGEB': 'ageb'})
    gdf = gdf.drop(columns=['AGEB'], errors='ignore')

    return gdf


def limpiar_datos_poblacion(gdf):
    """
    Limpieza de datos de poblacion.
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


def procesar_geometrias_y_densidades(gdf):
    """
    Limpieza de geometrias, calculo de densidades,
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
    Prepara el GeoDataFrame para subir a PostGIS.
    - Agrega columna anio
    - Reproyecta a WGS84 (EPSG:4326) para almacenamiento
    - Selecciona columnas finales
    """
    logger.info("Preparando datos para carga a PostGIS...")

    # Agregar anio
    gdf['anio'] = anio

    # Reproyectar a WGS84 para almacenamiento
    gdf = gdf.to_crs(CRS_ALMACENAMIENTO)

    # Eliminar columnas auxiliares del shapefile que no necesitamos
    columnas_a_eliminar = ['CVEGEO', 'CVE_ENT', 'CVE_MUN', 'CVE_LOC', 'index_right']
    gdf = gdf.drop(columns=[c for c in columnas_a_eliminar if c in gdf.columns])

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


def subir_a_neon(gdf, engine, modo='append'):
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


# ──────────────────────────────────────────────
# Punto de entrada
# ──────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="ETL de datos demograficos INEGI 2020 para Coyoacan -> Neon PostGIS"
    )
    parser.add_argument(
        "ruta_csv",
        help="Ruta al CSV de datos abiertos INEGI (conjunto_de_datos_ageb_urbana_09_cpv2020.csv)"
    )
    parser.add_argument(
        "ruta_poligonos",
        help="Ruta al shapefile de poligonos AGEB (poligono_ageb_urbanas_cdmx.shp)"
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
    logger.info(f"INICIO ETL DEMOGRAFICOS - Censo INEGI {anio}")
    logger.info(f"CSV de datos: {args.ruta_csv}")
    logger.info(f"Poligonos AGEB: {args.ruta_poligonos}")
    logger.info("=" * 60)

    # 1. Cargar CSV + poligonos y hacer merge
    gdf = cargar_csv_y_poligonos(args.ruta_csv, args.ruta_poligonos)

    # 2. Limpiar datos de poblacion
    gdf = limpiar_datos_poblacion(gdf)

    # 3. Limpiar geometrias y calcular densidades
    gdf = procesar_geometrias_y_densidades(gdf)

    # 4. Preparar para carga
    gdf = preparar_para_carga(gdf, anio=anio)

    # 5. Subir a Neon
    modo = 'replace' if args.reemplazar else 'append'
    if args.reemplazar:
        logger.warning("Modo REEMPLAZAR activado: se eliminaran datos previos de la tabla.")
    subir_a_neon(gdf, engine, modo)

    logger.info("=" * 60)
    logger.info("ETL DEMOGRAFICOS COMPLETADO EXITOSAMENTE")
    logger.info(f"  Registros cargados: {len(gdf)}")
    logger.info(f"  Tabla destino: {TABLA_DESTINO}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
