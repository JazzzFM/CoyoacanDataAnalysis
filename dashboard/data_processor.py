# data_processor.py

import geopandas as gpd

class DataProcessor:
    @staticmethod
    def procesar_datos(df, nivel_granularidad, metricas):
        """
        Agrupa y procesa los datos según el nivel de granularidad y las métricas seleccionadas.

        Args:
            df (GeoDataFrame): DataFrame con los datos geoespaciales.
            nivel_granularidad (str): Nivel de granularidad ('manzana', 'ageb', 'colonia').
            metricas (list): Lista de métricas a calcular. Ejemplo: ['pob_total', 'densidad_pob_total'].

        Returns:
            GeoDataFrame: DataFrame procesado con las métricas agregadas por nivel de granularidad.
        """
        niveles = {
            "manzana": "id_manzana",
            "ageb": "id_ageb",
            "colonia": "id_colonia"
        }

        if nivel_granularidad not in niveles:
            raise ValueError(f"Nivel de granularidad no válido. Debe ser uno de: {list(niveles.keys())}")

        columna_grupo = niveles[nivel_granularidad]

        # Verificar que la columna de agrupación existe en el DataFrame
        if columna_grupo not in df.columns:
            raise KeyError(f"La columna '{columna_grupo}' no existe en el DataFrame.")

        # Agrupar y calcular métricas
        datos_procesados = df.groupby(columna_grupo).agg({
            "geometry": "first",  # Mantener la geometría
            **{metrica: "sum" for metrica in metricas}  # Calcular suma para las métricas
        }).reset_index()

        return gpd.GeoDataFrame(datos_procesados, geometry="geometry")
