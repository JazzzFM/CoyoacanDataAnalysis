---
id: "DATA-2026-03-09__cargar-datos-denue"
title: "Descargar y cargar datos DENUE (negocios/servicios) a Neon"
status: "BACKLOG"
phase: "Research"
scope_in:
  - "Descargar DENUE 2024 de INEGI para Coyoacán"
  - "Crear tabla datos_servicios en Neon PostGIS"
  - "Categorizar por tipo: salud, educación, comercio, transporte"
  - "Georreferenciar puntos con coordenadas lat/lon"
  - "Crear script ETL en scripts/"
scope_out:
  - "Análisis de accesibilidad (tarea separada)"
  - "Datos de transporte público (GTFS)"
artifacts:
  card: card.md
plan_phase: 1
---

# Summary
- Objective: Tener el DENUE (Directorio Estadístico Nacional de Unidades Económicas) de Coyoacán como puntos geolocalizados en PostGIS, categorizados por tipo de servicio.
- Constraints: DENUE es descarga libre de INEGI. Son puntos (no polígonos). Aproximadamente 15,000-25,000 registros para Coyoacán.

# Fuente de datos
- **URL:** https://www.inegi.org.mx/app/descarga/?ti=6
- **Formato:** CSV con coordenadas lat/lon
- **Campos clave:** codigo_act (actividad económica SCIAN), nombre_act, per_ocu (personal ocupado), latitud, longitud
- **Categorización sugerida:**
  - Salud: códigos SCIAN 621*, 622*, 623*
  - Educación: 611*
  - Comercio: 461*, 462*, 463*
  - Alimentación: 722*
  - Transporte: no incluido en DENUE (necesita GTFS aparte)

# Tabla destino
```sql
CREATE TABLE datos_servicios (
    id SERIAL PRIMARY KEY,
    nombre TEXT,
    categoria TEXT,       -- salud, educacion, comercio, alimentacion, otro
    subcategoria TEXT,    -- nombre_act del SCIAN
    codigo_scian TEXT,
    personal_ocupado TEXT,
    geometry GEOMETRY(POINT, 4326),
    anio INT DEFAULT 2024
);
```

# Dependencias
- **Requiere:** Nada
- **Bloquea:** TASK__analisis-accesibilidad, TASK__rubro-servicios

# Updates
- 2026-03-09 - Created. Datos DENUE son gratuitos y de alta calidad.
