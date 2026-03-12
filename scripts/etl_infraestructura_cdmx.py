#!/usr/bin/env python3
# scripts/etl_infraestructura_cdmx.py

"""
ETL para datos de infraestructura y recursos naturales de CDMX.

Carga shapefiles de transporte, salud, comercio, patrimonio y medio ambiente,
filtra al area de Coyoacan mediante clip espacial, y sube a PostGIS.

Genera dos tablas:
  - datos_infraestructura: puntos y lineas de equipamiento
  - datos_recursos_naturales: areas verdes, rios, monumentos

Uso:
    python scripts/etl_infraestructura_cdmx.py --reemplazar
"""

import sys
import os
import glob as globmod
import argparse
import logging
import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

CRS_ALMACENAMIENTO = "EPSG:4326"
BASE_DIR = "data/datos_abiertos_cdmx"

# Bounding box aproximado de Coyoacan para clip rapido
# (se usa el poligono real de PostGIS si esta disponible)
COYOACAN_BBOX = (-99.21, 19.28, -99.09, 19.38)


def obtener_poligono_coyoacan(engine):
    """Carga el poligono de Coyoacan desde PostGIS para clip espacial."""
    try:
        gdf = gpd.read_postgis(
            "SELECT geometry FROM datos_indicadores_colonia LIMIT 1",
            con=engine, geom_col="geometry"
        )
        # Cargar todas las colonias y hacer union
        gdf_all = gpd.read_postgis(
            "SELECT geometry FROM datos_indicadores_colonia",
            con=engine, geom_col="geometry"
        )
        from shapely.ops import unary_union
        poligono = unary_union(gdf_all.geometry)
        gdf_coyoacan = gpd.GeoDataFrame(geometry=[poligono], crs=gdf_all.crs)
        logger.info(f"  Poligono de Coyoacan cargado ({len(gdf_all)} colonias)")
        return gdf_coyoacan
    except Exception as e:
        logger.warning(f"  No se pudo cargar poligono de PostGIS: {e}")
        logger.info("  Usando bounding box aproximado")
        from shapely.geometry import box
        poligono = box(*COYOACAN_BBOX)
        return gpd.GeoDataFrame(geometry=[poligono], crs=CRS_ALMACENAMIENTO)


def buscar_shp(directorio, patron):
    """Busca un SHP dentro de un directorio usando glob (resuelve Unicode/rutas)."""
    resultados = globmod.glob(os.path.join(directorio, "**", patron), recursive=True)
    # Filtrar __MACOSX
    resultados = [r for r in resultados if '__MACOSX' not in r]
    return resultados[0] if resultados else None


def cargar_y_filtrar(ruta, gdf_coyoacan, nombre, encoding=None):
    """Carga un SHP y lo recorta al area de Coyoacan."""
    if not os.path.exists(ruta):
        logger.warning(f"  [{nombre}] No encontrado: {ruta}")
        return None

    try:
        kwargs = {"encoding": encoding} if encoding else {}
        gdf = gpd.read_file(ruta, **kwargs)
    except Exception:
        try:
            gdf = gpd.read_file(ruta, encoding='latin1')
        except Exception as e:
            logger.error(f"  [{nombre}] Error: {e}")
            return None

    logger.info(f"  [{nombre}] Cargado: {len(gdf)} registros, CRS: {gdf.crs}")

    # Reproyectar si es necesario
    if gdf.crs and str(gdf.crs) != CRS_ALMACENAMIENTO:
        gdf = gdf.to_crs(CRS_ALMACENAMIENTO)

    # Clip a Coyoacan
    coyoacan_reproj = gdf_coyoacan.to_crs(gdf.crs) if gdf.crs != gdf_coyoacan.crs else gdf_coyoacan
    try:
        gdf_clip = gpd.clip(gdf, coyoacan_reproj)
    except Exception:
        # Fallback: spatial join
        gdf_clip = gpd.sjoin(gdf, coyoacan_reproj, how='inner', predicate='intersects')
        gdf_clip = gdf_clip.drop(columns=['index_right'], errors='ignore')

    logger.info(f"  [{nombre}] En Coyoacan: {len(gdf_clip)} registros")
    return gdf_clip


