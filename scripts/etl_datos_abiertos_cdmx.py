#!/usr/bin/env python3
# scripts/etl_datos_abiertos_cdmx.py

"""
ETL para datasets de datos abiertos CDMX (datos.cdmx.gob.mx).

Carga 7 shapefiles tematicos por colonia, filtra Coyoacan, y los une
en una sola tabla `datos_indicadores_colonia` en Neon PostGIS.

Uso:
    python scripts/etl_datos_abiertos_cdmx.py --reemplazar

Requiere:
    - Shapefiles descargados en data/datos_abiertos_cdmx/
    - Archivo .env con DATABASE_URI
"""

import sys
import os
import argparse
import logging
import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from functools import reduce

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

TABLA_DESTINO = "datos_indicadores_colonia"
CRS_ALMACENAMIENTO = "EPSG:4326"
BASE_DIR = "data/datos_abiertos_cdmx"

# Definicion de datasets: ruta relativa, columna filtro, columnas a extraer, renombramientos
DATASETS = {
    "incremento_pob": {
        "shp": "incremento_pob_vivienda/incremento_absoluto_pob/rc_9.shp",
        "filtro_col": "alcaldia",
        "filtro_val": "COYOACAN",
        "cols_id": ["colonia", "cve_col"],
        "cols_datos": {
            "INCABSPOB": "incremento_abs_poblacion",
            "POBZCP00": "poblacion_2000",
            "POBZCP16": "poblacion_2016",
            "VIVZCP00": "viviendas_2000",
            "VIVZCP16": "viviendas_2016",
            "C_INCABPOB": "cat_incremento_pob",
            "PPVIVRUV": "pct_viv_ruv",
            "C_PPVIVRUV": "cat_viv_ruv",
        }
    },
    "viv_desocupadas": {
        "shp": "viviendas_desocupadas/viviendas_abandonadas/ri_7.shp",
        "filtro_col": "alcaldia",
        "filtro_val": "COYOACAN",
        "cols_id": ["colonia", "cve_col"],
        "cols_datos": {
            "VIVDES": "viviendas_desocupadas",
            "VIV2010": "viviendas_total_2010",
            "P_VIVDESO": "pct_viviendas_desocupadas",
            "C_VIVDESO": "cat_viv_desocupadas",
            "DetVal": "deterioro_valor",
            "Cp_DETURB": "cat_deterioro_urbano",
        }
    },
    "densidad_hab": {
        "shp": "densidad_habitacional/densidad_vivha/ri_11.shp",
        "filtro_col": "alcaldia",
        "filtro_val": "COYOACAN",
        "cols_id": ["colonia", "cve_col"],
        "cols_datos": {
            "pob_2010": "poblacion_2010",
            "SUP_COL_M2": "superficie_colonia_m2",
            "VIV2010": "viviendas_2010",
            "DENVIVHa": "densidad_viv_ha",
            "C_DENVIVHa": "cat_densidad_viv",
        }
    },
    "areas_verdes": {
        "shp": "areas_verdes/ca_1.shp",
        "filtro_col": "alcaldia",
        "filtro_val": "COYOACAN",
        "cols_id": ["colonia", "cve_col"],
        "cols_datos": {
            "pob_2010": "av_poblacion_2010",
            "T_AV_M2": "area_verde_m2",
            "M2_AV_HAB": "m2_area_verde_hab",
            "C_M2AVHAB": "cat_area_verde",
        }
    },
    "espacio_publico": {
        "shp": "espacio_publico_m2/esppublico_habit.shp",
        "filtro_col": "alcaldia",
        "filtro_val": "COYOACAN",
        "cols_id": ["colonia", "cve_col"],
        "cols_datos": {
            "M2EspPub": "m2_espacio_pub_total",
            "m2EP_hab": "m2_espacio_pub_hab",
            "C_m2EPhab": "cat_espacio_pub",
        }
    },
    "marginalidad": {
        "shp": "marginalidad_violencia/urbanismo_social_sintesis.shp",
        "filtro_col": "alcaldia",
        "filtro_val": "COYOACAN",
        "cols_id": ["colonia", "cve_col"],
        "cols_datos": {
            "C_US": "cat_urbanismo_social",
        }
    },
    "sismica": {
        "shp": "zonificacion_sismica/sismos_col.shp",
        "filtro_col": "DELEG",
        "filtro_val": "COYOACAN",
        "cols_id": ["COLONIA"],
        "cols_datos": {
            "TAXONOMIA": "taxonomia_sismica",
            "INTENSIDAD": "intensidad_sismica",
            "DESCRIPCIO": "descripcion_sismica",
        },
        "rename_id": {"COLONIA": "colonia"},
    },
    "ue_turismo": {
        "shp": "ue_turismo/servicios_turismo/rc_8.shp",
        "filtro_col": "alcaldia",
        "filtro_val": "COYOACAN",
        "cols_id": ["colonia", "cve_col"],
        "cols_datos": {
            "NoSERVTUR": "num_servicios_turismo",
            "C_NoSERVTU": "cat_servicios_turismo",
        }
    },
    "calidad_vivienda": {
        "shp": "calidad_vivienda/calidad_espacios/us_7.shp",
        "filtro_col": "alcaldia",
        "filtro_val": "COYOACAN",
        "cols_id": ["colonia", "cve_col"],
        "cols_datos": {
            "ids_cev_su": "indice_calidad_viv_superior",
            "ids_cev_me": "indice_calidad_viv_media",
            "rangos_cc": "rango_calidad_vivienda",
            "C_IDS_cev": "cat_calidad_vivienda",
        }
    },
    "escuelas_basicas": {
        "shp": "escuelas_basicas/Equip_bаsico_educ.shp",
        "filtro_col": "alcaldia",
        "filtro_val": "COYOACAN",
        "cols_id": ["colonia", "cve_col"],
        "cols_datos": {
            "NoEqEduBas": "num_escuelas_basicas",
            "DisEqBas_m": "distancia_escuela_m",
            "C_EqEduBas": "cat_escuelas_basicas",
        }
    },
    "infra_peatonal": {
        "shp": "infra_peatonal/Nivel de presencia de infraestructura peatonal por colonia/Dist_acce_infra.shp",
        "filtro_col": "alcaldia",
        "filtro_val": "COYOACAN",
        "cols_id": ["colonia", "cve_col"],
        "cols_datos": {
            "INFRAPEAT": "infra_peatonal",
        }
    },
    "consumo_agua": {
        "shp": "consumo_agua/Consumo_hab_prom_agua_col.shp",
        "filtro_col": "alcaldia",
        "filtro_val": "COYOACAN",
        "cols_id": ["colonia", "cve_col"],
        "cols_datos": {
            "PROMVIVCON": "consumo_agua_prom_m3",
            "C_PROMVIVC": "cat_consumo_agua",
        }
    },
    "tasa_crecimiento": {
        "shp": "tasa_crecimiento/tasa_crecimiento_medio/tcma10_20.shp",
        "filtro_col": "alcaldia",
        "filtro_val": "COYOACAN",
        "cols_id": ["colonia", "cve_col"],
        "cols_datos": {
            "TCMA10_20": "tasa_crecimiento_2010_2020",
            "PobTot2020": "poblacion_2020",
            "DenPob20": "densidad_pob_2020",
            "DifDenPob": "dif_densidad_pob",
        }
    },
    "ue_comerciales": {
        "shp": "densidad_ue_comerciales/due_comerciales/ue_comerciales_colonia.shp",
        "filtro_col": "alcaldia",
        "filtro_val": "COYOACAN",
        "cols_id": ["colonia", "cve_col"],
        "cols_datos": {
            "ue": "ue_total",
            "com": "ue_comerciales",
            "ind": "ue_industriales",
            "serv": "ue_servicios",
        },
        "rename_id": {"nombre": "_drop_nombre_ue"},
    },
    "rezago_espacio_pub": {
        "shp_glob": "rezago_espacio_publico/**/rezago_esppublico.shp",
        "filtro_col": "nom_mun",
        "filtro_val": "COYOACAN",
        "cols_id": ["nombre"],
        "cols_datos": {
            "sumaval": "rezago_espacio_publico",
        },
        "rename_id": {"nombre": "colonia"},
    },
}


