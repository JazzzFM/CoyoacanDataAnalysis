from dash import Input, Output
from figures_utils import create_choropleth
from data_loader import load_data

gdf = load_data("../clean_data/coyoacan_poblacion_2020_clean.geojson")

def register_callbacks(app):
    @app.callback(
        Output("choropleth-map", "figure"),
        Input("year-dropdown", "value"),
        Input("metric-radio", "value"),
    )
    def update_map(selected_year, selected_metric):
        print(f"[CALLBACK] Año seleccionado: {selected_year}, Métrica seleccionada: {selected_metric}")
        filtered_data = gdf[gdf["anio"] == selected_year]

        if filtered_data.empty:
            print(f"[CALLBACK ERROR] No hay datos disponibles para el año {selected_year}.")
            return create_choropleth(gdf, None, "Datos no disponibles", color_scale="Greys")

        print(f"[CALLBACK] Filtrado de datos exitoso. Total de registros: {len(filtered_data)}")
        return create_choropleth(
            filtered_data,
            metric_column=selected_metric,
            title=f"{selected_metric} en {selected_year}"
        )