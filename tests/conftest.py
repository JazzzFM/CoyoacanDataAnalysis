# tests/conftest.py

import pytest
from app import create_app, db
from app.models import User  # Asegúrate de que esta ruta es correcta
from unittest.mock import patch
import geopandas as gpd
from shapely.geometry import Polygon

@pytest.fixture
def app():
    config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False  # Desactivar CSRF para pruebas
    }
    app = create_app(config=config)  # Pasar la configuración directamente

    with app.app_context():
        db.create_all()
        # Crear un usuario de prueba
        user = User(username='testuser')
        user.set_password('testpassword')  # Asegúrate de tener este método en tu modelo
        db.session.add(user)
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture(autouse=True)
def mock_geopandas_read_postgis():
    with patch('app.data_loader.gpd.read_postgis') as mock_read:
        def side_effect(query, engine, geom_col='geom'):
            if "limites_alcaldias" in query:
                return gpd.GeoDataFrame({
                    'nomgeo': ['Coyoacán'],
                    'identifica': ['ID001'],
                    'geom': [Polygon([(-99.16, 19.43), (-99.16, 19.42), (-99.17, 19.42), (-99.16, 19.43)])]
                }, geometry='geom', crs="EPSG:4326")
            
            elif "uso_suelo_coyoacan" in query:
                return gpd.GeoDataFrame({
                    'us_dscr': ['Residencial', 'Comercial'],
                    'identifica': ['ID001', 'ID002'],
                    'geom': [
                        Polygon([(-99.16, 19.43), (-99.16, 19.42), (-99.17, 19.42), (-99.16, 19.43)]),
                        Polygon([(-99.18, 19.44), (-99.18, 19.43), (-99.19, 19.43), (-99.18, 19.44)])
                    ]
                }, geometry='geom', crs="EPSG:4326")
            
            elif "manzanas_coyoacan" in query:
                return gpd.GeoDataFrame({
                    'nombre': ['Manzana 1', 'Manzana 2'],
                    'identifica': ['ID001', 'ID002'],
                    'geom': [
                        Polygon([(-99.16, 19.43), (-99.16, 19.42), (-99.17, 19.42), (-99.16, 19.43)]),
                        Polygon([(-99.18, 19.44), (-99.18, 19.43), (-99.19, 19.43), (-99.18, 19.44)])
                    ]
                }, geometry='geom', crs="EPSG:4326")
            
            else:
                return gpd.GeoDataFrame()
        
        mock_read.side_effect = side_effect
        yield mock_read