def procesar_dataset(nombre, config):
    """Carga un shapefile, filtra Coyoacan y extrae columnas relevantes."""
    import glob as globmod
    if "shp_glob" in config:
        encontrados = [r for r in globmod.glob(
            os.path.join(BASE_DIR, config["shp_glob"]), recursive=True)
            if '__MACOSX' not in r]
        ruta = encontrados[0] if encontrados else os.path.join(BASE_DIR, config.get("shp", ""))
    else:
        ruta = os.path.join(BASE_DIR, config["shp"])
        # Fallback: si la ruta no existe, buscar con glob (resuelve Unicode)
        if not os.path.exists(ruta):
            patron = os.path.join(os.path.dirname(ruta), "**",
                                  os.path.basename(ruta))
            encontrados = [r for r in globmod.glob(patron, recursive=True)
                           if '__MACOSX' not in r]
            if encontrados:
                ruta = encontrados[0]
    logger.info(f"  [{nombre}] Cargando: {ruta}")

    if not os.path.exists(ruta):
        logger.warning(f"  [{nombre}] NO ENCONTRADO, saltando.")
        return None

    try:
        gdf = gpd.read_file(ruta)
    except Exception:
        try:
            gdf = gpd.read_file(ruta, encoding='latin1')
        except Exception as e:
            logger.error(f"  [{nombre}] Error de lectura: {e}")
            return None

    # Filtrar Coyoacan
    col_filtro = config["filtro_col"]
    val_filtro = config["filtro_val"]

    if col_filtro not in gdf.columns:
        # Buscar variantes
        for c in gdf.columns:
            if c.lower() in ['alcaldia', 'delegacion', 'demarcacion']:
                col_filtro = c
                break

    if col_filtro in gdf.columns:
        # Usar contains parcial para manejar mojibake y acentos
        gdf = gdf[gdf[col_filtro].str.upper().str.contains(
            val_filtro[:4], na=False)].copy()
    else:
        logger.warning(f"  [{nombre}] No se encontro columna de filtro '{col_filtro}'")
        return None

    logger.info(f"  [{nombre}] Filas Coyoacan: {len(gdf)}")

    if gdf.empty:
        return None

    # Seleccionar y renombrar columnas
    cols_disponibles = {}
    for orig, nuevo in config["cols_datos"].items():
        if orig in gdf.columns:
            cols_disponibles[orig] = nuevo
        else:
            logger.warning(f"  [{nombre}] Columna faltante: {orig}")

    cols_id_disponibles = [c for c in config["cols_id"] if c in gdf.columns]

    gdf_out = gdf[cols_id_disponibles + list(cols_disponibles.keys())].copy()
    gdf_out = gdf_out.rename(columns=cols_disponibles)

    # Renombrar columnas de ID si se especifica (e.g., COLONIA -> colonia)
    if "rename_id" in config:
        gdf_out = gdf_out.rename(columns=config["rename_id"])

    return gdf_out


