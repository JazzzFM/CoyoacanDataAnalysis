# figures_utils.py

import plotly.express as px

def create_choropleth(gdf, metric_column, title, nivel_granularidad, color_scale="YlOrRd"):
    print(f"[FIGURE UTILS] Generando mapa para métrica: {metric_column}")

    if gdf.empty or metric_column not in gdf.columns:
        print("[FIGURE UTILS ERROR] DataFrame vacío o métrica no definida. No se puede generar el mapa.")
        return px.choropleth_mapbox(title="No Data Available")

    # Mapear identificador según el nivel de granularidad
    id_column = {
        "manzana": "id_manzana",
        "ageb": "id_ageb",
        "colonia": "id_colonia"
    }.get(nivel_granularidad, None)

    if id_column not in gdf.columns:
        print(f"[FIGURE UTILS ERROR] La columna '{id_column}' no existe en el DataFrame.")
        return px.choropleth_mapbox(title="Error en los datos")

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
        )
        # Configurar el mapa centrado en Coyoacán
        fig.update_layout(
            mapbox=dict(
                style="carto-positron",
                center={"lat": 19.34, "lon": -99.16},
                zoom=12,
            ),
            autosize=True,
            margin={"r": 0, "t": 50, "l": 0, "b": 0},
        )
        print("[FIGURE UTILS SUCCESS] Mapa generado correctamente.")
        return fig
    except Exception as e:
        print(f"[FIGURE UTILS ERROR] Error al crear el mapa: {e}")
        return px.choropleth_mapbox(title="Error Generating Map")
