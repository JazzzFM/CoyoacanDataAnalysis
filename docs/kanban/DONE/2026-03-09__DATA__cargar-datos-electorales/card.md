---
id: "DATA-2026-03-09__cargar-datos-electorales"
title: "Descargar y cargar datos electorales INE/IECM a Neon"
status: "DONE"
phase: "Done"
scope_in:
  - "Descargar secciones electorales SECCION.shp del Marco Geoestadístico INE"
  - "Descargar resultados electorales 2024 (IECM alcaldías + INE diputaciones federales)"
  - "Crear tabla datos_electorales en Neon PostGIS con polígonos de secciones"
  - "Enriquecer con votos por partido, participación, ganador por sección"
  - "Crear scripts ETL: etl_electorales.py y etl_resultados_electorales.py"
scope_out:
  - "Análisis predictivo electoral"
  - "Datos de encuestas"
  - "Resultados de elecciones anteriores a 2024"
artifacts:
  card: card.md
plan_phase: 1
---

# Summary
- Objective: Tener resultados electorales 2024 geolocalizados por sección electoral para correlacionar con perfil socioeconómico y demográfico de Coyoacán.
- Constraints: Datos del INE/IECM son públicos. Las secciones electorales son polígonos propios (no requieren merge con manzanas/AGEBs).

# Resultados
- **403 secciones electorales** de Coyoacán cargadas con geometría (EPSG:4326)
- **55 columnas** por sección: metadata + 21 cols alcaldía + 24 cols federal
- **Distritos federales**: 8 y 19
- **Distritos locales**: 26 y 30
- **Área total**: 53.99 km2

## Resultados electorales 2024
- **Alcaldía**: PAN+ ganó 236/403 secciones (59%), MORENA+ ganó 166 (41%)
- **Federal**: PAN+ ganó 220/403 secciones (55%), MORENA+ ganó 183 (45%)
- **Participación media**: 74.1% (rango 60.8%-83.0%)

# Fuentes de datos
- **Polígonos:** SECCION.shp del Marco Geoestadístico Electoral INE (SIGE8)
- **Resultados alcaldía:** bd2024alccas.xlsx del IECM (estadisticaresultadospelo2024.iecm.mx)
- **Resultados federal:** DIP_FED_2024.csv de Cómputos Distritales INE (computos2024.ine.mx)

# Scripts creados
- `scripts/etl_electorales.py` -- Carga SECCION.shp, filtra Coyoacán, reproyecta, sube polígonos
- `scripts/etl_resultados_electorales.py` -- Procesa IECM+INE, agrega por sección, calcula ganador

# Archivos modificados
- `app/domain/domain_models.py` -- Tabla electorales + tooltip_cols
- `app/presentation/callback_register.py` -- Merge para geometría propia + limpieza prints debug

# Updates
- 2026-03-09 - Created. Datos INE de acceso público.
- 2026-03-09 - COMPLETADO. 403 secciones + resultados IECM/INE 2024 cargados. Commit 897e527.