def main():
    parser = argparse.ArgumentParser(
        description="ETL infraestructura y recursos naturales CDMX -> PostGIS"
    )
    parser.add_argument("--reemplazar", action="store_true")
    args = parser.parse_args()

    ruta_proyecto = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    load_dotenv(os.path.join(ruta_proyecto, '.env'))

    database_uri = os.getenv('DATABASE_URI')
    if not database_uri:
        logger.error("DATABASE_URI no configurada.")
        sys.exit(1)

    engine = create_engine(database_uri)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    logger.info("Conexion exitosa.")

    logger.info("=" * 60)
    logger.info("ETL INFRAESTRUCTURA Y RECURSOS NATURALES")
    logger.info("=" * 60)

    gdf_coyoacan = obtener_poligono_coyoacan(engine)

    # ── INFRAESTRUCTURA ──
    infra_frames = []

    # Metro estaciones
    gdf = cargar_y_filtrar(
        f"{BASE_DIR}/metro/stcmetro_shp/STC_Metro_estaciones_utm14n.shp",
        gdf_coyoacan, "metro_estaciones")
    if gdf is not None and len(gdf) > 0:
        gdf['categoria'] = 'transporte'
        gdf['subcategoria'] = 'metro_estacion'
        # Buscar columna de nombre
        for col in ['NOMBRE', 'nombre', 'ESTACION', 'estacion', 'Nombre']:
            if col in gdf.columns:
                gdf['nombre'] = gdf[col]
                break
        else:
            gdf['nombre'] = 'Estacion Metro'
        infra_frames.append(gdf[['nombre', 'categoria', 'subcategoria', 'geometry']].copy())

    # Metro lineas
    gdf = cargar_y_filtrar(
        f"{BASE_DIR}/metro/stcmetro_shp/STC_Metro_lineas_utm14n.shp",
        gdf_coyoacan, "metro_lineas")
    if gdf is not None and len(gdf) > 0:
        gdf['categoria'] = 'transporte'
        gdf['subcategoria'] = 'metro_linea'
        for col in ['NOMBRE', 'nombre', 'LINEA', 'linea', 'Nombre']:
            if col in gdf.columns:
                gdf['nombre'] = gdf[col]
                break
        else:
            gdf['nombre'] = 'Linea Metro'
        infra_frames.append(gdf[['nombre', 'categoria', 'subcategoria', 'geometry']].copy())

    # Tren Ligero estaciones
    ruta_tl_est = buscar_shp(f"{BASE_DIR}/tren_ligero", "STE_TrenLigero_estaciones*.shp")
    gdf = cargar_y_filtrar(
        ruta_tl_est or f"{BASE_DIR}/tren_ligero/ste_shp/ste_tren_ligero_shp/STE_TrenLigero_estaciones_utm14n.shp",
        gdf_coyoacan, "tren_ligero_estaciones")
    if gdf is not None and len(gdf) > 0:
        gdf['categoria'] = 'transporte'
        gdf['subcategoria'] = 'tren_ligero_estacion'
        for col in ['NOMBRE', 'nombre', 'ESTACION', 'Nombre']:
            if col in gdf.columns:
                gdf['nombre'] = gdf[col]
                break
        else:
            gdf['nombre'] = 'Estacion Tren Ligero'
        infra_frames.append(gdf[['nombre', 'categoria', 'subcategoria', 'geometry']].copy())

    # Tren Ligero linea
    ruta_tl_lin = buscar_shp(f"{BASE_DIR}/tren_ligero", "STE_TrenLigero_linea*.shp")
    gdf = cargar_y_filtrar(
        ruta_tl_lin or f"{BASE_DIR}/tren_ligero/ste_shp/ste_tren_ligero_shp/STE_TrenLigero_linea_utm14n.shp",
        gdf_coyoacan, "tren_ligero_linea")
    if gdf is not None and len(gdf) > 0:
        gdf['categoria'] = 'transporte'
        gdf['subcategoria'] = 'tren_ligero_linea'
        gdf['nombre'] = 'Tren Ligero'
        infra_frames.append(gdf[['nombre', 'categoria', 'subcategoria', 'geometry']].copy())

    # Ciclovias (total)
    for shp_name in ['Infraestructura ciclista total.shp', 'Ciclovia.shp']:
        ruta_ciclo = f"{BASE_DIR}/ciclovias/infraestructura_vial_ciclista/{shp_name}"
        if os.path.exists(ruta_ciclo):
            gdf = cargar_y_filtrar(ruta_ciclo, gdf_coyoacan, "ciclovias")
            if gdf is not None and len(gdf) > 0:
                gdf['categoria'] = 'transporte'
                gdf['subcategoria'] = 'ciclovia'
                gdf['nombre'] = 'Ciclovia'
                infra_frames.append(gdf[['nombre', 'categoria', 'subcategoria', 'geometry']].copy())
            break

    # Salud (nombre del archivo tiene 'а' cirilica U+0430 en "bаsico")
    ruta_salud = buscar_shp(f"{BASE_DIR}/salud", "Equipamiento_*salud.shp")
    gdf = cargar_y_filtrar(
        ruta_salud or f"{BASE_DIR}/salud/Equipamiento_basico_de_salud.shp",
        gdf_coyoacan, "salud")
    if gdf is not None and len(gdf) > 0:
        gdf['categoria'] = 'salud'
        gdf['subcategoria'] = 'centro_salud'
        for col in ['NOMBRE', 'nombre', 'Nombre', 'NOM_EQUIPO', 'nom_equipo']:
            if col in gdf.columns:
                gdf['nombre'] = gdf[col]
                break
        else:
            gdf['nombre'] = 'Centro de Salud'
        infra_frames.append(gdf[['nombre', 'categoria', 'subcategoria', 'geometry']].copy())

    # Tianguis
    gdf = cargar_y_filtrar(
        f"{BASE_DIR}/tianguis/TIANGUIS_ADIP.shp",
        gdf_coyoacan, "tianguis")
    if gdf is not None and len(gdf) > 0:
        gdf['categoria'] = 'comercio'
        gdf['subcategoria'] = 'tianguis'
        for col in ['NOMBRE', 'nombre', 'Nombre', 'TIANGUIS']:
            if col in gdf.columns:
                gdf['nombre'] = gdf[col]
                break
        else:
            gdf['nombre'] = 'Tianguis'
        infra_frames.append(gdf[['nombre', 'categoria', 'subcategoria', 'geometry']].copy())

    # Metrobus estaciones
    gdf = cargar_y_filtrar(
        f"{BASE_DIR}/metrobus/mb_shp/Metrobus_estaciones.shp",
        gdf_coyoacan, "metrobus_estaciones")
    if gdf is not None and len(gdf) > 0:
        gdf['categoria'] = 'transporte'
        gdf['subcategoria'] = 'metrobus_estacion'
        gdf['nombre'] = gdf.get('NOMBRE', 'Estacion Metrobus')
        infra_frames.append(gdf[['nombre', 'categoria', 'subcategoria', 'geometry']].copy())

    # Metrobus lineas
    gdf = cargar_y_filtrar(
        f"{BASE_DIR}/metrobus/mb_shp/Metrobus_lineas.shp",
        gdf_coyoacan, "metrobus_lineas")
    if gdf is not None and len(gdf) > 0:
        gdf['categoria'] = 'transporte'
        gdf['subcategoria'] = 'metrobus_linea'
        gdf['nombre'] = gdf.get('LINEA', 'Linea Metrobus')
        infra_frames.append(gdf[['nombre', 'categoria', 'subcategoria', 'geometry']].copy())

    # Ecobici
    gdf = cargar_y_filtrar(
        f"{BASE_DIR}/ecobici/cicloestaciones_ecobici/cicloestaciones_ecobici.shp",
        gdf_coyoacan, "ecobici")
    if gdf is not None and len(gdf) > 0:
        gdf['categoria'] = 'transporte'
        gdf['subcategoria'] = 'ecobici'
        gdf['nombre'] = 'Cicloestacion Ecobici #' + gdf['num_cicloe'].astype(str)
        infra_frames.append(gdf[['nombre', 'categoria', 'subcategoria', 'geometry']].copy())

    # Accidentes peatones
    ruta_acc = buscar_shp(f"{BASE_DIR}/accidentes_peatones", "accidentado_peaton.shp")
    gdf = cargar_y_filtrar(
        ruta_acc or f"{BASE_DIR}/accidentes_peatones/accidentado_peaton.shp",
        gdf_coyoacan, "accidentes_peatones")
    if gdf is not None and len(gdf) > 0:
        gdf['categoria'] = 'seguridad'
        gdf['subcategoria'] = 'accidente_peaton'
        gdf['nombre'] = 'Accidente peatonal'
        infra_frames.append(gdf[['nombre', 'categoria', 'subcategoria', 'geometry']].copy())

    # Subir infraestructura
    if infra_frames:
        gdf_infra = pd.concat(infra_frames, ignore_index=True)
        gdf_infra = gpd.GeoDataFrame(gdf_infra, geometry='geometry', crs=CRS_ALMACENAMIENTO)
        logger.info(f"\nInfraestructura total: {len(gdf_infra)} registros")
        for cat, n in gdf_infra['subcategoria'].value_counts().items():
            logger.info(f"  {cat}: {n}")

        # Forzar geometria 2D (algunos SHP tienen coordenada Z)
        from shapely.ops import transform
        gdf_infra['geometry'] = gdf_infra.geometry.apply(
            lambda geom: transform(lambda x, y, z=None: (x, y), geom) if geom and geom.has_z else geom
        )

        modo = 'replace' if args.reemplazar else 'append'
        gdf_infra.to_postgis('datos_infraestructura', engine, if_exists=modo, index=False)
        logger.info("  -> Subido a 'datos_infraestructura'")

    # ── RECURSOS NATURALES ──
    nat_frames = []

    # Areas verdes
    gdf = cargar_y_filtrar(
        f"{BASE_DIR}/inventario_areas_verdes/inventario_areas_verdes_1.shp",
        gdf_coyoacan, "areas_verdes_inventario")
    if gdf is not None and len(gdf) > 0:
        gdf['categoria'] = 'area_verde'
        for col in ['NOMBRE', 'nombre', 'Nombre', 'NOM_AV']:
            if col in gdf.columns:
                gdf['nombre'] = gdf[col]
                break
        else:
            gdf['nombre'] = 'Area Verde'
        for col in ['TIPO', 'tipo', 'Tipo', 'TIPO_AV']:
            if col in gdf.columns:
                gdf['tipo'] = gdf[col]
                break
        else:
            gdf['tipo'] = 'general'
        nat_frames.append(gdf[['nombre', 'categoria', 'tipo', 'geometry']].copy())

    # Rios (archivo real tiene acento: "Ríos de CDMX.shp")
    ruta_rios_found = buscar_shp(f"{BASE_DIR}/rios", "R*os de CDMX.shp")
    for ruta_rios in filter(None, [ruta_rios_found, f"{BASE_DIR}/rios/rios_cdmx/Ríos de CDMX.shp"]):
        if os.path.exists(ruta_rios):
            gdf = cargar_y_filtrar(ruta_rios, gdf_coyoacan, "rios")
            if gdf is not None and len(gdf) > 0:
                gdf['categoria'] = 'hidrologia'
                for col in ['NOMBRE', 'nombre', 'Nombre', 'NOM_RIO']:
                    if col in gdf.columns:
                        gdf['nombre'] = gdf[col]
                        break
                else:
                    gdf['nombre'] = 'Rio/Canal'
                for col in ['TIPO', 'tipo', 'Tipo']:
                    if col in gdf.columns:
                        gdf['tipo'] = gdf[col]
                        break
                else:
                    gdf['tipo'] = 'rio'
                nat_frames.append(gdf[['nombre', 'categoria', 'tipo', 'geometry']].copy())
            break

    # Monumentos historicos (archivo real: "Zonas_Monumentos_Históricos_.shp")
    ruta_monum = buscar_shp(f"{BASE_DIR}/monumentos_historicos", "Zonas_Monumentos_Hist*ricos_.shp")
    gdf = cargar_y_filtrar(
        ruta_monum or f"{BASE_DIR}/monumentos_historicos/monumentos_historicos/Zonas_Monumentos_Históricos_.shp",
        gdf_coyoacan, "monumentos")
    if gdf is not None and len(gdf) > 0:
        gdf['categoria'] = 'patrimonio'
        for col in ['NOMBRE', 'nombre', 'Nombre', 'ZONA']:
            if col in gdf.columns:
                gdf['nombre'] = gdf[col]
                break
        else:
            gdf['nombre'] = 'Zona de Monumentos'
        gdf['tipo'] = 'monumento_historico'
        nat_frames.append(gdf[['nombre', 'categoria', 'tipo', 'geometry']].copy())

    # Subir recursos naturales
    if nat_frames:
        gdf_nat = pd.concat(nat_frames, ignore_index=True)
        gdf_nat = gpd.GeoDataFrame(gdf_nat, geometry='geometry', crs=CRS_ALMACENAMIENTO)
        logger.info(f"\nRecursos naturales total: {len(gdf_nat)} registros")
        for cat, n in gdf_nat['categoria'].value_counts().items():
            logger.info(f"  {cat}: {n}")

        modo = 'replace' if args.reemplazar else 'append'
        gdf_nat.to_postgis('datos_recursos_naturales', engine, if_exists=modo, index=False)
        logger.info("  -> Subido a 'datos_recursos_naturales'")

    logger.info("=" * 60)
    logger.info("ETL INFRAESTRUCTURA Y RECURSOS NATURALES COMPLETADO")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
