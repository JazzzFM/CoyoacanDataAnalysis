# figures_utils.py

import plotly.express as px

def create_choropleth(gdf, metric_column, title, nivel_granularidad, color_scale="YlOrRd"):
    print(f"[FIGURE UTILS] Generando mapa para métrica: {metric_column}")

    if gdf.empty or metric_column not in gdf.columns:
        print("[FIGURE UTILS ERROR] DataFrame vacío o métrica no definida. No se puede generar el mapa.")
        return {}

    # Mapear identificador según el nivel de granularidad
    id_column = {
        "manzana": "id_manzana",
        "ageb": "id_ageb",
        "colonia": "id_colonia"
    }.get(nivel_granularidad, None)

    if id_column not in gdf.columns:
        print(f"[FIGURE UTILS ERROR] La columna '{id_column}' no existe en el DataFrame.")
        return {}

    # Restablecer índice y crear columna 'id' si es necesario
    gdf = gdf.reset_index(drop=True)
    gdf['id'] = gdf[id_column].astype(str)

    # Convertir geometría a GeoJSON
    geojson = gdf.set_index('id')['geometry'].__geo_interface__

    # Configurar escalas de colores específicas para cada métrica
    color_scales = {
        "pob_total": "YlOrRd",
        "densidad_pob_total": "YlOrRd",
        "densidad_hombres": "Blues",
        "densidad_mujeres": "Purples",
        "dependencia_infantil": "Greens",
        "relacion_genero": "RdYlBu",
        "tasa_alfabetizacion": "YlGnBu",
    }
    color_scale = color_scales.get(metric_column, "Viridis")

    try:
        fig = px.choropleth_mapbox(
            gdf,
            geojson=geojson,
            locations='id',
            color=metric_column,
            color_continuous_scale=color_scale,
            title=title,
            hover_data={
                metric_column: ":.2f",  # Métrica seleccionada
            },
            mapbox_style="carto-positron",
            center={"lat": 19.34, "lon": -99.16},
            zoom=12,
        )
        # Configurar el layout
        fig.update_layout(
            autosize=True,
            margin={"r": 0, "t": 50, "l": 0, "b": 0},
            coloraxis_colorbar={"title": metric_column.capitalize()}
        )
        print("[FIGURE UTILS SUCCESS] Mapa generado correctamente.")
        return fig
    except Exception as e:
        print(f"[FIGURE UTILS ERROR] Error al crear el mapa: {e}")
        return {}

def create_edafologia_map(gdf):
    """
    Genera un mapa interactivo de uso de suelo utilizando Plotly Express.
    """
    print("[FIGURE UTILS] Generando mapa de edafología.")

    # Asegurarnos de que hay datos para graficar
    if gdf.empty:
        print("[FIGURE UTILS ERROR] No hay datos para generar el mapa de edafología.")
        return {}

    # Crear una copia del GeoDataFrame para evitar modificaciones no deseadas
    gdf = gdf.copy()

    # Crear un identificador único para cada geometría
    gdf['id'] = gdf.index.astype(str)

    # Convertir geometría a GeoJSON
    geojson = gdf.set_index('id')['geometry'].__geo_interface__

    # Crear el mapa
    fig = px.choropleth_mapbox(
        gdf,
        geojson=geojson,
        locations='id',
        color='us_dscr',
        title='Uso de Suelo en Coyoacán',
        hover_data={'us_dscr': True},
        category_orders={'us_dscr': sorted(gdf['us_dscr'].unique())},
        mapbox_style="carto-positron",
        center={"lat": 19.34, "lon": -99.16},
        zoom=12,
    )

    # Actualizar el layout
    fig.update_layout(
        margin={"r": 0, "t": 50, "l": 0, "b": 0},
        legend_title_text='Uso de Suelo',
    )

    print("[FIGURE UTILS SUCCESS] Mapa de edafología generado correctamente.")
    return fig
