import json
import logging

logger = logging.getLogger(__name__)

def generar_geojson(gdf, include_us_dscr=False, simplification_tolerance=0.001):
    """
    Genera un GeoJSON a partir de un GeoDataFrame, simplificando las geometrías.

    Parameters:
        gdf (GeoDataFrame): GeoDataFrame que contiene los datos espaciales.
        include_us_dscr (bool): Si es True, incluirá la columna 'us_dscr' en las propiedades del GeoJSON.
        simplification_tolerance (float): Tolerancia para simplificar las geometrías.

    Returns:
        dict: GeoJSON en formato dict.
    """
    try:
        # Renombrar la columna de geometría a 'geometry' para GeoJSON
        gdf = gdf.rename_geometry('geometry')

        # Simplificar las geometrías
        gdf['geometry'] = gdf['geometry'].simplify(tolerance=simplification_tolerance, preserve_topology=True)
        logger.info("Geometrías simplificadas.")

        # Seleccionar las columnas necesarias
        columnas = ['geometry']
        if include_us_dscr and 'us_dscr' in gdf.columns:
            columnas.append('us_dscr')

        # Filtrar el GeoDataFrame
        gdf_filtrado = gdf[columnas]
        logger.info(f"GeoDataFrame filtrado con columnas: {columnas}")

        # Convertir a GeoJSON
        geojson = json.loads(gdf_filtrado.to_json())
        logger.info("GeoJSON generado correctamente.")
        return geojson

    except Exception as e:
        logger.error(f"Error al generar GeoJSON: {e}")
        raise
