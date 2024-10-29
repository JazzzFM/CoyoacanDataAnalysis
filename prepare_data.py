# prepare_data.py

import geopandas as gpd
import os

def ensure_column(data_path, column_name, default_value):
    """
    Ensures that a specified column exists in the GeoDataFrame, if not adds it.
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"File not found: {data_path}")
    
    # Load the GeoDataFrame
    gdf = gpd.read_file(data_path)
    
    # Check if column exists, if not, add it with a default value
    if column_name not in gdf.columns:
        print(f"Adding missing column '{column_name}' with default value '{default_value}'")
        gdf[column_name] = default_value
        # Save the updated GeoDataFrame back to GeoJSON
        gdf.to_file(data_path, driver="GeoJSON")
    else:
        print(f"Column '{column_name}' already exists.")
    
    return gdf

if __name__ == "__main__":
    # Define the path to your geojson file and column settings
    data_path = 'data/manzanas_coyoacan.geojson'
    column_name = 'nombre'
    default_value = 'Unknown'
    
    # Ensure the required column exists
    ensure_column(data_path, column_name, default_value)

