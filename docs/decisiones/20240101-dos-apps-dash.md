# ADR: Dos aplicaciones Dash coexistentes

**Fecha:** Inicio del proyecto
**Estado:** Vigente

## Contexto

El proyecto tiene dos formas de servir dashboards Dash:

1. **Flask+Dash integrado** (`app/dashboard.py`): Dash embebido dentro de una aplicación Flask que maneja autenticación con Flask-Login. Desplegado en Docker con Gunicorn. Lee datos de un GeoJSON local.

2. **Dashboard standalone** (`dashboard/app.py`): Aplicación Dash independiente con arquitectura en capas (data_access, domain, services, presentation). Conecta directamente a PostGIS. Sin autenticación.

## Decisión

Se mantienen ambas aplicaciones porque sirven propósitos diferentes:

- La app Flask provee autenticación y un entorno de producción con Gunicorn
- El dashboard standalone tiene una arquitectura más limpia y es donde se desarrollan las nuevas visualizaciones con conexión directa a PostGIS

## Consecuencias

- Hay duplicación parcial de lógica de dashboard entre `app/dashboard.py` y `dashboard/`
- Los nuevos rubros temáticos se desarrollan en `dashboard/` (standalone) que tiene la arquitectura en capas
- La integración final requiere migrar las visualizaciones del standalone al Flask+Dash integrado
- El standalone es útil para desarrollo rápido sin necesidad de autenticación
