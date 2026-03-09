# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Descripción del Proyecto

Análisis geoespacial de la alcaldía de Coyoacán (CDMX) con datos demográficos, edafológicos, electorales, ambientales y de servicios. Visualización interactiva mediante mapas coropléticos en Dash sobre una base PostGIS.

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

### 2. Dashboard standalone (`dashboard/`)
Arquitectura en capas con inyección de dependencias:

```
dashboard/app.py (punto de entrada)
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
│   └── callback_register.py → CallbackRegister (navegación, métricas, mapas)
└── figures/
    └── figures_utils.py    → FiguresGenerator (mapas coropléticos con Plotly)
```

**Flujo de datos:** PostGIS → `PostgresGeoDataLoader` → `DataService` → `CallbackRegister` (merge con polígonos + filtros) → `FiguresGenerator` → Plotly choropleth_mapbox

### Jerarquía geográfica
Municipio → Colonia → AGEB → Manzana. Los polígonos se almacenan en la tabla `poligonos_manzanas_agebs_colonias` con geometrías separadas (`GEOM_MANZANA`, `GEOM_AGEB`, `GEOM_COLONIA`). Los datos temáticos se unen con polígonos vía merge en `CallbackRegister`.

### Tablas PostGIS clave (definidas en `domain_models.py:TableController`)
- `poligonos_manzanas_agebs_colonias` — polígonos a 3 niveles
- `datos_demograficos_particionada` — datos demográficos
- `datos_edafologicos_particionada` — uso de suelo

## Infraestructura

### Producción: Neon + Render (costo $0/mes)
- **Neon PostGIS:** Project `lucky-sun-44184647`, host `ep-holy-queen-ak4xzy1t-pooler.c-3.us-west-2.aws.neon.tech`
- **Render:** Web Service free tier, Python 3.11, Gunicorn
- **Deploy:** `render.yaml` + `build.sh` + `Procfile`
- **Variables de entorno** (`.env` / Render dashboard): `DATABASE_URI`, `SECRET_KEY`
- **Anti-sleep:** UptimeRobot ping cada 5 min
- **Werkzeug:** Pinneado a 2.3.8 para compatibilidad con Flask-Login 0.6.2

### Legacy: Docker Compose
- Servicio `app` (Python 3.9-slim) + servicio `db` (postgis/postgis:14-3.2)
- El Dockerfile aplica un patch a Flask-Login para Werkzeug (ya no necesario con pin)

## Convenciones

- Proyecto en español: variables, comentarios, nombres de rutas y UI en español
- Datos geoespaciales: GeoPandas + PostGIS, proyección WGS84 (EPSG:4326) para visualización, UTM 14N (EPSG:32614) para cálculos métricos
- Visualizaciones: Plotly Express choropleth_mapbox con esquema de color aleatorio de `AVAILABLE_COLOR_SCHEMES`
- Coordenadas centro de Coyoacán: lat 19.332608, lon -99.143209
- Notebooks exploratorios en `notebooks/` — no son parte de la app de producción
- Datos limpios (shapefiles) en `clean_data/poligonos/` por nivel geográfico
