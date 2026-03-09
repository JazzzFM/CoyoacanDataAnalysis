#!/usr/bin/env python3
# scripts/etl_resultados_electorales.py

"""
ETL para resultados electorales 2024 (votos por seccion).

Procesa dos fuentes de datos:
  1. IECM (bd2024alccas.xlsx): Resultados de la eleccion de Alcaldias
  2. INE  (DIP_FED_2024.csv):  Resultados de Diputaciones Federales (computos)

Agrega los votos por seccion y enriquece la tabla `datos_electorales`
(que ya contiene los poligonos de secciones cargados por etl_electorales.py).

Uso:
    python scripts/etl_resultados_electorales.py \\
        --iecm data/electoral/resultados/bd2024alccas.xlsx \\
        --ine  data/electoral/resultados/DIP_FED_2024.csv

Requiere:
    - Tabla `datos_electorales` ya cargada con poligonos de secciones
    - Archivo .env con DATABASE_URI
    - openpyxl instalado (pip install openpyxl)
"""

import sys
import os
import argparse
import logging
import pandas as pd
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
CVE_ENTIDAD_CDMX = 9

# Partidos individuales (orden estandar)
PARTIDOS = ['PAN', 'PRI', 'PRD', 'PVEM', 'PT', 'MC', 'MORENA']

# Coaliciones 2024
COALICIONES = [
    'PAN_PRI_PRD', 'PAN_PRI', 'PAN_PRD', 'PRI_PRD',
    'PVEM_PT_MORENA', 'PVEM_PT', 'PVEM_MORENA', 'PT_MORENA'
]


# ──────────────────────────────────────────────
# Funciones ETL
# ──────────────────────────────────────────────
def cargar_secciones_existentes(engine):
    """
    Carga las secciones de Coyoacan ya almacenadas en PostGIS.
    Retorna un GeoDataFrame con la geometria y columnas base.
    """
    logger.info(f"Cargando secciones existentes de '{TABLA_DESTINO}'...")

    try:
        gdf = gpd.read_postgis(
            f"SELECT * FROM {TABLA_DESTINO}",
            con=engine,
            geom_col="geometry"
        )
        logger.info(f"  Secciones cargadas: {len(gdf)}")
        return gdf
    except Exception as e:
        logger.error(f"  Error al cargar secciones: {e}")
        logger.error("  Ejecute primero: python scripts/etl_electorales.py")
        sys.exit(1)


def procesar_iecm(ruta_xlsx, secciones_coyoacan):
    """
    Procesa el archivo IECM de resultados de alcaldias.
    Filtra Coyoacan, agrega votos por seccion.
    """
    logger.info(f"Procesando IECM: {ruta_xlsx}")

    df = pd.read_excel(ruta_xlsx, header=8)
    logger.info(f"  Total filas (todas las alcaldias): {len(df)}")

    # Filtrar Coyoacan
    df = df[df['Demarcación territorial'] == 'Coyoacán'].copy()
    logger.info(f"  Filas Coyoacán: {len(df)}")
    logger.info(f"  Secciones únicas: {df['Sección electoral'].nunique()}")

    # Columnas de votos a sumar
    cols_votos = [c for c in PARTIDOS if c in df.columns]
    cols_coaliciones = [c for c in COALICIONES if c in df.columns]
    cols_extra = []
    for c in ['CSP', 'Votos candidatos no registrados', 'Votos nulos',
              'Votos totales', 'Lista nominal']:
        if c in df.columns:
            cols_extra.append(c)

    todas_cols = cols_votos + cols_coaliciones + cols_extra

    # Convertir a numerico (pueden tener valores no numericos)
    for col in todas_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    # Agregar por seccion (sumar casillas)
    agg = df.groupby('Sección electoral')[todas_cols].sum().reset_index()
    agg = agg.rename(columns={'Sección electoral': 'seccion'})

    # Renombrar columnas con prefijo alc_ para distinguir de federal
    rename_map = {}
    for col in cols_votos + cols_coaliciones:
        rename_map[col] = f'alc_{col.lower()}'
    rename_map['Votos candidatos no registrados'] = 'alc_cnr'
    rename_map['Votos nulos'] = 'alc_votos_nulos'
    rename_map['Votos totales'] = 'alc_votos_totales'
    rename_map['Lista nominal'] = 'alc_lista_nominal'
    if 'CSP' in rename_map:
        rename_map['CSP'] = 'alc_csp'

    agg = agg.rename(columns=rename_map)

    # Filtrar solo secciones de Coyoacan
    agg = agg[agg['seccion'].isin(secciones_coyoacan)]
    logger.info(f"  Secciones procesadas (IECM): {len(agg)}")

    # Calcular participacion
    if 'alc_votos_totales' in agg.columns and 'alc_lista_nominal' in agg.columns:
        agg['alc_participacion'] = (
            agg['alc_votos_totales'] / agg['alc_lista_nominal'] * 100
        ).round(2)

    # Partido ganador por seccion
    cols_partidos_alc = [f'alc_{p.lower()}' for p in PARTIDOS if f'alc_{p.lower()}' in agg.columns]
    cols_coaliciones_alc = [f'alc_{c.lower()}' for c in COALICIONES if f'alc_{c.lower()}' in agg.columns]

    # Sumar votos de coalicion a sus partidos componentes para determinar ganador
    agg['alc_fuerza_morena'] = agg.get('alc_morena', 0) + agg.get('alc_pvem', 0) + \
                                agg.get('alc_pt', 0) + agg.get('alc_pvem_pt_morena', 0) + \
                                agg.get('alc_pvem_pt', 0) + agg.get('alc_pvem_morena', 0) + \
                                agg.get('alc_pt_morena', 0)
    agg['alc_fuerza_pan'] = agg.get('alc_pan', 0) + agg.get('alc_pri', 0) + \
                             agg.get('alc_prd', 0) + agg.get('alc_pan_pri_prd', 0) + \
                             agg.get('alc_pan_pri', 0) + agg.get('alc_pan_prd', 0) + \
                             agg.get('alc_pri_prd', 0)
    agg['alc_fuerza_mc'] = agg.get('alc_mc', 0)

    def ganador_alc(row):
        fuerzas = {
            'MORENA+': row['alc_fuerza_morena'],
            'PAN+': row['alc_fuerza_pan'],
            'MC': row['alc_fuerza_mc']
        }
        return max(fuerzas, key=fuerzas.get)

    agg['alc_ganador'] = agg.apply(ganador_alc, axis=1)

    return agg


