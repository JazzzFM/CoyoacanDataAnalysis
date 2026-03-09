# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Descripción del Proyecto

Análisis geoespacial de la alcaldía de Coyoacán (CDMX) con datos demográficos, edafológicos, electorales, ambientales y de servicios. Visualización interactiva mediante mapas coropléticos en Dash sobre una base PostGIS.

## Comandos Principales

```bash
# Levantar toda la infraestructura (PostGIS + app)
docker compose up --build

# Solo la base de datos
docker compose up db

# Crear usuario admin dentro del contenedor
docker compose exec app flask create-admin <password>

# Ejecutar migraciones
docker compose exec app flask db upgrade

# Generar nueva migración
docker compose exec app flask db migrate -m "descripción"

# Dashboard standalone (fuera de Docker, requiere DB local)
cd dashboard && python app.py

# App Flask+Dash (fuera de Docker)
python run.py
```

## Arquitectura

El proyecto tiene **dos aplicaciones Dash coexistentes**:

### 1. Flask+Dash integrado (`app/` + `run.py`)
- `run.py` → `app/__init__.py:create_app()` (factory pattern)
- Flask maneja autenticación (`routes.py`, `models.py`, `auth.py`) con Flask-Login
- Dash embebido en `/dashboard/` vía `app/dashboard.py:init_dashboard(server)`
- Lee GeoJSON local (`data/manzanas_coyoacan.geojson`)
- Desplegado con Gunicorn en Docker (puerto 8050)

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

- **Docker Compose:** servicio `app` (Python 3.9-slim) + servicio `db` (postgis/postgis:14-3.2)
- **Red interna:** `coyoacan_network`
- **Variables de entorno** (archivo `.env`): `DATABASE_URI`, `SECRET_KEY`, `DASH_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- **wait-for-it.sh:** script de espera para que la DB esté lista antes de arrancar Gunicorn
- El Dockerfile aplica un patch a Flask-Login para compatibilidad con Werkzeug (línea 24-27)

## Convenciones

- Proyecto en español: variables, comentarios, nombres de rutas y UI en español
- Datos geoespaciales: GeoPandas + PostGIS, proyección WGS84 (EPSG:4326) para visualización, UTM 14N (EPSG:32614) para cálculos métricos
- Visualizaciones: Plotly Express choropleth_mapbox con esquema de color aleatorio de `AVAILABLE_COLOR_SCHEMES`
- Coordenadas centro de Coyoacán: lat 19.332608, lon -99.143209
- Notebooks exploratorios en `notebooks/` — no son parte de la app de producción
- Datos limpios (shapefiles) en `clean_data/poligonos/` por nivel geográfico
