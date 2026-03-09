---
id: "DATA-2026-03-08__reextraer-datos-edafologicos-seduvi"
title: "Re-extraer y cargar datos edafológicos/uso de suelo a Neon"
status: "BACKLOG"
phase: "Research"
scope_in:
  - "Descargar datos de uso de suelo SEDUVI (si no están en disco)"
  - "Ejecutar ETL basado en notebooks/ManzanasUsuoSueloEDA.ipynb"
  - "Cargar tabla datos_edafologicos_particionada a Neon"
scope_out:
  - "Análisis exploratorio nuevo"
artifacts:
  card: card.md
  validate: validate.md
plan_phase: 1
---

# Summary
- Objective: Reconstruir `datos_edafologicos_particionada` en Neon con datos de uso de suelo SEDUVI 2017 a nivel manzana para Coyoacán.
- Constraints: Shapefile original (`data/uso_suelo/uso-de-suelo.shp`) no está en disco. Hay que re-descargarlo.

# Datos fuente
- **Fuente:** SEDUVI — uso de suelo CDMX 2017
- **Notebook de referencia:** `notebooks/ManzanasUsuoSueloEDA.ipynb`

# Dependencias
- **Requiere:** Polígonos cargados en Neon (tarea DATA polígonos)
- **Bloquea:** Dashboard edafológico funcional

# Updates
- 2026-03-08 - Created. Datos originales no disponibles en disco.