def main():
    parser = argparse.ArgumentParser(
        description="ETL datos abiertos CDMX -> Neon PostGIS"
    )
    parser.add_argument("--reemplazar", action="store_true",
                        help="Reemplaza datos existentes (if_exists='replace')")
    args = parser.parse_args()

    # Cargar .env
    ruta_proyecto = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    load_dotenv(os.path.join(ruta_proyecto, '.env'))

    database_uri = os.getenv('DATABASE_URI')
    if not database_uri:
        logger.error("DATABASE_URI no configurada.")
        sys.exit(1)

    engine = create_engine(database_uri)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    logger.info("Conexion exitosa a Neon PostGIS.")

    logger.info("=" * 60)
    logger.info("INICIO ETL DATOS ABIERTOS CDMX")
    logger.info("=" * 60)

    # Procesar cada dataset
    dataframes = {}
    for nombre, config in DATASETS.items():
        df = procesar_dataset(nombre, config)
        if df is not None and not df.empty:
            dataframes[nombre] = df

    logger.info(f"\nDatasets procesados: {len(dataframes)}/{len(DATASETS)}")

    if not dataframes:
        logger.error("No se procesaron datasets.")
        sys.exit(1)

    # Merge progresivo por colonia
    logger.info("Uniendo datasets por colonia...")
    dfs = list(dataframes.values())
    df_merged = dfs[0]

    for df in dfs[1:]:
        # Usar colonia como clave de merge
        merge_cols = [c for c in ['colonia', 'cve_col'] if c in df.columns and c in df_merged.columns]
        if merge_cols:
            df_merged = df_merged.merge(df, on=merge_cols, how='outer')
        else:
            logger.warning("  No se encontraron columnas de merge comunes")

    logger.info(f"  Colonias resultantes: {len(df_merged)}")
    logger.info(f"  Columnas totales: {len(df_merged.columns)}")

    # Cargar geometria de colonias desde el primer SHP con geometria
    logger.info("Cargando geometria de colonias...")
    gdf_geom = gpd.read_file(os.path.join(BASE_DIR, "areas_verdes/ca_1.shp"))
    gdf_geom = gdf_geom[gdf_geom['alcaldia'].str.upper().str.strip() == 'COYOACAN']
    gdf_geom = gdf_geom[['colonia', 'cve_col', 'geometry']].copy()

    if gdf_geom.crs and str(gdf_geom.crs) != CRS_ALMACENAMIENTO:
        gdf_geom = gdf_geom.to_crs(CRS_ALMACENAMIENTO)

    # Merge datos con geometria
    gdf_final = gdf_geom.merge(df_merged, on=['colonia', 'cve_col'], how='left')
    gdf_final = gdf_final.set_geometry('geometry')

    # Spatial join: valor unitario del suelo (5 zonas citywide -> asignar a colonias)
    ruta_valor = os.path.join(BASE_DIR, "valor_suelo/vus_promedio/valores_unitarios.shp")
    if os.path.exists(ruta_valor):
        logger.info("  Enriqueciendo con valor unitario del suelo (spatial join)...")
        gdf_valor = gpd.read_file(ruta_valor)
        if gdf_valor.crs != gdf_final.crs:
            gdf_valor = gdf_valor.to_crs(gdf_final.crs)
        gdf_final = gpd.sjoin(gdf_final, gdf_valor[['RANGOS', 'VALOR', 'geometry']],
                              how='left', predicate='intersects')
        gdf_final = gdf_final.rename(columns={'RANGOS': 'valor_suelo_rango', 'VALOR': 'valor_suelo_pesos'})
        gdf_final = gdf_final.drop(columns=['index_right'], errors='ignore')
        # Desduplicar por colonia (una colonia puede caer en >1 zona)
        gdf_final = gdf_final.drop_duplicates(subset=['colonia', 'cve_col'], keep='first')
        logger.info(f"  Valor suelo asignado: {gdf_final['valor_suelo_rango'].notna().sum()} colonias")

    # Spatial join: temperatura nocturna por AGEB -> promedio por colonia
    import glob as globmod
    ruta_temp = globmod.glob(os.path.join(BASE_DIR, "temperatura_nocturna/**/*.shp"), recursive=True)
    ruta_temp = [r for r in ruta_temp if '__MACOSX' not in r]
    if ruta_temp:
        logger.info("  Enriqueciendo con temperatura nocturna (AGEB -> colonia)...")
        gdf_temp = gpd.read_file(ruta_temp[0])
        if gdf_temp.crs != gdf_final.crs:
            gdf_temp = gdf_temp.to_crs(gdf_final.crs)
        # Spatial join: centroides de AGEB -> colonias, promediar
        gdf_temp['centroid_temp'] = gdf_temp.geometry.centroid
        gdf_temp_pts = gdf_temp.set_geometry('centroid_temp')[['centroid_temp', 'MEAN', 'MIN', 'MAX']]
        gdf_temp_pts = gdf_temp_pts.rename(columns={'centroid_temp': 'geometry'}).set_geometry('geometry')
        joined = gpd.sjoin(gdf_temp_pts, gdf_final[['colonia', 'geometry']], how='inner', predicate='within')
        if not joined.empty:
            temp_por_col = joined.groupby('colonia').agg(
                temp_nocturna_media=('MEAN', 'mean'),
                temp_nocturna_min=('MIN', 'min'),
                temp_nocturna_max=('MAX', 'max'),
            ).round(2).reset_index()
            gdf_final = gdf_final.merge(temp_por_col, on='colonia', how='left')
            logger.info(f"  Temperatura asignada: {gdf_final['temp_nocturna_media'].notna().sum()} colonias")

    # Spatial join: internet por AGEB -> promedio por colonia
    ruta_inet = globmod.glob(os.path.join(BASE_DIR, "internet_viviendas/**/*.shp"), recursive=True)
    ruta_inet = [r for r in ruta_inet if '__MACOSX' not in r]
    if ruta_inet:
        logger.info("  Enriqueciendo con acceso a internet (AGEB -> colonia)...")
        gdf_inet = gpd.read_file(ruta_inet[0])
        if gdf_inet.crs != gdf_final.crs:
            gdf_inet = gdf_inet.to_crs(gdf_final.crs)
        gdf_inet['centroid_inet'] = gdf_inet.geometry.centroid
        gdf_inet_pts = gdf_inet.set_geometry('centroid_inet')[['centroid_inet', 'p_vph_pc', 'p_vph_cl', 'p_vph_n']]
        gdf_inet_pts = gdf_inet_pts.rename(columns={'centroid_inet': 'geometry'}).set_geometry('geometry')
        joined = gpd.sjoin(gdf_inet_pts, gdf_final[['colonia', 'geometry']], how='inner', predicate='within')
        if not joined.empty:
            inet_por_col = joined.groupby('colonia').agg(
                pct_viv_pc=('p_vph_pc', 'mean'),
                pct_viv_celular=('p_vph_cl', 'mean'),
                pct_viv_internet=('p_vph_n', 'mean'),
            ).round(2).reset_index()
            gdf_final = gdf_final.merge(inet_por_col, on='colonia', how='left')
            logger.info(f"  Internet asignado: {gdf_final['pct_viv_internet'].notna().sum()} colonias")

    # Limpiar columnas temporales de merges internos
    drop_cols = [c for c in gdf_final.columns if c.startswith('_drop_')]
    if drop_cols:
        gdf_final = gdf_final.drop(columns=drop_cols, errors='ignore')

    logger.info(f"  GeoDataFrame final: {len(gdf_final)} colonias, {len(gdf_final.columns)} columnas")

    # Mostrar resumen
    cols_numericas = [c for c in gdf_final.columns if gdf_final[c].dtype.kind in ['i', 'f']]
    logger.info(f"  Columnas numericas (metricas): {len(cols_numericas)}")
    for c in cols_numericas[:10]:
        logger.info(f"    {c}: min={gdf_final[c].min()}, max={gdf_final[c].max()}")

    # Subir a PostGIS
    modo = 'replace' if args.reemplazar else 'append'
    logger.info(f"Subiendo a '{TABLA_DESTINO}' (modo: {modo})...")
    gdf_final.to_postgis(name=TABLA_DESTINO, con=engine, if_exists=modo, index=False)

    logger.info("=" * 60)
    logger.info("ETL DATOS ABIERTOS CDMX COMPLETADO")
    logger.info(f"  Colonias: {len(gdf_final)}")
    logger.info(f"  Columnas: {len(gdf_final.columns)}")
    logger.info(f"  Tabla: {TABLA_DESTINO}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
