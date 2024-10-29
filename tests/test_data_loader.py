# tests/test_data_loader.py

from app.data_loader import load_coyoacan_boundary, load_land_use, load_manzanas, calcular_uso_suelo_predominante

def test_load_coyoacan_boundary(app):
    boundary = load_coyoacan_boundary()
    assert not boundary.empty
    assert boundary.iloc[0]['nomgeo'] == 'Coyoacán'

def test_load_land_use(app):
    land_use = load_land_use()
    assert not land_use.empty
    assert land_use.iloc[0]['us_dscr'] == 'Residencial'

def test_load_manzanas(app):
    manzanas = load_manzanas()
    assert not manzanas.empty
    assert manzanas.iloc[0]['nombre'] == 'Manzana 1'

def test_calcular_uso_suelo_predominante(app):
    resultado = calcular_uso_suelo_predominante()
    assert not resultado.empty
    assert resultado.iloc[0]['us_dscr'] in ['Residencial', 'Comercial']