def procesar_ine(ruta_csv, secciones_coyoacan):
    """
    Procesa el archivo INE de computos de diputaciones federales.
    Filtra CDMX, cruza con secciones de Coyoacan, agrega por seccion.
    """
    logger.info(f"Procesando INE: {ruta_csv}")

    df = pd.read_csv(ruta_csv, encoding='latin1', sep='|',
                     skiprows=7, header=0, dtype=str, low_memory=False)
    logger.info(f"  Total filas (nacional): {len(df)}")

    # Limpiar formato ="XX" de columnas clave
    for col in ['ID_ENTIDAD', 'SECCION', 'ID_DISTRITO_FEDERAL']:
        df[col] = df[col].str.strip('="').astype(int)

    # Filtrar CDMX
    df = df[df['ID_ENTIDAD'] == CVE_ENTIDAD_CDMX].copy()
    logger.info(f"  Filas CDMX: {len(df)}")

    # Filtrar solo secciones de Coyoacan
    df = df[df['SECCION'].isin(secciones_coyoacan)].copy()
    logger.info(f"  Filas secciones Coyoacán: {len(df)}")
    logger.info(f"  Secciones únicas: {df['SECCION'].nunique()}")

    # Columnas de votos
    cols_votos = [c for c in PARTIDOS if c in df.columns]
    cols_coaliciones = [c for c in COALICIONES if c in df.columns]
    cols_extra_raw = {
        'CANDIDATO/A NO REGISTRADO/A': 'fed_cnr',
        'VOTOS NULOS': 'fed_votos_nulos',
        'TOTAL_VOTOS_CALCULADOS': 'fed_votos_totales',
        'LISTA_NOMINAL': 'fed_lista_nominal'
    }
    cols_extra = [c for c in cols_extra_raw.keys() if c in df.columns]

    todas_cols = cols_votos + cols_coaliciones + cols_extra

    # Convertir a numerico
    for col in todas_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    # Agregar por seccion
    agg = df.groupby('SECCION')[todas_cols].sum().reset_index()
    agg = agg.rename(columns={'SECCION': 'seccion'})

    # Renombrar con prefijo fed_
    rename_map = {}
    for col in cols_votos + cols_coaliciones:
        rename_map[col] = f'fed_{col.lower()}'
    for raw_name, new_name in cols_extra_raw.items():
        if raw_name in agg.columns:
            rename_map[raw_name] = new_name

    agg = agg.rename(columns=rename_map)

    logger.info(f"  Secciones procesadas (INE): {len(agg)}")

    # Calcular participacion
    if 'fed_votos_totales' in agg.columns and 'fed_lista_nominal' in agg.columns:
        agg['fed_participacion'] = (
            agg['fed_votos_totales'] / agg['fed_lista_nominal'] * 100
        ).round(2)

    # Partido ganador federal
    agg['fed_fuerza_morena'] = agg.get('fed_morena', 0) + agg.get('fed_pvem', 0) + \
                                agg.get('fed_pt', 0) + agg.get('fed_pvem_pt_morena', 0) + \
                                agg.get('fed_pvem_pt', 0) + agg.get('fed_pvem_morena', 0) + \
                                agg.get('fed_pt_morena', 0)
    agg['fed_fuerza_pan'] = agg.get('fed_pan', 0) + agg.get('fed_pri', 0) + \
                             agg.get('fed_prd', 0) + agg.get('fed_pan_pri_prd', 0) + \
                             agg.get('fed_pan_pri', 0) + agg.get('fed_pan_prd', 0) + \
                             agg.get('fed_pri_prd', 0)
    agg['fed_fuerza_mc'] = agg.get('fed_mc', 0)

    def ganador_fed(row):
        fuerzas = {
            'MORENA+': row['fed_fuerza_morena'],
            'PAN+': row['fed_fuerza_pan'],
            'MC': row['fed_fuerza_mc']
        }
        return max(fuerzas, key=fuerzas.get)

    agg['fed_ganador'] = agg.apply(ganador_fed, axis=1)

    return agg


