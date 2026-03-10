# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Descripción del Proyecto

Análisis geoespacial de la alcaldía de Coyoacán (CDMX) con datos demográficos, edafológicos, electorales, ambientales, de servicios, infraestructura y recursos naturales. Visualización interactiva mediante mapas coropléticos y categóricos en Dash sobre una base PostGIS.

## Comandos Principales

```bash
# Desarrollo local (con Neon PostGIS remoto)
source .venv/bin/activate
python run.py

# Dashboard standalone (con Neon PostGIS remoto)
cd dashboard && python app.py

# Gunicorn local (simula Render)
gunicorn --bind 0.0.0.0:8050 --timeout 120 --workers 2 run:app

# Docker (legacy, para desarrollo con PostGIS local)
docker compose up --build

# Crear usuario admin
flask create-admin <password>
```

## Arquitectura

El proyecto tiene **dos aplicaciones Dash coexistentes**:

### 1. Flask+Dash integrado (`app/` + `run.py`)
- `run.py` → `app/__init__.py:create_app()` (factory pattern)
- Flask maneja autenticación (`routes.py`, `models.py`) con Flask-Login
- Dash embebido en `/dashboard/` vía `app/dashboard.py:init_dashboard(server)`
- Carga polígonos de colonias desde Neon PostGIS (`gpd.read_postgis`)
- Desplegado con Gunicorn en Render (free tier)

### 2. Dashboard standalone (`dashboard/`) — legacy, pendiente de eliminar
Arquitectura en capas con inyección de dependencias (misma estructura que `app/`):

```
app/ (arquitectura integrada en Flask)
├── data_access/
│   ├── data_connection.py  → DatabaseCredentials + DatabaseConnectionManager (SQLAlchemy Engine)
│   ├── data_loader.py      → PostgresGeoDataLoader (gpd.read_postgis)
│   └── data_processor.py   → GeoDataProcessor (filtrado estático por año/métricas)
├── domain/
│   └── domain_models.py    → TableController, DashboardFilters, MapVisualizationConfig
├── services/
│   └── data_service.py     → DataService (orquesta loader + processor)
├── presentation/
│   ├── controller.py       → DashAppController (inicializa Dash + layout + callbacks)
│   ├── layout_builder.py   → LayoutBuilder (sidebar + páginas por rubro)
│   └── callback_register.py → CallbackRegister (navegación, métricas, mapas coropléticos y categóricos)
└── figures/
    └── figures_utils.py    → FiguresGenerator (mapas coropléticos + categóricos con Plotly)
```

**Flujo de datos (rubros numéricos):** PostGIS → `PostgresGeoDataLoader` → `DataService` → `CallbackRegister` (merge con polígonos + filtros) → `FiguresGenerator.generar_mapa_coropletico` → Plotly choropleth_mapbox

**Flujo de datos (rubros categóricos — infraestructura/recursos naturales):** PostGIS → `DataService` → `CallbackRegister` (filtro por categorías) → `FiguresGenerator.generar_mapa_categorico` → Plotly Scattermapbox (puntos, líneas, centroides de polígonos)

### Jerarquía geográfica
Municipio → Colonia → AGEB → Manzana. Los polígonos se almacenan en la tabla `poligonos_manzanas_agebs_colonias` con geometrías separadas (`GEOM_MANZANA`, `GEOM_AGEB`, `GEOM_COLONIA`). Los datos temáticos se unen con polígonos vía merge en `CallbackRegister`.

### Tablas PostGIS clave (definidas en `domain_models.py:TableController`)
- `poligonos_manzanas_agebs_colonias` — polígonos a 3 niveles
- `datos_demograficos_particionada` — datos demográficos (154 AGEBs)
- `datos_edafologicos_particionada` — uso de suelo (2,386 manzanas)
- `datos_servicios` — unidades económicas DENUE (25,082 registros)
- `datos_electorales` — secciones electorales + votos 2024 (403 secciones)
- `datos_indicadores_colonia` — métricas ambientales por colonia (153 colonias)
- `datos_infraestructura` — transporte, salud, comercio (392 registros, geometría mixta)
- `datos_recursos_naturales` — áreas verdes, ríos, patrimonio (1,839 registros)

## Infraestructura

### Producción: Neon + Render (costo $0/mes)
- **Neon PostGIS:** Project `lucky-sun-44184647`, host `ep-holy-queen-ak4xzy1t-pooler.c-3.us-west-2.aws.neon.tech`
- **Render:** Web Service free tier, Python 3.11, Gunicorn
- **Deploy:** `render.yaml` + `build.sh` + `Procfile`
- **Variables de entorno** (`.env` / Render dashboard): `DATABASE_URI`, `SECRET_KEY`
- **Anti-sleep:** UptimeRobot ping cada 5 min
- **Werkzeug:** 3.1.6, Flask 3.1.3, Flask-Login 0.6.3 (compatibles)

### Legacy: Docker Compose
- Servicio `app` (Python 3.9-slim) + servicio `db` (postgis/postgis:14-3.2)
- El Dockerfile aplica un patch a Flask-Login para Werkzeug (ya no necesario con pin)

## Convenciones

- Proyecto en español: variables, comentarios, nombres de rutas y UI en español
- Datos geoespaciales: GeoPandas + PostGIS, proyección WGS84 (EPSG:4326) para visualización, UTM 14N (EPSG:32614) para cálculos métricos
- Visualizaciones: Plotly Express choropleth_mapbox (datos numéricos) + Plotly GO Scattermapbox (datos categóricos), esquema de color aleatorio de `AVAILABLE_COLOR_SCHEMES`
- Coordenadas centro de Coyoacán: lat 19.332608, lon -99.143209
- Notebooks exploratorios en `notebooks/` — no son parte de la app de producción
- Datos limpios (shapefiles) en `clean_data/poligonos/` por nivel geográfico
