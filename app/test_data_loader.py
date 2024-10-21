import pytest
from data_loader import load_coyoacan_boundary, load_land_use, load_manzanas, calcular_uso_suelo_predominante

def test_load_coyoacan_boundary():
    gdf = load_coyoacan_boundary()
    assert not gdf.empty, "GeoDataFrame de límites de Coyoacán está vacío."
    assert 'geom' in gdf.columns, "Columna 'geom' no encontrada en límites de Coyoacán."

def test_load_land_use():
    gdf = load_land_use()
    assert not gdf.empty, "GeoDataFrame de uso de suelo está vacío."
    assert 'geom' in gdf.columns, "Columna 'geom' no encontrada en uso de suelo."

def test_load_manzanas():
    gdf = load_manzanas()
    assert not gdf.empty, "GeoDataFrame de manzanas está vacío."
    assert 'geom' in gdf.columns, "Columna 'geom' no encontrada en manzanas."

def test_calcular_uso_suelo_predominante():
    gdf = calcular_uso_suelo_predominante()
    assert not gdf.empty, "GeoDataFrame de uso de suelo predominante está vacío."
    assert 'us_dscr' in gdf.columns, "Columna 'us_dscr' no encontrada en uso de suelo predominante."