def merge_y_subir(gdf_secciones, df_iecm, df_ine, engine):
    """
    Une los resultados IECM e INE con las secciones y sube a PostGIS.
    """
    logger.info("Uniendo resultados con secciones...")

    # Merge IECM (alcaldia)
    gdf = gdf_secciones.merge(df_iecm, on='seccion', how='left')
    logger.info(f"  Despues de merge IECM: {len(gdf)} filas, "
                f"{gdf.columns.tolist()}")

    # Merge INE (federal)
    gdf = gdf.merge(df_ine, on='seccion', how='left')
    logger.info(f"  Despues de merge INE: {len(gdf)} filas")

    # Estadisticas
    cols_alc = [c for c in gdf.columns if c.startswith('alc_')]
    cols_fed = [c for c in gdf.columns if c.startswith('fed_')]
    logger.info(f"  Columnas alcaldia: {len(cols_alc)}")
    logger.info(f"  Columnas federal: {len(cols_fed)}")

    if 'alc_ganador' in gdf.columns:
        logger.info("  --- Ganadores Alcaldia por seccion ---")
        for g, n in gdf['alc_ganador'].value_counts().items():
            logger.info(f"    {g}: {n} secciones")

    if 'fed_ganador' in gdf.columns:
        logger.info("  --- Ganadores Federal por seccion ---")
        for g, n in gdf['fed_ganador'].value_counts().items():
            logger.info(f"    {g}: {n} secciones")

    if 'alc_participacion' in gdf.columns:
        logger.info(f"  Participacion alcaldia: "
                    f"min={gdf['alc_participacion'].min():.1f}%, "
                    f"max={gdf['alc_participacion'].max():.1f}%, "
                    f"media={gdf['alc_participacion'].mean():.1f}%")

    # Subir a PostGIS (reemplaza la tabla)
    logger.info(f"Subiendo {len(gdf)} secciones enriquecidas a '{TABLA_DESTINO}'...")
    gdf.to_postgis(
        name=TABLA_DESTINO,
        con=engine,
        if_exists='replace',
        index=False
    )
    logger.info(f"  Datos subidos exitosamente.")

    return gdf


# ──────────────────────────────────────────────
# Punto de entrada
# ──────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="ETL de resultados electorales 2024 -> Neon PostGIS"
    )
    parser.add_argument(
        "--iecm",
        required=True,
        help="Ruta al archivo XLSX de resultados de alcaldias (bd2024alccas.xlsx)"
    )
    parser.add_argument(
        "--ine",
        required=True,
        help="Ruta al archivo CSV de computos INE (DIP_FED_2024.csv)"
    )

    args = parser.parse_args()

    # Verificar archivos
    for ruta, nombre in [(args.iecm, 'IECM'), (args.ine, 'INE')]:
        if not os.path.exists(ruta):
            logger.error(f"Archivo {nombre} no encontrado: {ruta}")
            sys.exit(1)

    # Cargar variables de entorno
    ruta_proyecto = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ruta_env = os.path.join(ruta_proyecto, '.env')
    load_dotenv(ruta_env)

    database_uri = os.getenv('DATABASE_URI')
    if not database_uri:
        db_user = os.getenv('DB_USER', 'neondb_owner')
        db_password = os.getenv('DB_PASSWORD')
        db_host = os.getenv('DB_HOST')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME', 'neondb')

        if not db_password or not db_host:
            logger.error("Faltan variables de entorno.")
            sys.exit(1)

        database_uri = (
            f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            f"?sslmode=require"
        )

    engine = create_engine(database_uri)

    # Verificar conexion
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Conexion exitosa a Neon PostGIS.")
    except Exception as e:
        logger.error(f"No se pudo conectar: {e}")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("INICIO ETL RESULTADOS ELECTORALES 2024")
    logger.info("=" * 60)

    # 1. Cargar secciones existentes
    gdf_secciones = cargar_secciones_existentes(engine)
    secciones_coyoacan = set(gdf_secciones['seccion'].unique())
    logger.info(f"  Secciones de referencia: {len(secciones_coyoacan)}")

    # 2. Procesar IECM (alcaldia)
    df_iecm = procesar_iecm(args.iecm, secciones_coyoacan)

    # 3. Procesar INE (federal)
    df_ine = procesar_ine(args.ine, secciones_coyoacan)

    # 4. Merge y subir
    gdf_final = merge_y_subir(gdf_secciones, df_iecm, df_ine, engine)

    logger.info("=" * 60)
    logger.info("ETL RESULTADOS ELECTORALES COMPLETADO")
    logger.info(f"  Secciones enriquecidas: {len(gdf_final)}")
    logger.info(f"  Columnas totales: {len(gdf_final.columns)}")
    logger.info(f"  Tabla: {TABLA_DESTINO}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
