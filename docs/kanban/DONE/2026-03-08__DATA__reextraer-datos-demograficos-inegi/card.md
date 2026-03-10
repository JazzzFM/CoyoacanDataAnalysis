---
id: "DATA-2026-03-08__reextraer-datos-demograficos-inegi"
title: "Re-extraer y cargar datos demográficos INEGI a Neon"
status: "BACKLOG"
phase: "Research"
scope_in:
  - "Descargar datos censo 2020 de INEGI (si no están en disco)"
  - "Ejecutar ETL de limpieza (basado en notebooks/EDADemografia.ipynb)"
  - "Cargar tabla datos_demograficos_particionada a Neon"
scope_out:
  - "Análisis exploratorio nuevo"
  - "Datos de años diferentes al 2020"
artifacts:
  card: card.md
  plan: plan.md
  validate: validate.md
plan_phase: 1
---

# Summary
- Objective: Reconstruir la tabla `datos_demograficos_particionada` en Neon con datos del censo INEGI 2020 a nivel AGEB para Coyoacán.
- Constraints: Los shapefiles originales del censo (`data/demografico/2020/`) no están en disco (directorio `data/` está en .gitignore). Hay que re-descargarlos o extraer la lógica del notebook existente.

# Datos fuente
- **Fuente:** INEGI Censo de Población y Vivienda 2020
- **Archivos necesarios:** `hombres.shp`, `mujeres.shp`, `total.shp` (nivel AGEB)
- **Notebook de referencia:** `notebooks/EDADemografia.ipynb` — contiene todo el ETL

# Transformaciones clave (del notebook)
1. Merge de 3 shapefiles (hombres + mujeres + total) por columna `ageb`
2. Clip espacial a polígono de Coyoacán
3. Reproyección a EPSG:32614 para cálculo de área en km²
4. Cálculo de densidades (pob/km²)
5. Reproyección a EPSG:4326 para almacenamiento
6. Agregar columna `anio = 2020`

# Dependencias
- **Requiere:** Polígonos cargados en Neon (tarea DATA polígonos)
- **Bloquea:** Dashboard demográfico funcional

# Updates
- 2026-03-08 - Created. Datos originales no disponibles en disco, necesitan re-descarga.
