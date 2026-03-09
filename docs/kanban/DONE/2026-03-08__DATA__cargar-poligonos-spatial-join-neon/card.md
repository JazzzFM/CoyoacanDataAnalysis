---
id: "DATA-2026-03-08__cargar-poligonos-spatial-join-neon"
title: "Recrear spatial join de polígonos y cargar a Neon"
status: "DONE"
phase: "Validate"
scope_in:
  - "Spatial join de manzanas + agebs + colonias en un solo GeoDataFrame"
  - "Cargar tabla poligonos_manzanas_agebs_colonias a Neon"
  - "Verificar integridad: conteos, geometrías válidas, CRS"
scope_out:
  - "Datos temáticos (demográficos, edafológicos)"
  - "Optimización de geometrías (ST_Simplify) — se hará después"
artifacts:
  card: card.md
  plan: plan.md
  validate: validate.md
plan_phase: 1
---

# Summary
- Objective: Recrear la tabla consolidada `poligonos_manzanas_agebs_colonias` a partir de los shapefiles limpios en `clean_data/poligonos/` y cargarla a Neon PostGIS.
- Constraints: Los shapefiles están separados (manzana, ageb, colonia). Hay que hacer spatial join (ST_Within/ST_Intersects) para asociar cada manzana a su AGEB y colonia.

# Datos disponibles

| Archivo | Registros | Columnas |
|---|---|---|
| `manzanas_coyoacan_clean.shp` | 4,813 | id_manzana, geometry |
| `ageb_coyoacan_clean.shp` | 167 | id_ageb, geometry |
| `colonias_coyoacan_clean.shp` | 153 | id_colonia, nombre_col, geometry |

# Dependencias
- **Requiere:** Proyecto Neon creado con PostGIS (completado en INFRA task)
- **Bloquea:** Todas las tareas DATA temáticas + Phase 2 de INFRA (adaptar código)

# Neon connection
- Project ID: `lucky-sun-44184647`
- DB: `neondb`
- Tabla destino: `poligonos_manzanas_agebs_colonias` (ya creada, vacía)

# Updates
- 2026-03-08 - Created.
- 2026-03-08 - DONE. Spatial join completado: 4,813 manzanas, 156 AGEBs, 152 colonias. Solo 1 manzana sin colonia asignada. Cargado a Neon con 3 columnas geometry convertidas.
